"""The remote script must run on Live 12.0/12.1 (Python 3.7) and 12.3 (Python 3.11)."""
import ast
import io
import os
import re
import shutil
import subprocess
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
PACKAGE = os.path.join(ROOT, "remote-script", "ClaudeLive")


def _python_files():
    for directory, _dirs, files in os.walk(PACKAGE):
        if "__pycache__" in directory:
            continue
        for name in files:
            if name.endswith(".py"):
                yield os.path.join(directory, name)


def _vermin_command():
    executable = shutil.which("vermin")
    if executable:
        return [executable]
    try:
        import vermin  # noqa: F401
    except ImportError:
        return None
    return [sys.executable, "-c", "from vermin.main import main; main()"]


def test_package_has_expected_modules():
    names = sorted(os.path.relpath(p, PACKAGE) for p in _python_files())
    assert "__init__.py" in names and "ClaudeLive.py" in names
    assert os.path.join("handlers", "notes.py") in names
    assert len(names) == 21


@pytest.mark.skipif(_vermin_command() is None, reason="vermin is not installed")
def test_vermin_reports_py37_compatible():
    command = _vermin_command() + ["-t=3.7-", "--no-tips", "--violations", PACKAGE]
    proc = subprocess.run(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, universal_newlines=True)
    assert proc.returncode == 0, proc.stdout
    match = re.search(r"Minimum required versions:\s*(.+)", proc.stdout)
    assert match, proc.stdout
    for version in re.findall(r"3\.(\d+)", match.group(1)):
        assert int(version) <= 7, proc.stdout


@pytest.mark.skipif(sys.version_info < (3, 8), reason="ast feature_version needs Python 3.8+")
def test_ast_parses_with_feature_version_37():
    for path in _python_files():
        with io.open(path, "r", encoding="utf-8") as handle:
            source = handle.read()
        ast.parse(source, filename=path, feature_version=(3, 7))


def test_only_stdlib_and_live_imports():
    allowed_roots = {"Live", "_Framework"}
    stdlib = set(getattr(sys, "stdlib_module_names", ()))
    for path in _python_files():
        with io.open(path, "r", encoding="utf-8") as handle:
            tree = ast.parse(handle.read(), filename=path)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                roots = [alias.name.split(".")[0] for alias in node.names]
            elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
                roots = [node.module.split(".")[0]]
            else:
                continue
            for root in roots:
                assert root in allowed_roots or not stdlib or root in stdlib, "%s imports %s" % (path, root)


def test_never_saves_the_set():
    pattern = re.compile(r"\bsave\w*\s*\(|\.save\b|save_set|save_live_set", re.IGNORECASE)
    for path in _python_files():
        with io.open(path, "r", encoding="utf-8") as handle:
            for number, line in enumerate(handle, 1):
                assert not pattern.search(line), "%s:%d looks like a save call: %s" % (path, number, line.strip())


def test_config_json_matches_defaults():
    import json
    from ClaudeLive import config
    with io.open(os.path.join(PACKAGE, "config.json"), "r", encoding="utf-8") as handle:
        shipped = json.load(handle)
    assert shipped == {"host": "127.0.0.1", "port": 9892, "log_level": "INFO", "max_requests_per_tick": 32,
                       "max_tick_ms": 50, "dev_mode": False}
    loaded = config.load_config(os.path.join(PACKAGE, "config.json"))
    assert loaded["port"] == 9892 and loaded["_config_error"] is None
    assert loaded["dev_mode"] is False and loaded["queue_max"] == 256 and loaded["max_connections"] == 8


def test_config_never_crashes_on_bad_file(tmp_path):
    from ClaudeLive import config
    bad = tmp_path / "config.json"
    bad.write_text("{not json", encoding="utf-8")
    loaded = config.load_config(str(bad))
    assert loaded["port"] == 9892 and "could not read" in loaded["_config_error"]
    bad.write_text('{"port": "abc", "host": "0.0.0.0", "max_tick_ms": -5, "log_level": "LOUD"}', encoding="utf-8")
    loaded = config.load_config(str(bad))
    assert loaded["port"] == 9892 and loaded["host"] == "127.0.0.1"
    assert loaded["max_tick_ms"] == 50 and loaded["log_level"] == "INFO"
    assert "loopback" in loaded["_config_error"]
    loaded = config.load_config(str(tmp_path / "missing.json"))
    assert loaded["port"] == 9892 and "not found" in loaded["_config_error"]
    bad.write_text("[1, 2, 3]", encoding="utf-8")
    assert config.load_config(str(bad))["port"] == 9892


def _load(tmp_path, payload):
    import json
    from ClaudeLive import config
    path = tmp_path / "config.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return config.load_config(str(path))


@pytest.mark.parametrize("host", ["0.0.0.0", "192.168.1.5", "::1", "::ffff:127.0.0.1", "example.com", "", 5, None,
                                  True, ["127.0.0.1"]])
def test_config_non_ipv4_loopback_host_is_forced_to_127_0_0_1(tmp_path, host):
    loaded = _load(tmp_path, {"host": host})
    assert loaded["host"] == "127.0.0.1"
    assert "loopback" in loaded["_config_error"] and "127.0.0.1" in loaded["_config_error"]


@pytest.mark.parametrize("host,expected", [("127.0.0.1", "127.0.0.1"), ("127.0.0.5", "127.0.0.5"),
                                           (" 127.0.0.1 ", "127.0.0.1"), ("localhost", "127.0.0.1"),
                                           ("LOCALHOST", "127.0.0.1")])
def test_config_ipv4_loopback_hosts_are_accepted(tmp_path, host, expected):
    loaded = _load(tmp_path, {"host": host})
    assert loaded["host"] == expected and loaded["_config_error"] is None


def test_config_loopback_helper():
    from ClaudeLive import config
    assert config.loopback_host("::1") is None
    assert config.loopback_host("127.1.2.3") == "127.1.2.3"
    assert config.loopback_host("localhost") == "127.0.0.1"
    assert config.loopback_host(None) is None


@pytest.mark.parametrize("port", [0, -1, 65536, 70000, "abc", 1.5, True, None, [9892]])
def test_config_port_out_of_range_uses_default(tmp_path, port):
    loaded = _load(tmp_path, {"port": port})
    assert loaded["port"] == 9892 and "port" in loaded["_config_error"]


def test_config_port_bounds(tmp_path):
    assert _load(tmp_path, {"port": 1})["port"] == 1
    assert _load(tmp_path, {"port": 65535})["port"] == 65535
    assert _load(tmp_path, {"port": 9000.0})["port"] == 9000  # whole-number floats are fine
    assert _load(tmp_path, {"port": "9001"})["port"] == 9001  # as are numeric strings


def test_config_new_keys_defaults_and_validation(tmp_path):
    loaded = _load(tmp_path, {})
    assert loaded["dev_mode"] is False and loaded["queue_max"] == 256 and loaded["max_connections"] == 8
    loaded = _load(tmp_path, {"dev_mode": True, "queue_max": 16, "max_connections": 2})
    assert loaded["dev_mode"] is True and loaded["queue_max"] == 16 and loaded["max_connections"] == 2
    assert loaded["_config_error"] is None
    loaded = _load(tmp_path, {"dev_mode": "yes", "queue_max": 0, "max_connections": "many"})
    assert loaded["dev_mode"] is False and loaded["queue_max"] == 256 and loaded["max_connections"] == 8
    assert "dev_mode" in loaded["_config_error"] and "queue_max" in loaded["_config_error"]
    assert "max_connections" in loaded["_config_error"]


def test_config_reads_utf8_with_bom(tmp_path):
    from ClaudeLive import config
    path = tmp_path / "config.json"
    path.write_bytes(b'\xef\xbb\xbf{"port": 9000, "log_level": "DEBUG"}')
    loaded = config.load_config(str(path))
    assert loaded["port"] == 9000 and loaded["log_level"] == "DEBUG" and loaded["_config_error"] is None
