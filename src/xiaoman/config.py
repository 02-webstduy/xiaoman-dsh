"""配置加载：config.toml + config.local.toml（本机私密覆盖）+ 环境变量。

公开仓库里只有 config.toml；真实模型地址、你的联系人这类东西写进
config.local.toml（已 gitignore），不会被提交。
"""

from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass
from datetime import date
from pathlib import Path
from typing import Any

# src/xiaoman/config.py -> 仓库根目录（含 pyproject.toml / config.toml / web/）
ROOT = Path(__file__).resolve().parents[2]


@dataclass(frozen=True)
class ModelConfig:
    base_url: str
    model: str
    api_key_env: str | None = None
    temperature: float = 0.7
    max_tokens: int = 400
    timeout_s: float = 60.0
    max_history: int = 20

    def headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.api_key_env:
            key = os.environ.get(self.api_key_env)
            if key:
                headers["Authorization"] = f"Bearer {key}"
        return headers


@dataclass(frozen=True)
class SafetyConfig:
    """危机语句的固定回应。内容只从配置来，不让模型自由发挥。"""

    enabled: bool = True
    hotlines: tuple[str, ...] = (
        "12356 全国心理援助热线（24 小时）",
        "010-82951332 北京心理危机研究与干预中心",
    )
    contacts: tuple[str, ...] = ()
    extra_phrases: tuple[str, ...] = ()


@dataclass(frozen=True)
class AppConfig:
    name: str
    host: str
    port: int
    started_on: date
    model: ModelConfig
    safety: SafetyConfig
    persona_path: Path
    web_dir: Path


def _deep_merge(base: dict[str, Any], overlay: dict[str, Any]) -> dict[str, Any]:
    out = dict(base)
    for key, value in overlay.items():
        if isinstance(value, dict) and isinstance(out.get(key), dict):
            out[key] = _deep_merge(out[key], value)
        else:
            out[key] = value
    return out


def _read_toml(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {}
    return tomllib.loads(path.read_text("utf-8"))


def _load_dotenv() -> None:
    """读仓库根的 .env（不进 git）；已存在的环境变量优先。"""
    path = ROOT / ".env"
    if not path.exists():
        return
    for line in path.read_text("utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip().strip('"').strip("'"))


def _cfg_path() -> Path:
    return Path(os.environ.get("XIAOMAN_CONFIG") or (ROOT / "config.toml"))


def load(path: Path | None = None) -> AppConfig:
    _load_dotenv()
    p = Path(path) if path else _cfg_path()
    raw = _read_toml(p)
    # 本机私密覆盖：与 config.toml 同目录的 config.local.toml
    raw = _deep_merge(raw, _read_toml(p.with_name("config.local.toml")))

    app = raw.get("app", {})
    model_raw = raw.get("model", {})
    safety_raw = raw.get("safety", {})

    base_url = os.environ.get("XIAOMAN_BASE_URL") or model_raw.get("base_url", "")
    model_name = os.environ.get("XIAOMAN_MODEL") or model_raw.get("model", "")

    model = ModelConfig(
        base_url=str(base_url).rstrip("/"),
        model=str(model_name),
        api_key_env=model_raw.get("api_key_env"),
        temperature=float(model_raw.get("temperature", 0.7)),
        max_tokens=int(model_raw.get("max_tokens", 400)),
        timeout_s=float(model_raw.get("timeout_s", 60)),
        max_history=int(model_raw.get("max_history", 20)),
    )

    safety = SafetyConfig(
        enabled=bool(safety_raw.get("enabled", True)),
        hotlines=tuple(str(x) for x in safety_raw.get("hotlines", SafetyConfig.hotlines)),
        contacts=tuple(str(x) for x in safety_raw.get("contacts", ())),
        extra_phrases=tuple(str(x) for x in safety_raw.get("extra_phrases", ())),
    )

    started_raw = str(app.get("started_on") or date.today().isoformat())
    try:
        started_on = date.fromisoformat(started_raw)
    except ValueError:
        started_on = date.today()

    return AppConfig(
        name=str(app.get("name", "小满")),
        host=os.environ.get("XIAOMAN_HOST") or str(app.get("host", "127.0.0.1")),
        port=int(os.environ.get("XIAOMAN_PORT") or app.get("port", 8765)),
        started_on=started_on,
        model=model,
        safety=safety,
        persona_path=ROOT / "src" / "xiaoman" / "persona" / "base.md",
        web_dir=ROOT / "web",
    )
