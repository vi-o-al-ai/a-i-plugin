"""Entry point: ``ableton-live-mcp`` (stdio). stdout is the MCP wire; all logging goes to stderr/file."""

from __future__ import annotations

import logging
import os
import sys

from .config import Settings
from .server import build_server

log = logging.getLogger("ableton_live_mcp")


def configure_logging(settings: Settings) -> None:
    handlers: list[logging.Handler] = [logging.StreamHandler(sys.stderr)]
    try:
        settings.ensure_dir(settings.logs_dir)
        # Create the file 0600 before the handler opens it (best effort; the handler appends).
        try:
            os.close(os.open(settings.log_file, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o600))
        except OSError:
            pass
        handlers.append(logging.FileHandler(settings.log_file, encoding="utf-8"))
    except OSError as exc:  # unwritable home: stderr only
        print(f"ableton-live-mcp: cannot open log file {settings.log_file}: {exc}", file=sys.stderr)
    logging.basicConfig(
        level=getattr(logging, settings.log_level, logging.INFO),
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        handlers=handlers,
        force=True,
    )
    # The low-level server logs every request at INFO; keep stderr readable.
    logging.getLogger("mcp.server.lowlevel.server").setLevel(logging.WARNING)
    for warning in settings.warnings:
        log.warning(warning)


def main() -> None:
    settings = Settings.from_env()
    configure_logging(settings)
    server = build_server(settings)
    server.run(transport="stdio")


if __name__ == "__main__":
    main()
