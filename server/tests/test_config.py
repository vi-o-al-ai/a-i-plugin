"""Settings.from_env: loopback-only host, absolute home, 0700 directories, warnings surfaced by ableton_status."""

from __future__ import annotations

import os
import stat
from pathlib import Path

import pytest
from mcp.shared.memory import create_connected_server_and_client_session

from ableton_live_mcp.config import DEFAULT_HOST, Settings, is_loopback_host, make_private_dir
from ableton_live_mcp.server import build_server
from ableton_live_mcp.tools.common import AppContext


def test_loopback_hosts() -> None:
    for host in ("127.0.0.1", "127.0.0.2", "localhost", "LOCALHOST", "::1", " 127.0.0.1 "):
        assert is_loopback_host(host), host
    for host in ("0.0.0.0", "192.168.1.5", "10.0.0.1", "example.com", "live.local", "", "[::1]", "::"):
        assert not is_loopback_host(host), host


def test_host_accepts_loopback_only(tmp_path: Path) -> None:
    s = Settings.from_env({"CLAUDE_LIVE_HOST": "localhost", "CLAUDE_LIVE_HOME": str(tmp_path)})
    assert s.host == "localhost" and s.warnings == ()
    s = Settings.from_env({"CLAUDE_LIVE_HOST": "::1", "CLAUDE_LIVE_HOME": str(tmp_path)})
    assert s.host == "::1" and s.warnings == ()
    s = Settings.from_env({"CLAUDE_LIVE_HOST": "192.168.1.5", "CLAUDE_LIVE_HOME": str(tmp_path)})
    assert s.host == DEFAULT_HOST
    assert len(s.warnings) == 1 and "CLAUDE_LIVE_HOST='192.168.1.5' is not a loopback address" in s.warnings[0]
    s = Settings.from_env({"CLAUDE_LIVE_HOST": "evil.example.com", "CLAUDE_LIVE_HOME": str(tmp_path)})
    assert s.host == DEFAULT_HOST and "evil.example.com" in s.warnings[0]
    s = Settings.from_env({"CLAUDE_LIVE_HOST": "   ", "CLAUDE_LIVE_HOME": str(tmp_path)})
    assert s.host == DEFAULT_HOST and s.warnings == ()


def test_home_must_be_absolute(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("HOME", str(tmp_path))
    s = Settings.from_env({"CLAUDE_LIVE_HOME": str(tmp_path / "data")})
    assert s.home == (tmp_path / "data").resolve() and s.home.is_absolute() and s.warnings == ()
    s = Settings.from_env({"CLAUDE_LIVE_HOME": "~/elsewhere"})
    assert s.home == (tmp_path / "elsewhere").resolve() and s.warnings == ()
    s = Settings.from_env({"CLAUDE_LIVE_HOME": "relative/dir"})
    assert s.home == (tmp_path / ".claude-live").resolve()
    assert len(s.warnings) == 1 and "CLAUDE_LIVE_HOME='relative/dir' is not an absolute path" in s.warnings[0]
    s = Settings.from_env({})
    assert s.home == (tmp_path / ".claude-live").resolve()


def test_home_is_resolved(tmp_path: Path) -> None:
    real = tmp_path / "real"
    real.mkdir()
    link = tmp_path / "link"
    link.symlink_to(real, target_is_directory=True)
    s = Settings.from_env({"CLAUDE_LIVE_HOME": str(link)})
    assert s.home == real.resolve()


def test_bad_port_and_level_still_warn(tmp_path: Path) -> None:
    s = Settings.from_env({"CLAUDE_LIVE_PORT": "99999", "CLAUDE_LIVE_LOG_LEVEL": "LOUD", "CLAUDE_LIVE_HOME": str(tmp_path)})
    assert s.port == 9892 and s.log_level == "INFO" and len(s.warnings) == 2


@pytest.mark.skipif(os.name != "posix", reason="POSIX modes")
def test_ensure_dir_creates_private_directories(tmp_path: Path) -> None:
    os.umask(0o022)
    s = Settings.from_env({"CLAUDE_LIVE_HOME": str(tmp_path / "home")})
    created = s.ensure_dir(s.history_dir)
    assert created == s.home / "history" and created.is_dir()
    assert stat.S_IMODE(s.home.stat().st_mode) == 0o700
    assert stat.S_IMODE(created.stat().st_mode) == 0o700
    # a second call is a no-op and does not fail
    assert s.ensure_dir(s.history_dir) == created
    # pre-existing directories keep their mode
    other = tmp_path / "existing"
    other.mkdir(mode=0o755)
    make_private_dir(other)
    assert stat.S_IMODE(other.stat().st_mode) == 0o755


async def test_status_surfaces_config_warnings(fake_script, tmp_path: Path) -> None:
    settings = Settings.from_env({
        "CLAUDE_LIVE_HOST": "10.0.0.7",
        "CLAUDE_LIVE_PORT": str(fake_script.port),
        "CLAUDE_LIVE_HOME": "not/absolute",
    })
    settings = Settings(host=settings.host, port=settings.port, home=tmp_path / "home", log_level=settings.log_level, warnings=settings.warnings)
    assert settings.host == "127.0.0.1"
    app = AppContext(settings)
    server = build_server(settings, app=app)
    async with create_connected_server_and_client_session(server) as session:
        res = await session.call_tool("ableton_status", {})
    assert res.isError is False
    s = res.structuredContent
    assert s["connected"] is True  # the fallback host still reaches the (loopback) script
    assert s["host"] == "127.0.0.1"
    assert len(s["config_warnings"]) == 2
    assert "CLAUDE_LIVE_HOST='10.0.0.7' is not a loopback address" in s["config_warnings"][0]
    assert "CLAUDE_LIVE_HOME='not/absolute' is not an absolute path" in s["config_warnings"][1]
