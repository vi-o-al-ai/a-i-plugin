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
    # The client still gets an answer carrying its id instead of waiting for its timeout.
    assert len(conn.lines) == 1
    crashed = json.loads(conn.lines[0].decode("utf-8"))
    assert crashed["id"] == 1 and crashed["error"]["code"] == -32603
    assert crashed["error"]["data"]["exception"] == "ValueError"
    monkeypatch.undo()
    control_surface.inbox.put((conn, {"jsonrpc": "2.0", "id": 2, "method": "sys.ping"}))
    harness.tick()  # the tick was rescheduled despite the crash
    assert len(conn.lines) == 2
    assert json.loads(conn.lines[1].decode("utf-8"))["result"]["protocol_version"] == 1
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
        # An INTERNAL_ERROR response with the request id, and the tick keeps running.
        assert len(conn.lines) == 1
        response = json.loads(conn.lines[0].decode("utf-8"))
        assert response["id"] == 1 and response["error"]["code"] == -32603
        assert response["error"]["data"]["exception"] == "AssertionError"
        harness.tick()
        assert control_surface.tick_count == 2
    finally:
        control_surface.dispatcher.methods["sys.ping"] = original


# --------------------------------------------------------------------------
# Writer threads, bounded queue, connection cap, closed-connection drop
# --------------------------------------------------------------------------

def _wait_for(predicate, timeout=5.0, pause=0.005):
    deadline = time.time() + timeout
    while time.time() < deadline:
        if predicate():
            return True
        time.sleep(pause)
    return predicate()


class SlowSock(object):
    """Wraps a socket so that sendall() stalls, like a peer that stopped reading."""

    def __init__(self, sock, delay):
        self._sock = sock
        self.delay = delay
        self.sendall_calls = 0
        self.sendall_threads = []

    def sendall(self, data):
        self.sendall_calls += 1
        self.sendall_threads.append(threading.current_thread().name)
        time.sleep(self.delay)
        return self._sock.sendall(data)

    def __getattr__(self, name):
        return getattr(self._sock, name)


def _server_connection(control_surface):
    conns = control_surface.server.connections()
    assert len(conns) == 1
    return conns[0]


def test_stalled_client_does_not_block_tick(control_surface, harness, make_tcp_client):
    client = make_tcp_client()
    assert client.request("sys.ping")["result"]["protocol_version"] == 1
    conn = _server_connection(control_surface)
    slow = SlowSock(conn.sock, delay=0.3)
    conn.sock = slow
    for i in range(5):
        client.send({"jsonrpc": "2.0", "id": 100 + i, "method": "sys.ping"})
    assert _wait_for(lambda: control_surface.inbox.qsize() == 5)
    started = time.perf_counter()
    processed = control_surface.process_pending()
    elapsed = time.perf_counter() - started
    assert processed == 5
    assert elapsed < 0.25, "the tick blocked on the socket for %.3f s" % elapsed
    # The responses still arrive, written by the connection's writer thread.
    ids = [client.read_response(max_ticks=3000)["id"] for _ in range(5)]
    assert ids == [100, 101, 102, 103, 104]
    assert slow.sendall_calls == 5
    assert all(name.startswith("ClaudeLive-writer-") for name in slow.sendall_threads)
    assert threading.current_thread().name not in slow.sendall_threads


def test_send_line_only_enqueues(control_surface, make_tcp_client):
    client = make_tcp_client()
    client.request("sys.ping")
    conn = _server_connection(control_surface)
    assert conn.lines_sent == 1
    assert conn.outbox.qsize() == 0
    assert conn.send_line(b'{"jsonrpc":"2.0","id":9,"result":{"ok":true}}\n') is True
    assert _wait_for(lambda: conn.lines_sent == 2)
    assert client.read_response()["id"] == 9


def test_requests_from_closed_connections_are_dropped(control_surface, harness, fake_live, make_tcp_client):
    client = make_tcp_client()
    client.send({"jsonrpc": "2.0", "id": 1, "method": "song.create_midi_track", "params": {"name": "Ghost"}})
    assert _wait_for(lambda: control_surface.inbox.qsize() == 1)
    client.close()  # the client timed out and went away before Live got to its request
    assert _wait_for(lambda: control_surface.server.connection_count == 0)
    harness.tick()
    assert control_surface.dispatcher.handled == 0
    assert control_surface.requests_dropped == 1
    assert control_surface.inbox.qsize() == 0
    assert [t.name for t in fake_live.song.tracks] == ["Drums", "Bass", "Pad", "Vox", "Synths", "Lead"]
    # A fresh connection is served normally afterwards.
    second = make_tcp_client()
    assert second.request("sys.ping")["result"]["protocol_version"] == 1


def test_inbox_is_bounded_with_back_pressure(control_surface, harness, make_tcp_client):
    import queue as queue_module
    small = queue_module.Queue(maxsize=3)
    control_surface.inbox = small
    control_surface.server.inbox = small
    client = make_tcp_client()
    client.send_raw(b"".join(_line({"jsonrpc": "2.0", "id": i, "method": "sys.ping"}) for i in range(10)))
    assert _wait_for(lambda: small.qsize() == 3)
    time.sleep(0.2)  # the reader thread must wait, not drop or grow
    assert small.qsize() == 3 and small.full()
    assert control_surface.server.connection_count == 1
    ids = [client.read_response()["id"] for _ in range(10)]
    assert ids == list(range(10))
    assert small.qsize() == 0


def test_connection_cap_closes_extra_clients(control_surface, harness, make_tcp_client):
    control_surface.server.max_connections = 2
    first = make_tcp_client()
    second = make_tcp_client()
    assert first.request("sys.ping")["id"] == 1
    assert second.request("sys.ping")["id"] == 1
    assert control_surface.server.connection_count == 2
    third = make_tcp_client()
    third.send({"jsonrpc": "2.0", "id": 1, "method": "sys.ping"})
    assert third.read_line() is None  # closed right after accept: EOF, no response
    assert _wait_for(lambda: control_surface.server.connections_refused == 1)
    assert control_surface.server.connection_count == 2
    # The refusal is logged from the accept thread and surfaces on the next tick.
    harness.tick()
    assert any("max_connections" in line for line in control_surface.c_instance.logged)
    # The existing clients are unaffected, and a slot frees up when one leaves.
    assert first.request("sys.ping")["id"] == 2
    second.close()
    assert _wait_for(lambda: control_surface.server.connection_count == 1)
    fourth = make_tcp_client()
    assert fourth.request("sys.ping")["result"]["protocol_version"] == 1


def test_outbox_overflow_drops_the_client(control_surface, make_tcp_client):
    from ClaudeLive import server as server_module
    client = make_tcp_client()
    client.request("sys.ping")
    conn = _server_connection(control_surface)
    conn.sock = SlowSock(conn.sock, delay=5.0)  # the writer is stuck on the first line
    line = b'{"jsonrpc":"2.0","id":1,"result":{}}\n'
    accepted = 0
    for _ in range(server_module.OUTBOX_MAX + 2):
        if not conn.send_line(line):
            break
        accepted += 1
    # A full outbox (plus possibly the one line the writer already took) and then the drop.
    assert accepted in (server_module.OUTBOX_MAX, server_module.OUTBOX_MAX + 1)
    assert conn.closed is True
    assert conn.send_line(line) is False
    assert _wait_for(lambda: control_surface.server.connection_count == 0)


def test_connection_close_is_idempotent_and_joins_writer(control_surface, make_tcp_client):
    client = make_tcp_client()
    client.request("sys.ping")
    conn = _server_connection(control_surface)
    writer = conn._writer
    assert writer.is_alive() and writer.daemon
    started = time.perf_counter()
    conn.close()
    conn.close()
    assert time.perf_counter() - started < 1.0
    assert conn.closed is True
    writer.join(2.0)
    assert not writer.is_alive()
    assert conn.send_line(b"x\n") is False
    assert client.read_line() is None


def test_writer_failure_closes_connection_from_writer_thread(control_surface, make_tcp_client):
    client = make_tcp_client()
    client.request("sys.ping")
    conn = _server_connection(control_surface)

    class BrokenSock(object):
        def __init__(self, sock):
            self._sock = sock

        def sendall(self, data):
            raise OSError("broken pipe")

        def __getattr__(self, name):
            return getattr(self._sock, name)

    conn.sock = BrokenSock(conn.sock)
    assert conn.send_line(b'{"jsonrpc":"2.0","id":1,"result":{}}\n') is True
    assert _wait_for(lambda: conn.closed)
    assert _wait_for(lambda: control_surface.server.connection_count == 0)
    assert client.read_line() is None


def test_disconnect_with_live_connections_is_quick(control_surface, make_tcp_client):
    clients = [make_tcp_client() for _ in range(3)]
    for client in clients:
        client.request("sys.ping")
    assert control_surface.server.connection_count == 3
    started = time.perf_counter()
    control_surface.disconnect()
    assert time.perf_counter() - started < 3.0
    assert control_surface.server.connection_count == 0
    for client in clients:
        assert client.read_line() is None
