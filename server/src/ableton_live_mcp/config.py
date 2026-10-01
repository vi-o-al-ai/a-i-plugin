"""Server settings read from the environment (see TOOLS.md "Environment variables")."""

from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 9892
DEFAULT_HOME = "~/.claude-live"
DEFAULT_LOG_LEVEL = "INFO"

_LOG_LEVELS = ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")


@dataclass(frozen=True)
class Settings:
    """Where the Remote Script listens and where this server keeps its data.

    ``home`` defaults to ``~/.claude-live`` (outside the plugin install directory) so the
    action history survives plugin updates and uninstalls. ``CLAUDE_LIVE_HOME`` overrides it.
    """

    host: str = DEFAULT_HOST
    port: int = DEFAULT_PORT
    home: Path = field(default_factory=lambda: Path(DEFAULT_HOME).expanduser())
    log_level: str = DEFAULT_LOG_LEVEL
    warnings: tuple[str, ...] = ()

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> Settings:
        """Build settings from ``CLAUDE_LIVE_*`` variables; bad values fall back with a warning."""
        env = os.environ if env is None else env
        warnings: list[str] = []

        host = (env.get("CLAUDE_LIVE_HOST") or "").strip() or DEFAULT_HOST

        port = DEFAULT_PORT
        port_raw = (env.get("CLAUDE_LIVE_PORT") or "").strip()
        if port_raw:
            try:
                port = int(port_raw)
                if not 1 <= port <= 65535:
                    raise ValueError("out of range")
            except ValueError:
                warnings.append(f"CLAUDE_LIVE_PORT={port_raw!r} is not a valid port; using {DEFAULT_PORT}")
                port = DEFAULT_PORT

        home_raw = (env.get("CLAUDE_LIVE_HOME") or "").strip() or DEFAULT_HOME
        home = Path(home_raw).expanduser()

        log_level = ((env.get("CLAUDE_LIVE_LOG_LEVEL") or "").strip() or DEFAULT_LOG_LEVEL).upper()
        if log_level not in _LOG_LEVELS:
            warnings.append(f"CLAUDE_LIVE_LOG_LEVEL={log_level!r} is not a log level; using {DEFAULT_LOG_LEVEL}")
            log_level = DEFAULT_LOG_LEVEL

        return cls(host=host, port=port, home=home, log_level=log_level, warnings=tuple(warnings))

    # -- computed paths ---------------------------------------------------------------

    @property
    def history_dir(self) -> Path:
        return self.home / "history"

    @property
    def logs_dir(self) -> Path:
        return self.home / "logs"

    @property
    def log_file(self) -> Path:
        return self.logs_dir / "server.log"

    def ensure_dir(self, path: Path) -> Path:
        """Create ``path`` (and parents) on demand; directories are never created at import time."""
        path.mkdir(parents=True, exist_ok=True)
        return path
