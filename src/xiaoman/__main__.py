"""启动入口：python -m xiaoman [--host] [--port] [--config]。"""

from __future__ import annotations

import argparse
import os


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(
        prog="xiaoman", description="小满：一个记得住事的脱困搭子"
    )
    parser.add_argument("--host", help="监听地址，默认取 config.toml")
    parser.add_argument("--port", type=int, help="端口，默认取 config.toml")
    parser.add_argument("--config", help="配置文件路径")
    args = parser.parse_args(argv)

    if args.config:
        os.environ["XIAOMAN_CONFIG"] = args.config

    from .config import load

    cfg = load()
    host = args.host or cfg.host
    port = args.port or cfg.port

    if not cfg.model.model:
        raise SystemExit("config.toml 里没有配置 model.model")

    import uvicorn

    print(f"{cfg.name} · {cfg.model.model}")
    print(f"http://{host}:{port}")
    uvicorn.run(
        "xiaoman.app:app",
        host=host,
        port=port,
        log_level="warning",
        access_log=False,
    )


if __name__ == "__main__":
    main()
