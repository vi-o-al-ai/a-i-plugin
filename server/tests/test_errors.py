"""Error text format: "<NAME>: <message>. <hint>" plus compact data; and how it reaches Claude."""

from __future__ import annotations

from mcp.shared.memory import create_connected_server_and_client_session

from ableton_live_mcp.errors import LiveError, code_name, confirm_required, format_error, to_tool_error
from ableton_live_mcp.server import build_server


def test_code_names() -> None:
    assert code_name(-32700) == "PARSE_ERROR"
    assert code_name(-32600) == "INVALID_REQUEST"
    assert code_name(-32601) == "METHOD_NOT_FOUND"
    assert code_name(-32602) == "INVALID_PARAMS"
    assert code_name(-32603) == "INTERNAL_ERROR"
    assert code_name(-32000) == "NOT_FOUND"
    assert code_name(-32001) == "INVALID_STATE"
    assert code_name(-32002) == "CONFIRM_REQUIRED"
    assert code_name(-32003) == "UNSUPPORTED"
    assert code_name(-32004) == "LIVE_ERROR"
    assert code_name(-32005) == "TOO_LARGE"
    assert code_name(-32006) == "TIMEOUT"
    assert code_name("CONNECTION") == "CONNECTION"
    assert code_name(-1) == "ERROR_-1"


def test_format_not_found_with_hint_and_data() -> None:
    text = format_error(-32000, "Track 9 does not exist (set has 4 tracks)", {"kind": "track", "index": 9, "count": 4})
    assert text == (
        "NOT_FOUND: Track 9 does not exist (set has 4 tracks). Call get_session or get_track to refresh indices. "
        'Data: {"kind":"track","index":9,"count":4}'
    )


def test_format_hints() -> None:
    assert format_error(-32001, "Slot is empty.", {"reason": "slot_empty"}).startswith(
        "INVALID_STATE: Slot is empty. Check the object's state with get_clip/get_track."
    )
    assert format_error(-32002, "needs confirm") == "CONFIRM_REQUIRED: needs confirm. Ask the user, then call again with confirm=True."
    assert "Live is not running, or the ClaudeLive control surface is not selected" in format_error("CONNECTION", "refused")
    assert "modal dialog" in format_error("TIMEOUT", "no answer")
    assert "modal dialog" not in format_error(-32006, "budget exhausted")  # script-side budget, different hint
    assert format_error(-32602, "bad").startswith("INVALID_PARAMS: bad.")


def test_live_error_includes_detail() -> None:
    err = LiveError(-32004, "The LOM raised an exception", {"exception": "RuntimeError", "detail": "Clip is not a MIDI clip"})
    assert err.text.startswith("LIVE_ERROR: The LOM raised an exception. Live reported: Clip is not a MIDI clip.")
    assert err.text.endswith('Data: {"exception":"RuntimeError","detail":"Clip is not a MIDI clip"}')
    assert str(err) == err.text


def test_to_tool_error() -> None:
    tool_err = to_tool_error(LiveError(-32005, "Too many notes", {"limit": 1000, "got": 2400}))
    assert str(tool_err) == 'TOO_LARGE: Too many notes. Split the request into smaller batches. Data: {"limit":1000,"got":2400}'
    assert str(confirm_required("delete_track", "track 2")) == (
        "CONFIRM_REQUIRED: delete_track would delete track 2. Ask the user, then call again with confirm=True."
    )


async def test_not_found_reaches_claude(client, fake_script) -> None:
    res = await client.call_tool("get_track", {"track": 9})
    assert res.isError is True
    text = res.content[0].text
    assert "NOT_FOUND: Track 9 does not exist (set has 4 tracks). Call get_session or get_track to refresh indices." in text
    assert '{"kind":"track","index":9,"count":4}' in text


async def test_confirm_required_before_network(client, fake_script) -> None:
    for tool, args in (
        ("delete_track", {"track": 2}),
        ("delete_scene", {"scene": 1}),
        ("delete_clip", {"track": 2, "slot": 0}),
        ("delete_device", {"track": 2, "device_path": "0"}),
        ("delete_track", {"track": 2, "confirm": False}),
    ):
        res = await client.call_tool(tool, args)
        assert res.isError is True, tool
        text = res.content[0].text
        assert f"CONFIRM_REQUIRED: {tool} would delete" in text, text
        assert "Ask the user, then call again with confirm=True." in text
    assert fake_script.requests == []


async def test_confirm_true_is_forwarded(client, fake_script) -> None:
    res = await client.call_tool("delete_device", {"track": 2, "device_path": "1", "confirm": True})
    assert res.isError is False
    assert fake_script.calls == [("device.delete", {"track": 2, "path": "1", "confirm": True})]
    assert res.structuredContent == {"deleted": "Reverb"}


async def test_connection_refused_reaches_claude(closed_port_settings) -> None:
    server = build_server(closed_port_settings)
    async with create_connected_server_and_client_session(server) as session:
        res = await session.call_tool("get_transport", {})
        assert res.isError is True
        text = res.content[0].text
        assert "CONNECTION: Could not connect to Live at 127.0.0.1:" in text
        assert "Live is not running, or the ClaudeLive control surface is not selected (Preferences → Link, Tempo & MIDI → Control Surface)" in text


async def test_timeout_reaches_claude_and_reconnects(client, app, fake_script) -> None:
    app.client.timeout_overrides["song.get_transport"] = 0.1
    fake_script.delays["song.get_transport"] = 0.4
    res = await client.call_tool("get_transport", {})
    assert res.isError is True
    assert "TIMEOUT: No response from Live within 0.1 s for song.get_transport. Live is not responding. It may be showing a modal dialog" in res.content[0].text
    fake_script.delays.clear()
    res = await client.call_tool("get_transport", {})
    assert res.isError is False
    assert fake_script.connections == 2


async def test_unexpected_exception_is_internal_error(client, app, fake_script) -> None:
    async def boom(*args, **kwargs):
        raise RuntimeError("kaboom")

    app.client.call = boom  # type: ignore[method-assign]
    res = await client.call_tool("get_transport", {})
    assert res.isError is True
    assert "INTERNAL_ERROR: RuntimeError: kaboom." in res.content[0].text
