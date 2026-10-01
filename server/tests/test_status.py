"""ableton_status never raises and reports what to do."""

from __future__ import annotations

from mcp.shared.memory import create_connected_server_and_client_session

from ableton_live_mcp.server import build_server
from ableton_live_mcp.tools.common import AppContext


async def test_status_connected(client, fake_script, settings) -> None:
    res = await client.call_tool("ableton_status", {})
    assert res.isError is False
    s = res.structuredContent
    assert s["connected"] is True
    assert s["script_version"] == "0.1.0"
    assert s["protocol_version"] == 1
    assert s["live_version"] == "12.1.5"
    assert s["python_version"] == "3.11.4"
    assert isinstance(s["round_trip_ms"], float)
    assert s["host"] == "127.0.0.1" and s["port"] == fake_script.port
    assert s["home"] == str(settings.home)
    assert s["history_jsonl"].endswith(".jsonl") and s["history_md"].endswith(".md")
    assert "warning" not in s
    assert fake_script.calls == [("sys.ping", {})]


async def test_status_warns_on_protocol_mismatch(client, fake_script) -> None:
    fake_script.ping_result["protocol_version"] = 2
    res = await client.call_tool("ableton_status", {})
    s = res.structuredContent
    assert s["connected"] is True
    assert "Protocol version mismatch" in s["warning"]


async def test_status_disconnected(closed_port_settings) -> None:
    app = AppContext(closed_port_settings)
    server = build_server(closed_port_settings, app=app)
    async with create_connected_server_and_client_session(server) as session:
        res = await session.call_tool("ableton_status", {})
    assert res.isError is False  # never raises
    s = res.structuredContent
    assert s["connected"] is False
    assert s["error"].startswith("CONNECTION: Could not connect to Live at 127.0.0.1:")
    assert s["error_code"] == "CONNECTION"
    assert isinstance(s["diagnosis"], list) and len(s["diagnosis"]) >= 3
    assert "running" in s["diagnosis"][0]
    assert "Control Surface" in s["diagnosis"][1]
    assert str(closed_port_settings.port) in s["diagnosis"][2]
    assert s["history_jsonl"].endswith(".jsonl")
    # the failed status check is itself recorded
    assert app.history.entries[-1]["tool"] == "ableton_status" and app.history.entries[-1]["ok"] is True


async def test_status_timeout_diagnosis(client, app, fake_script) -> None:
    app.client.timeout_overrides["sys.ping"] = 0.1
    fake_script.delays["sys.ping"] = 0.4
    res = await client.call_tool("ableton_status", {})
    s = res.structuredContent
    assert s["connected"] is False
    assert s["error_code"] == "TIMEOUT"
    assert "modal dialog" in s["diagnosis"][0]
