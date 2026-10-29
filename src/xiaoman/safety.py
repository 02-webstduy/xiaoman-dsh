"""危机语句的检测与固定回应。

两条原则：
1. 命中后**不调用模型**，回复由配置拼出来，避免自由发挥；
2. 宁可多问一句"你现在安全吗"，也不要分析原因、说教、承诺保密。
"""

from __future__ import annotations

import re

from .config import SafetyConfig

# 明确指向自伤/自杀的说法
_PATTERNS: tuple[str, ...] = (
    r"不想活",
    r"不想再活",
    r"活不下去",
    r"活够了",
    r"活着没(有)?(意思|意义|盼头)",
    r"想(要)?死",
    r"自杀",
    r"轻生",
    r"结束(自己|生命)",
    r"了结(自己|生命)",
    r"一了百了",
    r"割腕",
    r"跳楼",
    r"自残",
    r"想消失",
    r"不想(再)?撑",
    r"撑不下去",
    r"撑不住了",
    r"没有(活下去|活着)的(理由|意义)",
    r"不如死了",
)

# 常见夸张/亲密用法，先剔掉再匹配（否则「累死了」会被误判）
_IDIOMS = re.compile(
    r"(笑|累|气|困|饿|烦|热|冷|吓|无聊|美|帅|香|甜|乐|忙|急|疼|痛|哭)死"
    r"|想死你|想死我了"
)

# 明确否定（「我不想死」不是危机），先剔掉
_NEGATION = re.compile(
    r"(不|没|没有|不会|别)(?:想|打算|会|要|去|曾经|考虑过|想过(?:要)?)?(?:死|自杀|轻生)"
)


def detect(text: str, cfg: SafetyConfig | None = None) -> str | None:
    """命中返回命中的模式，否则 None。"""
    cleaned = re.sub(r"\s+", "", text or "")
    if not cleaned:
        return None

    stripped = _IDIOMS.sub("", cleaned)
    stripped = _NEGATION.sub("", stripped)
    for pattern in _PATTERNS:
        if re.search(pattern, stripped):
            return pattern

    for phrase in (cfg.extra_phrases if cfg else ()):
        phrase = phrase.strip()
        if phrase and phrase in cleaned:
            return phrase
    return None


def build_reply(cfg: SafetyConfig) -> str:
    """固定回应：先确认安全，再给可拨打的资源和具体的人。"""
    lines = ["我在。先不聊别的——你现在安全吗？"]

    if cfg.contacts:
        lines.append(
            "如果愿意，现在就给"
            + "、".join(cfg.contacts)
            + "发一条消息，哪怕只说「我现在不太好」。"
        )

    if cfg.hotlines:
        lines.append("如果身边没人能马上到，打这个电话：" + "；".join(cfg.hotlines) + "。")

    lines.append("如果你已经有具体的打算，请拨 120 或去最近的急诊。")
    return "\n".join(lines)


def help_info(cfg: SafetyConfig) -> dict:
    """给页面「求助」按钮用的静态信息。"""
    return {
        "hotlines": list(cfg.hotlines),
        "contacts": list(cfg.contacts),
        "note": "我不能替代专业帮助；有立即危险请拨 120。",
    }
