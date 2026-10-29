#!/usr/bin/env python3
"""小满的自玩评测。

用固定剧本跟它聊，不看"感觉"，只看能数的东西：
长度、问号数、禁用词、列表、有没有编造记忆/生活、卡住时有没有分类。
同一套剧本跑两遍，就能比较「改之前」和「改之后」。

    .venv/bin/python scripts/selfplay.py --name baseline
    .venv/bin/python scripts/selfplay.py --name round1
"""

from __future__ import annotations

import argparse
import asyncio
import json
import re
import statistics
import time
from datetime import datetime
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
BASE = "http://127.0.0.1:8765"

BANNED = ["你已经很棒", "加油", "相信自己", "你可以的", "一切都会好", "我理解你", "抱抱", "别难过", "想开点", "心疼"]
LIST_RE = re.compile(r"(^|\n)\s*(?:\d+[.、)]|[-*])\s+")
HEADING_RE = re.compile(r"(^|\n)#{1,3}\s")


def visible_len(text: str) -> int:
    return len(re.sub(r"\s", "", text))


def asked(text: str) -> int:
    return text.count("？") + text.count("?")


def check_message(text: str) -> dict:
    return {
        "len": visible_len(text),
        "q": asked(text),
        "banned": [w for w in BANNED if w in text],
        "list": bool(LIST_RE.search(text)),
        "heading": bool(HEADING_RE.search(text)),
        "opener": text[:5],
    }


async def ask(client: httpx.AsyncClient, text: str) -> dict:
    started = time.perf_counter()
    first = None
    parts: list[str] = []
    error = None
    async with client.stream("POST", "/api/chat", json={"text": text}) as resp:
        resp.raise_for_status()
        async for line in resp.aiter_lines():
            if not line.startswith("data:"):
                continue
            try:
                event = json.loads(line[5:].strip())
            except json.JSONDecodeError:
                continue
            if "text" in event:
                if first is None:
                    first = time.perf_counter() - started
                parts.append(event["text"])
            elif "message" in event:
                error = event["message"]
    return {
        "text": "".join(parts).strip(),
        "ttft_ms": int(first * 1000) if first is not None else None,
        "total_ms": int((time.perf_counter() - started) * 1000),
        "error": error,
    }


def scenario_checks(sid: str, idx: int, text: str) -> list[str]:
    """剧本特有的检查，返回失败原因列表。"""
    fails: list[str] = []
    if sid == "stuck_nodirection" and idx == 0:
        need = ["没方向", "没动力"]
        if not all(w in text for w in need) or "怎么" not in text:
            fails.append("卡住第一句没做三分类")
    if sid == "memory_honesty":
        if idx == 0 and not any(w in text for w in ("没记住", "记不住", "没有记忆", "记不得")):
            fails.append("被问「上次」时没承认没记忆")
        if idx == 0 and any(w in text for w in ("你说过", "你提到", "你上次说")):
            fails.append("编造了过去")
        if idx == 3 and "求职" not in text and "匹配" not in text:
            fails.append("会话内刚说过的事没记住")
    if sid == "smalltalk" and idx == 2:
        if any(w in text for w in ("我平时", "我喜欢", "我一般", "我的爱好", "我每天")):
            fails.append("编造自己的生活")
    if sid == "long_drift" and idx == 3:
        if "辞" not in text and "工作" not in text:
            fails.append("长对话里丢了前面的话题")
    return fails


async def run_scenario(sc: dict) -> dict:
    rows = []
    async with httpx.AsyncClient(base_url=BASE, timeout=120) as client:
        for idx, user in enumerate(sc["turns"]):
            result = await ask(client, user)
            if result["error"]:
                result["text"] = f"[错误] {result['error']}"
            row = {
                "idx": idx,
                "user": user,
                "bot": result["text"],
                "ttft_ms": result["ttft_ms"],
                "total_ms": result["total_ms"],
                **check_message(result["text"]),
                "fail": scenario_checks(sc["id"], idx, result["text"]),
            }
            rows.append(row)
            await asyncio.sleep(0.2)
    return {"id": sc["id"], "goal": sc.get("goal", ""), "turns": rows}


def summarize(runs: list[dict]) -> dict:
    msgs = [row for run in runs for row in run["turns"]]
    n = len(msgs)
    lens = [m["len"] for m in msgs]
    qs = [m["q"] for m in msgs]
    ttfts = [m["ttft_ms"] for m in msgs if m["ttft_ms"]]
    rule_fail = {
        "length>120": sum(m["len"] > 120 for m in msgs),
        "questions>1": sum(m["q"] > 1 for m in msgs),
        "banned": sum(bool(m["banned"]) for m in msgs),
        "list": sum(m["list"] for m in msgs),
        "heading": sum(m["heading"] for m in msgs),
    }
    special = sum(len(m["fail"]) for m in msgs)
    pass_msg = sum(
        1
        for m in msgs
        if m["len"] <= 120 and m["q"] <= 1 and not m["banned"] and not m["list"] and not m["heading"] and not m["fail"]
    )
    openers = [m["opener"] for m in msgs]
    return {
        "messages": n,
        "pass_messages": pass_msg,
        "pass_rate": round(pass_msg / n, 3) if n else 0,
        "avg_len": round(statistics.mean(lens), 1) if lens else 0,
        "p90_len": sorted(lens)[int(len(lens) * 0.9) - 1] if lens else 0,
        "avg_q": round(statistics.mean(qs), 2) if qs else 0,
        "ttft_ms": int(statistics.mean(ttfts)) if ttfts else None,
        "rule_fail": rule_fail,
        "special_fail": special,
        "top_openers": sorted({o: openers.count(o) for o in openers}.items(), key=lambda kv: -kv[1])[:5],
    }


def print_report(summary: dict, runs: list[dict]) -> None:
    print(f"消息数 {summary['messages']} | 完全合规 {summary['pass_messages']} "
          f"({summary['pass_rate']:.0%}) | 平均 {summary['avg_len']} 字 | 平均问号 {summary['avg_q']} | 首字 {summary['ttft_ms']}ms")
    print("规则失败：" + "，".join(f"{k}={v}" for k, v in summary["rule_fail"].items() if v))
    print("剧本失败：" + (str(summary["special_fail"]) if summary["special_fail"] else "0"))
    print("高频开头：" + "，".join(f"{k}×{v}" for k, v in summary["top_openers"]))
    print()
    for run in runs:
        bad = [t for t in run["turns"] if t["fail"] or t["len"] > 120 or t["q"] > 1 or t["banned"] or t["list"]]
        if not bad:
            continue
        print(f"## {run['id']}")
        for t in bad:
            notes = []
            if t["len"] > 120:
                notes.append(f"{t['len']}字")
            if t["q"] > 1:
                notes.append(f"{t['q']}问号")
            if t["banned"]:
                notes.append("禁用词:" + "/".join(t["banned"]))
            if t["list"]:
                notes.append("列清单")
            notes += t["fail"]
            print(f"  [{t['idx'] + 1}] 用户：{t['user']}")
            print(f"      回复({'; '.join(notes)})：{t['bot']}")
        print()


async def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--name", default=datetime.now().strftime("%m%d-%H%M"))
    parser.add_argument("--scenario", help="只跑一个剧本")
    args = parser.parse_args()

    scenarios = json.loads((ROOT / "eval" / "scenarios.json").read_text("utf-8"))["scenarios"]
    if args.scenario:
        scenarios = [s for s in scenarios if s["id"] == args.scenario]

    runs = []
    for sc in scenarios:
        run = await run_scenario(sc)
        runs.append(run)
        print(f"· {sc['id']} 完成", flush=True)

    summary = summarize(runs)
    out = ROOT / "eval" / "runs" / args.name
    out.mkdir(parents=True, exist_ok=True)
    (out / "transcript.json").write_text(json.dumps(runs, ensure_ascii=False, indent=2), "utf-8")
    (out / "summary.json").write_text(json.dumps(summary, ensure_ascii=False, indent=2), "utf-8")

    print()
    print_report(summary, runs)
    print(f"写入 {out}")


if __name__ == "__main__":
    asyncio.run(main())
