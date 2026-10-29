"""本地模型客户端：OpenAI 兼容的流式对话。

刻意只做一件事：把消息流式吐出来。不在这里做记忆、不在这里做流程。
"""

from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator, Iterable
from typing import Any

import httpx

from .config import ModelConfig


class LLMError(RuntimeError):
    """可以直接展示给用户的模型错误。"""


async def stream_chat(
    cfg: ModelConfig,
    messages: Iterable[dict[str, str]],
    usage_out: dict[str, Any] | None = None,
) -> AsyncIterator[str]:
    url = f"{cfg.base_url}/chat/completions"
    payload = {
        "model": cfg.model,
        "messages": list(messages),
        "temperature": cfg.temperature,
        "max_tokens": cfg.max_tokens,
        "stream": True,
        "stream_options": {"include_usage": True},
    }

    attempt = 0
    while True:
        emitted = False
        try:
            async with httpx.AsyncClient(
                timeout=httpx.Timeout(cfg.timeout_s, connect=5.0)
            ) as client:
                async with client.stream(
                    "POST", url, json=payload, headers=cfg.headers()
                ) as resp:
                    if resp.status_code != 200:
                        body = (await resp.aread()).decode("utf-8", "replace")
                        raise LLMError(
                            f"模型服务返回 {resp.status_code}，先检查一下它是不是活着：{body[:160]}"
                        )

                    async for line in resp.aiter_lines():
                        if not line.startswith("data:"):
                            continue
                        data = line[5:].strip()
                        if data == "[DONE]":
                            return
                        try:
                            chunk = json.loads(data)
                        except json.JSONDecodeError:
                            continue

                        if usage_out is not None and chunk.get("usage"):
                            usage_out.update(chunk["usage"])

                        for choice in chunk.get("choices") or []:
                            text = (choice.get("delta") or {}).get("content")
                            if text:
                                emitted = True
                                yield text
            return

        except LLMError:
            raise
        except (httpx.ConnectError, httpx.ConnectTimeout) as exc:
            # 连不上：没吐出任何字之前，允许重试一次
            if emitted or attempt >= 1:
                raise LLMError(
                    f"连不上模型服务（{cfg.base_url}）。看看 vLLM 那个容器还在不在。"
                ) from exc
            attempt += 1
            await asyncio.sleep(0.6)
        except httpx.TimeoutException as exc:
            raise LLMError(f"模型想了超过 {cfg.timeout_s:g} 秒还没说完，先停一下。") from exc
        except httpx.HTTPError as exc:
            raise LLMError(f"跟模型通信时断了：{type(exc).__name__}") from exc
