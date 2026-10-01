"""Server settings read from the environment (see TOOLS.md "Environment variables")."""

from __future__ import annotations

import ipaddress
import os
from collections.abc import Mapping
from dataclasses import dataclass, field
from pathlib import Path

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 9892
DEFAULT_HOME = "~/.claude-live"
DEFAULT_LOG_LEVEL = "INFO"

PRIVATE_DIR_MODE = 0o700

_LOG_LEVELS = ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL")


def is_loopback_host(host: str) -> bool:
    """``localhost`` or any loopback IP literal; the Remote Script only ever listens on loopback."""
    host = host.strip()
    if not host:
        return False
    if host.lower() == "localhost":
        return True
    try:
        return ipaddress.ip_address(host).is_loopback
    except ValueError:
        return False


def make_private_dir(path: Path) -> Path:
    """``mkdir -p`` with mode 0700 on every directory this call creates (best effort)."""
    created: list[Path] = []
    probe = path
    while not probe.exists():
        created.append(probe)
        if probe.parent == probe:
            break
        probe = probe.parent
    path.mkdir(parents=True, exist_ok=True)
    for directory in created:
        try:
            directory.chmod(PRIVATE_DIR_MODE)
        except OSError:  # pragma: no cover - filesystem without POSIX modes
            pass
    return path


def _default_home() -> Path:
    return Path(DEFAULT_HOME).expanduser()


@dataclass(frozen=True)
class Settings:
    """Where the Remote Script listens and where this server keeps its data.

    ``home`` defaults to ``~/.claude-live`` (outside the plugin install directory) so the
    action history survives plugin updates and uninstalls. ``CLAUDE_LIVE_HOME`` overrides it.
    """

    host: str = DEFAULT_HOST
    port: int = DEFAULT_PORT
    home: Path = field(default_factory=_default_home)
    log_level: str = DEFAULT_LOG_LEVEL
    warnings: tuple[str, ...] = ()

    @classmethod
    def from_env(cls, env: Mapping[str, str] | None = None) -> Settings:
        """Build settings from ``CLAUDE_LIVE_*`` variables; bad values fall back with a warning.

        Only loopback hosts are accepted (nothing ever leaves this machine) and only an
        absolute ``CLAUDE_LIVE_HOME``; anything else is ignored with a warning that
        ``ableton_status`` surfaces as ``config_warnings``.
        """
        env = os.environ if env is None else env
        warnings: list[str] = []

        host = DEFAULT_HOST
        host_raw = (env.get("CLAUDE_LIVE_HOST") or "").strip()
        if host_raw:
            if is_loopback_host(host_raw):
                host = host_raw
            else:
                warnings.append(
                    f"CLAUDE_LIVE_HOST={host_raw!r} is not a loopback address; the ClaudeLive Remote Script only "
                    f"listens on this machine, so it is ignored and {DEFAULT_HOST} is used"
                )

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

        home = _default_home()
        home_raw = (env.get("CLAUDE_LIVE_HOME") or "").strip()
        if home_raw:
            try:
                candidate = Path(home_raw).expanduser()
            except RuntimeError:  # ~user with no resolvable home directory
                candidate = Path(home_raw)
            if candidate.is_absolute():
                home = candidate
            else:
                warnings.append(f"CLAUDE_LIVE_HOME={home_raw!r} is not an absolute path; using {home}")
        try:
            home = home.resolve()
        except OSError:  # pragma: no cover - unresolvable symlink chain; keep the expanded path
            pass

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
        """Create ``path`` (and parents) on demand with mode 0700; nothing is created at import time."""
        return make_private_dir(path)
