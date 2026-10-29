"""配置加载：config.toml + 少量环境变量覆盖。"""

from __future__ import annotations

import os
import tomllib
from dataclasses import dataclass
from datetime import date
from pathlib import Path

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
class AppConfig:
    name: str
    host: str
    port: int
    started_on: date
    model: ModelConfig
    persona_path: Path
    web_dir: Path


def _cfg_path() -> Path:
    return Path(os.environ.get("XIAOMAN_CONFIG") or (ROOT / "config.toml"))


def load(path: Path | None = None) -> AppConfig:
    p = Path(path) if path else _cfg_path()
    raw: dict = {}
    if p.exists():
        raw = tomllib.loads(p.read_text("utf-8"))

    app = raw.get("app", {})
    model_raw = raw.get("model", {})

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
        persona_path=ROOT / "src" / "xiaoman" / "persona" / "base.md",
        web_dir=ROOT / "web",
    )
