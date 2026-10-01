"""End-to-end fixtures: the real Remote Script on the mock Live module, driven by a
background "Live main thread", plus the real MCP server as a stdio subprocess.

    MCP client (this process) --stdio--> ableton-live-mcp (uv subprocess)
                                             --TCP 127.0.0.1:<ephemeral>--> ClaudeLive
                                                                             --tick--> mock Live

Only the client side needs the ``mcp`` SDK, so the whole directory skips where it is absent.
The tests themselves are synchronous: a private event-loop thread owns the MCP session, so
the suite depends neither on pytest-asyncio nor on the ``asyncio_mode`` of whichever
pytest configuration happens to be in effect.

Fixtures are module-scoped: the history test must read the same server process that the
production sequence drove, and one Live set per module keeps the run fast.
"""
import pytest

pytest.importorskip("mcp")

import asyncio  # noqa: E402
import json  # noqa: E402
import os  # noqa: E402
import shutil  # noqa: E402
import socket  # noqa: E402
import sys  # noqa: E402
import threading  # noqa: E402
import time  # noqa: E402
from pathlib import Path  # noqa: E402

HERE = Path(__file__).resolve().parent
TESTS_DIR = HERE.parent
ROOT = TESTS_DIR.parent
MOCK_DIR = TESTS_DIR / "mock_live"
SCRIPT_DIR = ROOT / "remote-script"
SERVER_DIR = ROOT / "server"

# tests/conftest.py does the same, but it is only loaded when pytest's rootdir is above
# tests/ (not the case for `uv run --directory server pytest ../tests/integration`).
for _path in (str(SCRIPT_DIR), str(MOCK_DIR)):
    if _path not in sys.path:
        sys.path.insert(0, _path)

import Live  # noqa: E402
from Live import _core  # noqa: E402
import factory  # noqa: E402

import ClaudeLive as package  # noqa: E402
from ClaudeLive import config as config_module  # noqa: E402

from mcp.client.session import ClientSession  # noqa: E402
from mcp.client.stdio import StdioServerParameters, stdio_client  # noqa: E402
from mcp.types import TextContent  # noqa: E402

TICK_PERIOD_S = 0.01  # the background "Live main thread" ticks every ~10 ms
READY_TIMEOUT_S = 10.0
INIT_TIMEOUT_S = 90.0  # uv may have to build the venv on a cold CI runner
CALL_TIMEOUT_S = 120.0
SHUTDOWN_TIMEOUT_S = 30.0


# --------------------------------------------------------------------------
# Live set
# --------------------------------------------------------------------------

@pytest.fixture(scope="module")
def live_set():
    """The factory set installed as the mock application.

    Built on the pytest thread while no main thread is designated, so the guard is silent
    during construction; ``remote_script`` then hands the guard to the tick thread.
    """
    _core.clear_main_thread()
    del _core.VIOLATIONS[:]
    fake = factory.make_set()
    Live.Application._set_application(fake.app)
    try:
        yield fake
    finally:
        Live.Application._set_application(None)
        _core.clear_main_thread()


# --------------------------------------------------------------------------
# Remote Script + "Live main thread"
# --------------------------------------------------------------------------

def _script_config(log_file):
    cfg = dict(config_module.DEFAULTS)
    cfg.update({
        "port": 0,  # ephemeral
        "log_level": "DEBUG",
        "log_file": str(log_file),
        "_config_path": None,
        "_config_error": None,
    })
    return cfg


def ping_over_tcp(port, timeout=READY_TIMEOUT_S):
    """One raw ``sys.ping`` round trip: proves the listener accepts and the tick answers."""
    deadline = time.monotonic() + timeout
    with socket.create_connection(("127.0.0.1", port), timeout=timeout) as sock:
        sock.sendall(b'{"jsonrpc":"2.0","id":"ready","method":"sys.ping","params":{}}\n')
        buf = b""
        while b"\n" not in buf:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                raise TimeoutError("the Remote Script did not answer sys.ping within %.0f s" % timeout)
            sock.settimeout(remaining)
            chunk = sock.recv(65536)
            if not chunk:
                raise ConnectionError("the Remote Script closed the connection before answering sys.ping")
            buf += chunk
    return json.loads(buf.split(b"\n", 1)[0].decode("utf-8"))


class RemoteScript(object):
    """The running control surface, its port and the thread that plays Live's main thread."""

    def __init__(self, surface, c_instance, thread, stop_event, tick_errors):
        self.surface = surface
        self.c_instance = c_instance
        self.thread = thread
        self._stop = stop_event
        self.tick_errors = tick_errors

    @property
    def port(self):
        return self.surface.server.port

    @property
    def violations(self):
        return list(_core.VIOLATIONS)

    def stop(self):
        self._stop.set()
        self.thread.join(5.0)


@pytest.fixture(scope="module")
def remote_script(live_set, tmp_path_factory):
    log_dir = tmp_path_factory.mktemp("remote-script")
    cfg = _script_config(log_dir / "ClaudeLive.log")
    c_instance = factory.FakeCInstance(live_set.song)
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(config_module, "load_config", lambda path=None: dict(cfg))
        surface = package.create_instance(c_instance)
    surface.c_instance = c_instance
    assert surface.server.port, "the Remote Script did not open its listening port: %r" % (c_instance.shown,)

    stop = threading.Event()
    tick_errors = []

    def live_main_thread():
        while not stop.is_set():
            try:
                surface.tick()
            except Exception as exc:  # noqa: BLE001 - reported at teardown
                tick_errors.append(exc)
            stop.wait(TICK_PERIOD_S)

    thread = threading.Thread(target=live_main_thread, name="LiveMainThread", daemon=True)
    # Designate the tick thread before it starts so the guard covers its very first tick.
    _core.set_main_thread(thread)
    thread.start()
    script = RemoteScript(surface, c_instance, thread, stop, tick_errors)
    try:
        pong = ping_over_tcp(script.port)
        assert pong.get("result", {}).get("protocol_version") == 1, pong
        yield script
    finally:
        script.stop()
        alive = thread.is_alive()
        surface.disconnect()
        assert not alive, "the Live main thread did not stop"
        assert tick_errors == [], "tick thread raised: %r" % (tick_errors,)
        assert _core.VIOLATIONS == [], "LOM touched off the main thread: %r" % (_core.VIOLATIONS,)


# --------------------------------------------------------------------------
# MCP server subprocess + client session
# --------------------------------------------------------------------------

class McpSession(object):
    """A live ``ClientSession`` (owned by a private loop thread) with synchronous helpers."""

    def __init__(self, loop, session, home, port, stderr_path):
        self.loop = loop
        self.session = session
        self.home = home
        self.port = port
        self.stderr_path = stderr_path

    def run(self, coro, timeout=CALL_TIMEOUT_S):
        return asyncio.run_coroutine_threadsafe(coro, self.loop).result(timeout)

    def list_tools(self):
        return self.run(self.session.list_tools()).tools

    def call(self, tool, **args):
        """Invoke ``tool``; returns ``(structured_result_or_None, text, is_error)``."""
        result = self.run(self.session.call_tool(tool, args))
        text = "\n".join(block.text for block in result.content if isinstance(block, TextContent))
        return result.structuredContent, text, bool(result.isError)

    def ok(self, tool, **args):
        """Call and assert success; returns the structured result."""
        structured, text, is_error = self.call(tool, **args)
        assert not is_error, "%s(%r) failed: %s" % (tool, args, text)
        assert isinstance(structured, dict), "%s returned no structured object: %r" % (tool, text)
        return structured

    def err(self, tool, **args):
        """Call and assert failure; returns the error text."""
        _structured, text, is_error = self.call(tool, **args)
        assert is_error, "%s(%r) unexpectedly succeeded: %s" % (tool, args, text)
        return text

    def server_stderr(self):
        try:
            return self.stderr_path.read_text(encoding="utf-8", errors="replace")
        except OSError:
            return ""


@pytest.fixture(scope="module")
def mcp_session(remote_script, tmp_path_factory):
    if shutil.which("uv") is None:
        pytest.skip("uv is required to launch the ableton-live-mcp server subprocess")
    home = tmp_path_factory.mktemp("claude-live-home")
    stderr_path = home / "server.stderr.log"
    params = StdioServerParameters(
        command="uv",
        args=["run", "--frozen", "--directory", str(SERVER_DIR), "ableton-live-mcp"],
        env={
            **os.environ,
            "CLAUDE_LIVE_PORT": str(remote_script.port),
            "CLAUDE_LIVE_HOME": str(home),
            "CLAUDE_LIVE_LOG_LEVEL": "DEBUG",
        },
    )

    loop = asyncio.new_event_loop()
    ready = threading.Event()
    state = {}
    errlog = stderr_path.open("w", encoding="utf-8")

    async def runner():
        stop = asyncio.Event()
        state["stop"] = stop
        try:
            async with stdio_client(params, errlog=errlog) as (read_stream, write_stream):
                async with ClientSession(read_stream, write_stream) as session:
                    state["init"] = await asyncio.wait_for(session.initialize(), INIT_TIMEOUT_S)
                    state["session"] = session
                    ready.set()
                    await stop.wait()
        except BaseException as exc:  # noqa: BLE001 - reported to the pytest thread
            state.setdefault("startup_error" if not ready.is_set() else "shutdown_error", exc)
            ready.set()
            raise

    thread = threading.Thread(target=lambda: loop.run_until_complete(runner()), name="McpClientLoop", daemon=True)
    thread.start()
    ready.wait(INIT_TIMEOUT_S + 10.0)

    def stop_loop():
        stop = state.get("stop")
        if stop is not None:
            loop.call_soon_threadsafe(stop.set)
        thread.join(SHUTDOWN_TIMEOUT_S)
        if not loop.is_closed():
            loop.close()
        errlog.close()

    if "session" not in state:
        stop_loop()
        stderr_text = stderr_path.read_text(encoding="utf-8", errors="replace") if stderr_path.exists() else ""
        raise RuntimeError(
            "the MCP server did not initialise: %r\n--- server stderr ---\n%s" % (state.get("startup_error"), stderr_text)
        )
    assert state["init"].serverInfo.name == "ableton-live", state["init"]

    session = McpSession(loop, state["session"], home, remote_script.port, stderr_path)
    try:
        yield session
    finally:
        stop_loop()
        assert not thread.is_alive(), "the MCP client loop thread did not stop"
        assert "shutdown_error" not in state, "MCP session shutdown raised: %r" % (state.get("shutdown_error"),)
