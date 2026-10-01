"""LiveClient: framing, ids, timeouts, reconnects, protocol errors."""

from __future__ import annotations

import json

import pytest

from ableton_live_mcp.client import LONG_TIMEOUT, MUTATION_TIMEOUT, READ_TIMEOUT, RETRY_ATTEMPTS, LiveClient, is_retryable, timeout_for
from ableton_live_mcp.errors import CONNECTION_HINT, TIMEOUT_HINT, LiveError

from .conftest import free_port


def test_timeout_table() -> None:
    assert timeout_for("track.get") == READ_TIMEOUT
    assert timeout_for("device.list") == READ_TIMEOUT
    assert timeout_for("sys.ping") == READ_TIMEOUT
    assert timeout_for("view.get_selection") == READ_TIMEOUT
    assert timeout_for("notes.add") == MUTATION_TIMEOUT
    assert timeout_for("song.delete_track") == MUTATION_TIMEOUT
    assert timeout_for("browser.search") == LONG_TIMEOUT
    assert timeout_for("browser.load") == LONG_TIMEOUT
    assert timeout_for("song.get_overview") == LONG_TIMEOUT
    assert timeout_for("sys.describe_api") == LONG_TIMEOUT
    assert timeout_for("track.get", {"track.get": 0.5}) == 0.5
    assert timeout_for("notes.add", {"notes.": 2.0}) == 2.0


async def test_call_round_trip(fake_script) -> None:
    client = LiveClient("127.0.0.1", fake_script.port)
    try:
        result = await client.call("song.get_transport", {})
        assert result["tempo"] == 124.0
        result = await client.call("notes.add", {"track": 2, "slot": 0, "notes": []})
        assert result == {"added": 0, "note_count": 16}
        assert [r["id"] for r in fake_script.requests] == [1, 2]
        assert fake_script.requests[1]["params"] == {"track": 2, "slot": 0, "notes": []}
        assert fake_script.connections == 1
        assert client.connected
    finally:
        await client.close()


async def test_ping_adds_round_trip(fake_script) -> None:
    client = LiveClient("127.0.0.1", fake_script.port)
    try:
        pong = await client.ping()
        assert pong["protocol_version"] == 1
        assert pong["script_version"] == "0.1.0"
        assert isinstance(pong["round_trip_ms"], float) and pong["round_trip_ms"] >= 0
    finally:
        await client.close()


async def test_connection_refused_wording() -> None:
    client = LiveClient("127.0.0.1", free_port())
    with pytest.raises(LiveError) as info:
        await client.call("sys.ping", {})
    err = info.value
    assert err.name == "CONNECTION"
    assert err.text.startswith("CONNECTION: Could not connect to Live at 127.0.0.1:")
    assert "Live is not running, or the ClaudeLive control surface is not selected" in err.text
    assert "Settings → Link, Tempo & MIDI → Control Surface (called Preferences in older Live versions)" in err.text
    assert CONNECTION_HINT in err.text
    assert not client.connected


async def test_protocol_error_from_script(fake_script) -> None:
    client = LiveClient("127.0.0.1", fake_script.port)
    try:
        with pytest.raises(LiveError) as info:
            await client.call("track.get", {"track": 9})
        err = info.value
        assert err.code == -32000 and err.name == "NOT_FOUND"
        assert err.message == "Track 9 does not exist (set has 4 tracks)"
        assert err.data == {"kind": "track", "index": 9, "count": 4}
        assert client.connected  # an application error keeps the connection
        with pytest.raises(LiveError) as info:
            await client.call("no.such_method", {})
        assert info.value.name == "METHOD_NOT_FOUND"
    finally:
        await client.close()


async def test_timeout_then_reconnect(fake_script) -> None:
    client = LiveClient("127.0.0.1", fake_script.port)
    try:
        fake_script.delays["track.get"] = 0.5
        with pytest.raises(LiveError) as info:
            await client.call("track.get", {"track": 2}, timeout=0.1)
        err = info.value
        assert err.name == "TIMEOUT"
        assert err.text.startswith("TIMEOUT: No response from Live within 0.1 s for track.get.")
        assert TIMEOUT_HINT in err.text
        assert not client.connected
        fake_script.delays.clear()
        result = await client.call("track.get", {"track": 2})
        assert result["name"] == "Bass"
        assert fake_script.connections == 2
    finally:
        await client.close()


async def test_dropped_connection_then_reconnect(fake_script) -> None:
    client = LiveClient("127.0.0.1", fake_script.port)
    try:
        await client.call("sys.ping", {})
        fake_script.drop_next = True
        with pytest.raises(LiveError) as info:
            await client.call("sys.ping", {})
        assert info.value.name == "CONNECTION"
        assert "closed the connection" in info.value.text or "lost" in info.value.text
        result = await client.call("sys.ping", {})
        assert result["protocol_version"] == 1
        assert fake_script.connections == 2
    finally:
        await client.close()


async def test_mismatched_id_is_protocol_error(fake_script) -> None:
    client = LiveClient("127.0.0.1", fake_script.port)
    try:
        fake_script.wrong_id_next = True
        with pytest.raises(LiveError) as info:
            await client.call("sys.ping", {})
        assert info.value.name == "PROTOCOL"
        assert "999999" in info.value.text  # raw line included
        assert not client.connected
        await client.call("sys.ping", {})
        assert fake_script.connections == 2
    finally:
        await client.close()


async def test_garbage_line_is_protocol_error(fake_script) -> None:
    client = LiveClient("127.0.0.1", fake_script.port)
    try:
        fake_script.garbage_next = True
        with pytest.raises(LiveError) as info:
            await client.call("sys.ping", {})
        assert info.value.name == "PROTOCOL"
        assert "this is not json" in info.value.text
        assert not client.connected
    finally:
        await client.close()


async def test_large_response_within_limit(fake_script) -> None:
    fake_script.handlers["sys.log"] = lambda p: {"blob": "x" * (2 * 1024 * 1024)}
    client = LiveClient("127.0.0.1", fake_script.port)
    try:
        result = await client.call("sys.log", {"message": "hi"})
        assert len(result["blob"]) == 2 * 1024 * 1024
    finally:
        await client.close()


async def test_wire_framing(fake_script) -> None:
    """Requests are compact single-line JSON (PROTOCOL.md section 1)."""
    seen: list[bytes] = []
    original = fake_script._handle_line

    async def spy(line: bytes, writer):
        seen.append(line)
        await original(line, writer)

    fake_script._handle_line = spy  # type: ignore[method-assign]
    client = LiveClient("127.0.0.1", fake_script.port)
    try:
        await client.call("clip.get", {"track": 2, "slot": 0})
    finally:
        await client.close()
    assert len(seen) == 1
    assert seen[0].endswith(b"\n") and seen[0].count(b"\n") == 1
    assert b": " not in seen[0] and b", " not in seen[0]
    assert json.loads(seen[0]) == {"jsonrpc": "2.0", "id": 1, "method": "clip.get", "params": {"track": 2, "slot": 0}}


def test_is_retryable() -> None:
    assert is_retryable(LiveError(-32006, "budget", {"retry": True, "nodes_visited": 5}))
    assert not is_retryable(LiveError(-32006, "budget", {"retry": False}))
    assert not is_retryable(LiveError(-32006, "budget", None))
    assert not is_retryable(LiveError(-32000, "missing", {"retry": True}))
    assert not is_retryable(LiveError("TIMEOUT", "local timeout", {"retry": True}))


async def test_call_retrying_succeeds_on_third_attempt(fake_script) -> None:
    client = LiveClient("127.0.0.1", fake_script.port)
    client.retry_delay = 0.0
    fake_script.retry_timeouts["browser.load"] = 2
    try:
        result = await client.call_retrying("browser.load", {"uri": "query:AudioFx#Reverb", "track": 2})
        assert result["loaded"]["name"] == "Reverb"
        assert [r["method"] for r in fake_script.requests] == ["browser.load"] * 3
        assert len({json.dumps(r["params"], sort_keys=True) for r in fake_script.requests}) == 1  # the same call
        assert fake_script.connections == 1  # an application error keeps the connection
    finally:
        await client.close()


async def test_call_retrying_gives_up_after_ten_attempts(fake_script) -> None:
    assert RETRY_ATTEMPTS == 10
    client = LiveClient("127.0.0.1", fake_script.port)
    client.retry_delay = 0.0
    fake_script.retry_timeouts["browser.list"] = 50
    try:
        with pytest.raises(LiveError) as info:
            await client.call_retrying("browser.list", {"uri": "query:Synths"})
        assert info.value.code == -32006 and info.value.data == {"retry": True, "nodes_visited": 1234}
        assert "still indexing the browser" in info.value.text
        assert len(fake_script.requests_for("browser.list")) == 10
        assert fake_script.retry_timeouts["browser.list"] == 40
    finally:
        await client.close()


async def test_call_retrying_does_not_retry_other_errors(fake_script) -> None:
    client = LiveClient("127.0.0.1", fake_script.port)
    client.retry_delay = 0.0
    fake_script.errors["browser.list"] = (-32006, "no retry flag", {"retry": False})
    try:
        with pytest.raises(LiveError):
            await client.call_retrying("browser.list", {"uri": "x"})
        assert len(fake_script.requests) == 1
        fake_script.errors.clear()
        with pytest.raises(LiveError) as info:
            await client.call_retrying("track.get", {"track": 9})
        assert info.value.name == "NOT_FOUND"
        assert len(fake_script.requests) == 2
    finally:
        await client.close()
