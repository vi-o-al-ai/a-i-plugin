"""Wire framing over the real TCP server, and the threading model."""
import json
import socket
import threading
import time

import pytest

from Live import _core
from ClaudeLive.handlers import song as song_handlers


def _line(payload):
    return json.dumps(payload).encode("utf-8") + b"\n"


def test_ping_over_tcp(tcp_client):
    response = tcp_client.request("sys.ping")
    assert response["id"] == 1
    assert response["result"]["protocol_version"] == 1


def test_two_requests_in_one_write(tcp_client):
    data = _line({"jsonrpc": "2.0", "id": 1, "method": "sys.ping"}) + \
        _line({"jsonrpc": "2.0", "id": 2, "method": "song.get_transport"})
    tcp_client.send_raw(data)
    first = tcp_client.read_response()
    second = tcp_client.read_response()
    assert first["id"] == 1 and "protocol_version" in first["result"]
    assert second["id"] == 2 and "tempo" in second["result"]


def test_partial_reads(tcp_client):
    line = _line({"jsonrpc": "2.0", "id": 3, "method": "song.get_transport", "params": {}})
    for start in range(0, len(line), 7):
        tcp_client.send_raw(line[start:start + 7])
        time.sleep(0.001)
    response = tcp_client.read_response()
    assert response["id"] == 3
    assert response["result"]["tempo"] == 120.0


def test_response_order_matches_arrival(tcp_client):
    data = b"".join(_line({"jsonrpc": "2.0", "id": i, "method": "sys.ping"}) for i in range(1, 6))
    tcp_client.send_raw(data)
    ids = [tcp_client.read_response()["id"] for _ in range(5)]
    assert ids == [1, 2, 3, 4, 5]


def test_oversized_line_rejected_connection_stays_open(control_surface, make_tcp_client):
    control_surface.server.max_line_bytes = 1024
    client = make_tcp_client()
    big = b'{"jsonrpc":"2.0","id":1,"method":"sys.ping","params":{"pad":"' + b"x" * 2000 + b'"}}\n'
    client.send_raw(big)
    response = client.read_response()
    assert response["error"]["code"] == -32600
    assert response["id"] is None
    assert "too long" in response["error"]["message"].lower()
    follow_up = client.request("sys.ping")
    assert follow_up["result"]["protocol_version"] == 1


def test_real_4mib_limit(tcp_client):
    big = b'{"jsonrpc":"2.0","id":1,"method":"sys.ping","params":{"pad":"' + b"x" * (4 * 1024 * 1024) + b'"}}\n'
    tcp_client.send_raw(big)
    response = tcp_client.read_response(max_ticks=2000)
    assert response["error"]["code"] == -32600
    assert tcp_client.request("sys.ping")["result"]["protocol_version"] == 1


def test_parse_error(tcp_client):
    tcp_client.send_raw(b"{this is not json\n")
    response = tcp_client.read_response()
    assert response["error"]["code"] == -32700
    assert response["id"] is None
    assert tcp_client.request("sys.ping")["result"]["protocol_version"] == 1


def test_invalid_utf8_is_parse_error(tcp_client):
    tcp_client.send_raw(b'{"jsonrpc":"2.0","id":1,"method":"\xff\xfe"}\n')
    response = tcp_client.read_response()
    assert response["error"]["code"] == -32700


def test_missing_method_over_tcp(tcp_client):
    tcp_client.send({"jsonrpc": "2.0", "id": 5})
    response = tcp_client.read_response()
    assert response["error"]["code"] == -32600
    assert response["id"] == 5


def test_unknown_method_over_tcp(tcp_client):
    response = tcp_client.request("song.explode")
    assert response["error"]["code"] == -32601


def test_notification_ignored(tcp_client):
    tcp_client.send({"jsonrpc": "2.0", "method": "sys.ping"})
    tcp_client.send({"jsonrpc": "2.0", "method": "song.play"})  # also ignored: nothing executes
    response = tcp_client.request("sys.ping", request_id=9)
    assert response["id"] == 9
    assert tcp_client.request("song.get_transport")["result"]["is_playing"] is False


def test_blank_lines_ignored(tcp_client):
    tcp_client.send_raw(b"\n\r\n   \n")
    assert tcp_client.request("sys.ping")["result"]["protocol_version"] == 1


def test_server_binds_loopback_only(control_surface):
    server = control_surface.server
    assert server.host == "127.0.0.1"
    assert server._listener.getsockname()[0] == "127.0.0.1"
    assert server.port > 0


def test_multiple_connections_have_independent_ids(make_tcp_client):
    a = make_tcp_client()
    b = make_tcp_client()
    a.send({"jsonrpc": "2.0", "id": "same", "method": "sys.ping"})
    b.send({"jsonrpc": "2.0", "id": "same", "method": "song.get_transport"})
    ra = a.read_response()
    rb = b.read_response()
    assert ra["id"] == "same" and "protocol_version" in ra["result"]
    assert rb["id"] == "same" and "tempo" in rb["result"]


def test_abrupt_disconnect_tolerated(control_surface, harness, make_tcp_client):
    first = make_tcp_client()
    first.send_raw(b'{"jsonrpc":"2.0","id":1,"method":"sys.ping"')  # no newline, then vanish
    first.close()
    harness.tick(2)
    second = make_tcp_client()
    assert second.request("sys.ping")["result"]["protocol_version"] == 1
    assert harness.tick_until(lambda: control_surface.server.connection_count == 1, max_ticks=200, pause=0.01)


def test_disconnect_closes_server(control_surface, tcp_client):
    port = control_surface.server.port
    control_surface.disconnect()
    assert control_surface.server.running is False
    assert control_surface.server.connection_count == 0
    with pytest.raises(OSError):
        socket.create_connection(("127.0.0.1", port), timeout=0.5)
    assert control_surface.disconnected is True


# --------------------------------------------------------------------------
# Threading model
# --------------------------------------------------------------------------

def test_request_from_another_thread_gets_response(control_surface, harness):
    port = control_surface.server.port
    outcome = {}

    def worker():
        sock = socket.create_connection(("127.0.0.1", port), timeout=5.0)
        try:
            sock.sendall(_line({"jsonrpc": "2.0", "id": 42, "method": "song.get_overview"}))
            buffer = b""
            while b"\n" not in buffer:
                chunk = sock.recv(65536)
                if not chunk:
                    break
                buffer += chunk
            outcome["response"] = json.loads(buffer.split(b"\n")[0].decode("utf-8"))
        except Exception as exc:  # pragma: no cover - reported through the assertion below
            outcome["error"] = repr(exc)
        finally:
            sock.close()

    thread = threading.Thread(target=worker, name="client-thread")
    thread.start()
    harness.tick_until(lambda: not thread.is_alive(), max_ticks=1000, pause=0.005)
    thread.join(2.0)
    assert "error" not in outcome, outcome.get("error")
    response = outcome["response"]
    assert response["id"] == 42
    assert "tracks" in response["result"]
    assert _core.VIOLATIONS == []  # the LOM was only touched from the ticking (main) thread


def test_handler_off_main_thread_trips_guard(control_surface):
    outcome = {}

    def worker():
        try:
            song_handlers.get_transport(control_surface.ctx, {})
            outcome["result"] = "no error"
        except AssertionError as exc:
            outcome["error"] = str(exc)

    thread = threading.Thread(target=worker, name="rogue-thread")
    thread.start()
    thread.join(5.0)
    assert "LOM accessed off main thread" in outcome.get("error", "")
    assert _core.VIOLATIONS and _core.VIOLATIONS[0][1] == "rogue-thread"
    del _core.VIOLATIONS[:]


def test_socket_threads_never_touch_lom(control_surface, tcp_client):
    # The reader thread parses JSON only; nothing is dispatched until the tick.
    tcp_client.send({"jsonrpc": "2.0", "id": 1, "method": "song.get_overview"})
    deadline = time.time() + 0.5
    while control_surface.inbox.qsize() == 0 and time.time() < deadline:
        time.sleep(0.005)
    assert control_surface.inbox.qsize() == 1
    assert control_surface.dispatcher.handled == 0
    assert _core.VIOLATIONS == []
    response = tcp_client.read_response()
    assert response["id"] == 1
    assert control_surface.dispatcher.handled == 1


# --------------------------------------------------------------------------
# Tick budget
# --------------------------------------------------------------------------

class FakeConn(object):
    def __init__(self):
        self.lines = []

    def send_line(self, data):
        self.lines.append(data)
        return True


def test_tick_processes_at_most_max_requests(control_surface, harness):
    conn = FakeConn()
    for i in range(100):
        control_surface.inbox.put((conn, {"jsonrpc": "2.0", "id": i, "method": "sys.ping"}))
    harness.tick()
    assert len(conn.lines) == 32
    harness.tick()
    assert len(conn.lines) == 64
    harness.tick()
    assert len(conn.lines) == 96
    harness.tick()
    assert len(conn.lines) == 100
    harness.tick()
    assert len(conn.lines) == 100
    assert control_surface.tick_count == 5
    assert control_surface.requests_processed == 100
    ids = [json.loads(line.decode("utf-8"))["id"] for line in conn.lines]
    assert ids == list(range(100))


def test_tick_time_budget_stops_early(control_surface, harness):
    control_surface.settings["max_tick_ms"] = 0.0001  # effectively zero: one request per tick
    conn = FakeConn()
    for i in range(5):
        control_surface.inbox.put((conn, {"jsonrpc": "2.0", "id": i, "method": "sys.ping"}))
    harness.tick()
    assert len(conn.lines) == 1
    harness.tick()
    assert len(conn.lines) == 2


def test_tick_survives_dispatcher_crash(control_surface, harness, monkeypatch):
    conn = FakeConn()

    def explode(payload):
        raise ValueError("kaboom")

    monkeypatch.setattr(control_surface.dispatcher, "handle", explode)
    control_surface.inbox.put((conn, {"jsonrpc": "2.0", "id": 1, "method": "sys.ping"}))
    harness.tick()
    assert conn.lines == []
    monkeypatch.undo()
    control_surface.inbox.put((conn, {"jsonrpc": "2.0", "id": 2, "method": "sys.ping"}))
    harness.tick()  # the tick was rescheduled despite the crash
    assert len(conn.lines) == 1
    assert control_surface.tick_count == 2


def test_tick_reschedules_itself_every_tick(control_surface, harness):
    assert control_surface.scheduled_count == 1
    harness.tick(5)
    assert control_surface.tick_count == 5
    assert control_surface.scheduled_count == 1


def test_handler_assertion_does_not_kill_tick(control_surface, harness):
    conn = FakeConn()
    original = control_surface.dispatcher.methods["sys.ping"]

    def guard_trip(ctx, params):
        raise AssertionError("LOM accessed off main thread (simulated)")

    control_surface.dispatcher.methods["sys.ping"] = guard_trip
    try:
        control_surface.inbox.put((conn, {"jsonrpc": "2.0", "id": 1, "method": "sys.ping"}))
        harness.tick()
        assert conn.lines == []  # no response, but the tick keeps running
        harness.tick()
        assert control_surface.tick_count == 2
    finally:
        control_surface.dispatcher.methods["sys.ping"] = original
