"""HTTP 层：单页、SSE 聊天、人格文件、健康检查。

第 1 步故意没有数据库：会话只放在内存里。
"""

from __future__ import annotations

import asyncio
import json
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from zoneinfo import ZoneInfo

import httpx
from fastapi import FastAPI, Request
from fastapi.responses import FileResponse, JSONResponse, PlainTextResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, Field

from . import llm
from .config import AppConfig, load

cfg: AppConfig = load()
TZ = ZoneInfo("Asia/Shanghai")

app = FastAPI(title=cfg.name, docs_url=None, redoc_url=None)
app.mount("/assets", StaticFiles(directory=cfg.web_dir), name="assets")

SESSION_COOKIE = "xmn_sid"
SESSION_TTL = 6 * 3600
MAX_SESSIONS = 200


@dataclass
class Session:
    id: str
    messages: list[dict[str, str]] = field(default_factory=list)
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)
    last_seen: float = field(default_factory=time.time)


_sessions: dict[str, Session] = {}


def _prune() -> None:
    if len(_sessions) <= MAX_SESSIONS:
        return
    now = time.time()
    dead = [sid for sid, s in _sessions.items() if now - s.last_seen > SESSION_TTL]
    for sid in dead[-(len(_sessions) - MAX_SESSIONS):]:
        _sessions.pop(sid, None)


@app.middleware("http")
async def attach_session(request: Request, call_next):
    sid = request.cookies.get(SESSION_COOKIE)
    session = _sessions.get(sid or "")
    new = session is None
    if session is None:
        session = Session(id=uuid.uuid4().hex)
        _sessions[session.id] = session
        _prune()
    session.last_seen = time.time()
    request.state.session = session

    response = await call_next(request)
    if new:
        response.set_cookie(
            SESSION_COOKIE,
            session.id,
            httponly=True,
            samesite="lax",
            max_age=SESSION_TTL,
        )
    return response


# ---------------------------------------------------------------- 人格文件


_persona_cache: dict[str, float | str] = {"mtime": -1.0, "text": ""}


def persona_text() -> str:
    path = cfg.persona_path
    mtime = path.stat().st_mtime
    if mtime != _persona_cache["mtime"]:
        _persona_cache["mtime"] = mtime
        _persona_cache["text"] = path.read_text("utf-8")
    return str(_persona_cache["text"])


def day_number() -> int:
    return max(1, (datetime.now(TZ).date() - cfg.started_on).days + 1)


def system_prompt() -> str:
    now = datetime.now(TZ)
    weekday = "一二三四五六日"[now.weekday()]
    return (
        persona_text().rstrip()
        + f"\n\n# 此刻\n今天是 {now:%Y-%m-%d}（周{weekday}），你们认识的第 {day_number()} 天。\n"
    )


# ---------------------------------------------------------------- 模型健康


async def model_health() -> tuple[bool, str, int | None]:
    started = time.perf_counter()
    try:
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.get(f"{cfg.model.base_url}/models", headers=cfg.model.headers())
            resp.raise_for_status()
        return True, "", int((time.perf_counter() - started) * 1000)
    except Exception as exc:  # noqa: BLE001 - 健康检查不该把服务打挂
        return False, f"{type(exc).__name__}: {exc}"[:200], None


# ---------------------------------------------------------------- 接口


class ChatIn(BaseModel):
    text: str = Field(min_length=1, max_length=4000)


def sse(event: str, data: dict) -> str:
    return f"event: {event}\ndata: {json.dumps(data, ensure_ascii=False)}\n\n"


@app.get("/")
async def index() -> FileResponse:
    return FileResponse(
        cfg.web_dir / "index.html",
        headers={"Cache-Control": "no-store"},
    )


@app.get("/api/state")
async def state(request: Request) -> dict:
    session: Session = request.state.session
    ok, detail, latency = await model_health()
    return {
        "name": cfg.name,
        "day": day_number(),
        "model": cfg.model.model,
        "ok": ok,
        "detail": detail,
        "latency_ms": latency,
        "turns": sum(1 for m in session.messages if m["role"] == "user"),
    }


@app.get("/api/persona", response_class=PlainTextResponse)
async def persona() -> PlainTextResponse:
    return PlainTextResponse(persona_text(), headers={"Cache-Control": "no-store"})


@app.post("/api/reset")
async def reset(request: Request) -> dict:
    session: Session = request.state.session
    session.messages.clear()
    return {"ok": True}


@app.post("/api/chat")
async def chat(payload: ChatIn, request: Request) -> StreamingResponse:
    session: Session = request.state.session
    text = payload.text.strip()
    if not text:
        return JSONResponse({"error": "空消息"}, status_code=400)  # type: ignore[return-value]

    async def event_stream():
        started = time.perf_counter()
        parts: list[str] = []
        usage: dict = {}
        failed = False
        yield sse("meta", {"model": cfg.model.model, "day": day_number()})

        async with session.lock:
            session.messages.append({"role": "user", "content": text})
            messages = [{"role": "system", "content": system_prompt()}] + session.messages[
                -cfg.model.max_history :
            ]
            try:
                async for delta in llm.stream_chat(cfg.model, messages, usage):
                    parts.append(delta)
                    yield sse("delta", {"text": delta})
            except llm.LLMError as exc:
                failed = True
                yield sse("error", {"message": str(exc)})
            finally:
                answer = "".join(parts).strip()
                if answer:
                    session.messages.append({"role": "assistant", "content": answer})
                elif failed:
                    # 一个字都没回：把这轮的用户消息撤掉，重试时不会重复
                    if session.messages and session.messages[-1]["role"] == "user":
                        session.messages.pop()
                yield sse(
                    "done",
                    {
                        "ms": int((time.perf_counter() - started) * 1000),
                        "chars": len(answer),
                        "usage": usage,
                    },
                )

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.get("/api/health")
async def health() -> dict:
    ok, detail, latency = await model_health()
    return {
        "ok": ok,
        "model": cfg.model.model,
        "base_url": cfg.model.base_url,
        "latency_ms": latency,
        "detail": detail,
        "persona_mtime": cfg.persona_path.stat().st_mtime,
    }
