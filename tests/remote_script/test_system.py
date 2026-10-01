"""sys.* handlers, package import and protocol coverage."""
import io
import os
import re
import stat
import threading

import pytest

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


def test_settings_wording_in_docstring():
    assert "Settings → Link, Tempo & MIDI → Control Surface" in package.__doc__
    assert "called Preferences in older Live versions" in package.__doc__


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


def _api_dir(home):
    return os.path.join(str(home), ".claude-live", "api")


def test_describe_api_writes_markdown_under_home(rpc, monkeypatch, tmp_path):
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    result = rpc("sys.describe_api")
    assert set(result) == {"path", "classes", "bytes"}
    assert result["path"] == os.path.join(_api_dir(home), "live_api_12.1.5.md")
    assert result["classes"] > 10
    assert result["bytes"] > 1000
    text = open(result["path"], encoding="utf-8").read()
    assert "## Live.Song.Song" in text
    assert "## Live.Clip.MidiNoteSpecification" in text
    assert "## _Framework.ControlSurface.ControlSurface" in text
    assert "get_notes_extended" in text
    # Nothing is written to the package dir when the home location works.
    assert not os.path.exists(os.path.join(ROOT, "remote-script", "ClaudeLive", "live_api_dump.md"))


@pytest.mark.skipif(os.name != "posix", reason="directory modes are POSIX only")
def test_describe_api_creates_private_directories(rpc, monkeypatch, tmp_path):
    home = tmp_path / "home"
    home.mkdir()
    monkeypatch.setenv("HOME", str(home))
    rpc("sys.describe_api", classes=["Song"])
    for directory in (os.path.join(str(home), ".claude-live"), _api_dir(home)):
        assert stat.S_IMODE(os.stat(directory).st_mode) == 0o700, directory
    # Second call reuses the directories (no error on existing dirs) and overwrites the dump.
    assert rpc("sys.describe_api", classes=["Song"])["classes"] == 1


def test_describe_api_filters_classes(rpc, monkeypatch, tmp_path):
    monkeypatch.setenv("HOME", str(tmp_path))
    result = rpc("sys.describe_api", classes=["Song", "Live.Clip.Clip"])
    assert result["classes"] == 2
    text = open(result["path"], encoding="utf-8").read()
    assert "## Live.Song.Song" in text
    assert "## Live.Track.Track" not in text
    assert rpc.err("sys.describe_api", classes=[1])["code"] == -32602
    assert rpc.err("sys.describe_api", classes="Song")["code"] == -32602


def test_describe_api_rejects_path_parameter(rpc, monkeypatch, tmp_path):
    monkeypatch.setenv("HOME", str(tmp_path))
    for path in ("/tmp/x.md", "../x.md", "dump.md", "", None):
        error = rpc.err("sys.describe_api", path=path)
        assert error["code"] == -32602 and error["data"]["parameter"] == "path", path
    assert not os.path.exists(os.path.join(_api_dir(tmp_path)))
    assert not os.path.exists(os.path.join(str(tmp_path), "x.md"))


def test_describe_api_falls_back_to_package_dir(rpc, monkeypatch, tmp_path):
    from ClaudeLive import introspect
    blocker = tmp_path / "not-a-directory"
    blocker.write_text("x", encoding="utf-8")
    monkeypatch.setenv("HOME", str(blocker))  # ~/.claude-live/api cannot be created under a file
    package_dir = tmp_path / "pkg"
    package_dir.mkdir()
    monkeypatch.setattr(introspect, "PACKAGE_DIR", str(package_dir))
    result = rpc("sys.describe_api", classes=["Song"])
    assert result["path"] == os.path.join(str(package_dir), "live_api_dump.md")
    assert os.path.exists(result["path"]) and result["classes"] == 1


def test_describe_api_version_in_filename_is_sanitised():
    from ClaudeLive.handlers import system as system_handlers
    path = system_handlers.api_dump_path("12.1.5 beta/../x")
    assert os.path.basename(path) == "live_api_12.1.5_beta_._x.md"
    assert os.sep not in os.path.basename(path) and "/" not in os.path.basename(path)
    assert os.path.basename(system_handlers.api_dump_path("")) == "live_api_unknown.md"
    assert os.path.basename(system_handlers.api_dump_path("../../etc")) == "live_api_etc.md"


def test_log_writes_to_live_log(rpc, control_surface):
    result = rpc("sys.log", message="hello from the test")
    assert result == {"ok": True}
    assert any("[ClaudeLive] hello from the test" in line for line in control_surface.c_instance.logged)


def test_log_is_truncated_and_single_line(rpc, control_surface):
    message = "line one\nline two\r\n" + "x" * 2000
    assert rpc("sys.log", message=message) == {"ok": True}
    lines = [line for line in control_surface.c_instance.logged if "line one" in line]
    assert len(lines) == 1
    logged = lines[0]
    assert "\n" not in logged and "\r" not in logged
    assert "line one line two" in logged
    body = logged.split("[ClaudeLive] ", 1)[1]
    assert len(body) == 1000


def test_log_requires_message(rpc):
    error = rpc.err("sys.log")
    assert error["code"] == -32602
    assert rpc.err("sys.log", message=5)["code"] == -32602


def test_reload_handlers_hidden_without_dev_mode(rpc, control_surface):
    assert control_surface.settings.get("dev_mode") is False
    error = rpc.err("sys.reload_handlers")
    assert error["code"] == -32601 and error["data"] == {"method": "sys.reload_handlers"}
    # Anything but a literal true keeps it hidden.
    control_surface.settings["dev_mode"] = "yes"
    assert rpc.err("sys.reload_handlers")["code"] == -32601


def test_reload_handlers_keeps_methods_working(rpc, control_surface):
    control_surface.settings["dev_mode"] = True
    before = len(control_surface.dispatcher.methods)
    result = rpc("sys.reload_handlers")
    assert "ClaudeLive.handlers.song" in result["reloaded"]
    assert "ClaudeLive.lom" in result["reloaded"]
    assert result["methods"] == before
    # The dispatcher holds the same dict object, rebuilt in place.
    assert rpc("sys.ping")["protocol_version"] == 1
    assert rpc("song.get_transport")["tempo"] == 120.0
    control_surface.settings["dev_mode"] = False
    assert rpc.err("sys.reload_handlers")["code"] == -32601


def test_logger_mirrors_warnings_to_live_log(control_surface):
    control_surface.rpc_logger.warning("something odd")
    assert any("[ClaudeLive] WARNING: something odd" in line for line in control_surface.c_instance.logged)
    control_surface.rpc_logger.info("quiet")
    assert not any("quiet" in line for line in control_surface.c_instance.logged)


def test_off_thread_log_records_are_deferred_to_the_tick(control_surface, harness):
    logged = control_surface.c_instance.logged
    worker = threading.Thread(target=lambda: control_surface.rpc_logger.warning("from a socket thread"))
    worker.start()
    worker.join(5.0)
    # Not written yet: log_message reaches Live's C++ side and may only run on the main thread.
    assert not any("from a socket thread" in line for line in logged)
    harness.tick()
    assert any("[ClaudeLive] WARNING: from a socket thread" in line for line in logged)
    harness.tick()
    assert sum(1 for line in logged if "from a socket thread" in line) == 1


def test_deferred_log_queue_is_bounded(control_surface, harness):
    from ClaudeLive import logger as logger_module
    for i in range(logger_module.DEFERRED_MAX + 50):
        worker = threading.Thread(target=control_surface.rpc_logger.warning, args=("flood %d" % i,))
        worker.start()
        worker.join(5.0)
    harness.tick()
    flooded = [line for line in control_surface.c_instance.logged if "flood " in line]
    assert len(flooded) == logger_module.DEFERRED_MAX
    assert "flood 249" in flooded[-1]  # the newest records survive


def test_log_file_written(control_surface, test_config):
    control_surface.rpc_logger.info("to file")
    for handler in control_surface.rpc_logger.handlers:
        handler.flush()
    text = open(test_config["log_file"], encoding="utf-8").read()
    assert "[ClaudeLive] to file" in text
    assert "listening on 127.0.0.1" in text


def test_startup_message_shown(control_surface):
    assert any("listening on 127.0.0.1" in msg for msg in control_surface.c_instance.shown)
