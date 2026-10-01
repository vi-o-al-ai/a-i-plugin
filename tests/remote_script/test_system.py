"""sys.* handlers, package import and protocol coverage."""
import io
import os
import re

import ClaudeLive as package
from ClaudeLive.handlers import METHODS

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PROTOCOL = os.path.join(ROOT, "docs", "PROTOCOL.md")


def test_create_instance_exposed():
    assert callable(package.create_instance)


def test_every_protocol_method_is_registered():
    """Every `ns.name` row in the PROTOCOL.md method tables has a handler, and the
    only handler allowed to be missing from the tables is the dev convenience
    sys.reload_handlers (documented or not)."""
    with io.open(PROTOCOL, "r", encoding="utf-8") as handle:
        text = handle.read()
    documented = set(re.findall(r"^\| `([a-z]+\.[a-z_]+)`", text, re.M))
    assert len(documented) >= 60
    assert documented - set(METHODS) == set()
    assert set(METHODS) - documented <= {"sys.reload_handlers"}
    assert all(callable(fn) for fn in METHODS.values())


def test_ping_shape(rpc, harness):
    harness.tick(3)
    result = rpc("sys.ping")
    assert result["protocol_version"] == 1
    assert isinstance(result["script_version"], str)
    assert result["live_version"] == "12.1.5"
    assert result["live_major"] == 12
    assert result["live_minor"] == 1
    assert result["python_version"].count(".") == 2
    assert result["tick_count"] >= 2


def test_ping_ignores_unknown_params(rpc):
    result = rpc("sys.ping", why="checking the connection")
    assert result["protocol_version"] == 1


def test_describe_api_writes_markdown(rpc, tmp_path):
    path = str(tmp_path / "dump.md")
    result = rpc("sys.describe_api", path=path)
    assert result["path"] == path
    assert result["classes"] > 10
    assert result["bytes"] > 1000
    text = open(path, encoding="utf-8").read()
    assert "## Live.Song.Song" in text
    assert "## Live.Clip.MidiNoteSpecification" in text
    assert "## _Framework.ControlSurface.ControlSurface" in text
    assert "get_notes_extended" in text


def test_describe_api_filters_classes(rpc, tmp_path):
    path = str(tmp_path / "dump.md")
    result = rpc("sys.describe_api", path=path, classes=["Song", "Live.Clip.Clip"])
    assert result["classes"] == 2
    text = open(path, encoding="utf-8").read()
    assert "## Live.Song.Song" in text
    assert "## Live.Track.Track" not in text


def test_describe_api_default_path(rpc, monkeypatch, tmp_path):
    from ClaudeLive import introspect
    monkeypatch.setattr(introspect, "PACKAGE_DIR", str(tmp_path))
    result = rpc("sys.describe_api")
    assert result["path"] == os.path.join(str(tmp_path), "live_api_dump.md")
    assert os.path.exists(result["path"])


def test_log_writes_to_live_log(rpc, control_surface):
    result = rpc("sys.log", message="hello from the test")
    assert result == {"ok": True}
    assert any("[ClaudeLive] hello from the test" in line for line in control_surface.c_instance.logged)


def test_log_requires_message(rpc):
    error = rpc.err("sys.log")
    assert error["code"] == -32602


def test_reload_handlers_keeps_methods_working(rpc, control_surface):
    before = len(control_surface.dispatcher.methods)
    result = rpc("sys.reload_handlers")
    assert "ClaudeLive.handlers.song" in result["reloaded"]
    assert "ClaudeLive.lom" in result["reloaded"]
    assert result["methods"] == before
    # The dispatcher holds the same dict object, rebuilt in place.
    assert rpc("sys.ping")["protocol_version"] == 1
    assert rpc("song.get_transport")["tempo"] == 120.0


def test_logger_mirrors_warnings_to_live_log(control_surface):
    control_surface.rpc_logger.warning("something odd")
    assert any("[ClaudeLive] WARNING: something odd" in line for line in control_surface.c_instance.logged)
    control_surface.rpc_logger.info("quiet")
    assert not any("quiet" in line for line in control_surface.c_instance.logged)


def test_log_file_written(control_surface, test_config):
    control_surface.rpc_logger.info("to file")
    for handler in control_surface.rpc_logger.handlers:
        handler.flush()
    text = open(test_config["log_file"], encoding="utf-8").read()
    assert "[ClaudeLive] to file" in text
    assert "listening on 127.0.0.1" in text


def test_startup_message_shown(control_surface):
    assert any("listening on 127.0.0.1" in msg for msg in control_surface.c_instance.shown)
