"""pytest fixtures: the mock Live on sys.path first, a populated fake set, a
ClaudeLive instance driven by a tick harness, and RPC / TCP helpers."""
import json
import os
import socket
import sys
import threading
import time

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
MOCK_DIR = os.path.join(HERE, "mock_live")
SCRIPT_DIR = os.path.join(ROOT, "remote-script")
for path in (SCRIPT_DIR, MOCK_DIR):
    while path in sys.path:
        sys.path.remove(path)
sys.path.insert(0, SCRIPT_DIR)
sys.path.insert(0, MOCK_DIR)  # must shadow any real `Live`

import pytest  # noqa: E402

import Live  # noqa: E402
from Live import _core  # noqa: E402
import factory  # noqa: E402

import ClaudeLive as package  # noqa: E402
from ClaudeLive import config as config_module  # noqa: E402

TEST_CONFIG = {
    "host": "127.0.0.1",
    "port": 0,  # ephemeral
    "log_level": "DEBUG",
    "max_requests_per_tick": 32,
    "max_tick_ms": 1000,  # never trip the time budget in tests unless a test lowers it
    "dev_mode": False,
    "queue_max": 256,
    "max_connections": 8,
    "max_line_bytes": 4 * 1024 * 1024,
    "browser_time_budget_ms": 1000,
    "browser_cache_ttl_s": 60,
    "log_file": None,
    "_config_error": None,
}


# --------------------------------------------------------------------------
# Fake Live
# --------------------------------------------------------------------------

@pytest.fixture
def fake_live():
    _core.set_main_thread(threading.current_thread())
    del _core.VIOLATIONS[:]
    fake = factory.make_set()
    Live.Application._set_application(fake.app)
    try:
        yield fake
    finally:
        Live.Application._set_application(None)
        _core.clear_main_thread()


@pytest.fixture
def test_config(tmp_path):
    cfg = dict(TEST_CONFIG)
    cfg["log_file"] = str(tmp_path / "ClaudeLive.log")
    return cfg


@pytest.fixture
def control_surface(fake_live, test_config, monkeypatch, tmp_path):
    # sys.describe_api writes under ~/.claude-live; never let a test touch the real home.
    monkeypatch.setenv("HOME", str(tmp_path))
    monkeypatch.setattr(config_module, "load_config", lambda path=None: dict(test_config))
    c_instance = factory.FakeCInstance(fake_live.song)
    surface = package.create_instance(c_instance)
    surface.c_instance = c_instance
    try:
        yield surface
    finally:
        surface.disconnect()


# --------------------------------------------------------------------------
# Harness
# --------------------------------------------------------------------------

class Harness(object):
    """Drives the fake ControlSurface tick from the test (= designated main) thread."""

    def __init__(self, surface, fake):
        self.surface = surface
        self.fake = fake

    def tick(self, count=1):
        for _ in range(count):
            self.surface.tick()

    def tick_until(self, predicate, max_ticks=500, pause=0.002):
        for _ in range(max_ticks):
            self.tick()
            if predicate():
                return True
            time.sleep(pause)
        return predicate()


@pytest.fixture
def harness(control_surface, fake_live):
    return Harness(control_surface, fake_live)


class RpcError(AssertionError):
    def __init__(self, error):
        AssertionError.__init__(self, "RPC error %s: %s %r" % (error.get("code"), error.get("message"), error.get("data")))
        self.code = error.get("code")
        self.message = error.get("message")
        self.data = error.get("data")


class Rpc(object):
    """Sends requests straight through the dispatcher (synchronously, on the test thread)."""

    def __init__(self, surface):
        self.surface = surface
        self._next_id = 0

    def call(self, method, params=None, request_id=None):
        if request_id is None:
            self._next_id += 1
            request_id = self._next_id
        payload = {"jsonrpc": "2.0", "id": request_id, "method": method}
        if params is not None:
            payload["params"] = params
        return self.surface.dispatcher.handle(payload)

    def raw(self, payload):
        return self.surface.dispatcher.handle(payload)

    def __call__(self, method, **params):
        response = self.call(method, params)
        assert response is not None, "no response for %s" % method
        if "error" in response:
            raise RpcError(response["error"])
        return response["result"]

    def err(self, method, **params):
        response = self.call(method, params)
        assert response is not None and "error" in response, "expected an error from %s, got %r" % (method, response)
        return response["error"]


@pytest.fixture
def rpc(control_surface):
    return Rpc(control_surface)


class TcpClient(object):
    """Talks to the real TCPServer over localhost while ticking the harness."""

    def __init__(self, harness, port):
        self.harness = harness
        self.sock = socket.create_connection(("127.0.0.1", port), timeout=2.0)
        self.sock.settimeout(0.01)
        self.buffer = b""
        self._next_id = 0

    def send_raw(self, data):
        # Large payloads need the reader thread to drain; do not let the short
        # read timeout abort a multi-chunk send.
        self.sock.settimeout(5.0)
        try:
            self.sock.sendall(data)
        finally:
            self.sock.settimeout(0.01)

    def send(self, payload):
        self.send_raw(json.dumps(payload).encode("utf-8") + b"\n")

    def read_line(self, max_ticks=400):
        for _ in range(max_ticks):
            newline = self.buffer.find(b"\n")
            if newline >= 0:
                line = self.buffer[:newline]
                self.buffer = self.buffer[newline + 1:]
                return line
            self.harness.tick()
            try:
                chunk = self.sock.recv(65536)
            except socket.timeout:
                continue
            except ConnectionError:
                return None  # reset by the server (e.g. refused for max_connections): same as EOF
            if not chunk:
                return None
            self.buffer += chunk
        return None

    def read_response(self, max_ticks=400):
        line = self.read_line(max_ticks)
        assert line is not None, "no response line received"
        return json.loads(line.decode("utf-8"))

    def request(self, method, params=None, request_id=None):
        if request_id is None:
            self._next_id += 1
            request_id = self._next_id
        payload = {"jsonrpc": "2.0", "id": request_id, "method": method}
        if params is not None:
            payload["params"] = params
        self.send(payload)
        return self.read_response()

    def close(self):
        try:
            self.sock.close()
        except OSError:
            pass


@pytest.fixture
def tcp_client(control_surface, harness):
    client = TcpClient(harness, control_surface.server.port)
    try:
        yield client
    finally:
        client.close()


@pytest.fixture
def make_tcp_client(control_surface, harness):
    clients = []

    def _make():
        client = TcpClient(harness, control_surface.server.port)
        clients.append(client)
        return client

    try:
        yield _make
    finally:
        for client in clients:
            client.close()
