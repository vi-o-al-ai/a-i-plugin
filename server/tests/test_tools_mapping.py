"""Contract check: every tool in TOOLS.md exists, and each maps to the documented protocol method and params."""

from __future__ import annotations

import json
from typing import Any

import pytest
from mcp.types import Tool

NOTE = {"pitch": 60, "start": 0.0, "duration": 0.5, "velocity": 100}

# (tool, arguments, [(expected protocol method, expected params), ...]); 55 entries = TOOLS.md.
CASES: list[tuple[str, dict[str, Any], list[tuple[str, dict[str, Any]]]]] = [
    # status and diagnostics
    ("ableton_status", {}, [("sys.ping", {})]),
    ("ableton_describe_api", {"path": "/tmp/dump.md"}, [("sys.describe_api", {"path": "/tmp/dump.md"})]),
    ("get_history", {}, []),
    # session and transport
    ("get_session", {}, [("song.get_overview", {"include_clips": True, "include_devices": True, "include_params": False, "include_returns": True})]),
    ("get_transport", {}, [("song.get_transport", {})]),
    ("set_transport", {"tempo": 124.0, "metronome": True, "why": "w"}, [("song.set_transport", {"tempo": 124.0, "metronome": True})]),
    ("play", {"from_start": True}, [("song.play", {"from_start": True})]),
    ("stop", {}, [("song.stop", {})]),
    ("continue_playing", {}, [("song.continue", {})]),
    ("set_scale", {"root_note": "D", "scale_name": "Dorian"}, [("song.set_scale", {"root_note": "D", "scale_name": "Dorian"})]),
    ("undo", {"steps": 2}, [("song.undo", {}), ("song.undo", {})]),
    ("redo", {}, [("song.redo", {})]),
    # tracks
    ("get_track", {"track": 2}, [("track.get", {"track": 2, "include_clips": True, "include_devices": True, "include_params": False})]),
    ("create_midi_track", {"name": "Lead"}, [("song.create_midi_track", {"index": -1, "name": "Lead"})]),
    ("create_audio_track", {}, [("song.create_audio_track", {"index": -1})]),
    ("create_return_track", {"name": "Delay"}, [("song.create_return_track", {"name": "Delay"})]),
    ("set_track", {"track": 2, "volume": 0.7, "mute": True, "sends": [{"index": 0, "value": 0.3}]},
     [("track.set", {"track": 2, "volume": 0.7, "mute": True, "sends": [{"index": 0, "value": 0.3}]})]),
    ("delete_track", {"track": 2, "confirm": True}, [("song.delete_track", {"track": 2, "confirm": True})]),
    # scenes
    ("create_scene", {"name": "Drop", "index": 3}, [("song.create_scene", {"index": 3, "name": "Drop"})]),
    ("set_scene", {"scene": 1, "name": "Verse 2"}, [("scene.set", {"scene": 1, "name": "Verse 2"})]),
    ("fire_scene", {"scene": 1}, [("scene.fire", {"scene": 1})]),
    ("duplicate_scene", {"scene": 1}, [("song.duplicate_scene", {"scene": 1})]),
    ("delete_scene", {"scene": 1, "confirm": True}, [("song.delete_scene", {"scene": 1, "confirm": True})]),
    # clips
    ("create_clip", {"track": 2, "slot": 0}, [("clip.create", {"track": 2, "slot": 0, "length": 4.0})]),
    ("get_clip", {"track": 2, "slot": 0}, [("clip.get", {"track": 2, "slot": 0})]),
    ("set_clip", {"track": 2, "arrangement_index": 1, "name": "X", "looping": False},
     [("clip.set", {"track": 2, "arrangement_index": 1, "name": "X", "looping": False})]),
    ("fire_clip", {"track": 2, "slot": 0}, [("clip.fire", {"track": 2, "slot": 0})]),
    ("stop_clip", {"track": 2}, [("clip.stop", {"track": 2})]),
    ("duplicate_clip", {"track": 2, "slot": 0, "target_slot": 1}, [("clip.duplicate", {"track": 2, "slot": 0, "target_slot": 1})]),
    ("duplicate_clip_loop", {"track": 2, "slot": 0}, [("clip.duplicate_loop", {"track": 2, "slot": 0})]),
    ("delete_clip", {"track": 2, "slot": 0, "confirm": True}, [("clip.delete", {"track": 2, "slot": 0, "confirm": True})]),
    # notes
    ("get_notes", {"track": 2, "slot": 0, "from_time": 0.0, "time_span": 4.0},
     [("notes.get", {"track": 2, "slot": 0, "from_time": 0.0, "time_span": 4.0})]),
    ("add_notes", {"track": 2, "slot": 0, "notes": [NOTE]}, [("notes.add", {"track": 2, "slot": 0, "notes": [NOTE]})]),
    ("replace_notes", {"track": 2, "slot": 0, "notes": [NOTE]}, [("notes.replace", {"track": 2, "slot": 0, "notes": [NOTE]})]),
    ("remove_notes", {"track": 2, "slot": 0, "note_ids": [1, 2]}, [("notes.remove", {"track": 2, "slot": 0, "note_ids": [1, 2]})]),
    ("modify_notes", {"track": 2, "slot": 0, "changes": [{"id": 1, "velocity": 90}]},
     [("notes.modify", {"track": 2, "slot": 0, "changes": [{"id": 1, "velocity": 90}]})]),
    ("quantize_notes", {"track": 2, "slot": 0}, [("notes.quantize", {"track": 2, "slot": 0, "grid": 0.25, "amount": 1.0, "swing": 0.0})]),
    ("transpose_notes", {"track": 2, "slot": 0, "semitones": -12}, [("notes.transpose", {"track": 2, "slot": 0, "semitones": -12})]),
    # devices and parameters
    ("get_devices", {"track": 2}, [("device.list", {"track": 2, "include_params": False, "depth": 2})]),
    ("set_parameter", {"track": 2, "device_path": "0", "parameter": "Filter Freq", "value": 0.62},
     [("device.set_parameter", {"track": 2, "path": "0", "parameter": "Filter Freq", "value": 0.62})]),
    ("set_parameters", {"track": 2, "device_path": "0", "values": [{"parameter": "Filter Freq", "normalized": 0.5}]},
     [("device.set_parameters", {"track": 2, "path": "0", "values": [{"parameter": "Filter Freq", "normalized": 0.5}]})]),
    ("set_device_enabled", {"track": 2, "device_path": "0", "enabled": False}, [("device.set_enabled", {"track": 2, "path": "0", "enabled": False})]),
    ("delete_device", {"track": 2, "device_path": "1", "confirm": True}, [("device.delete", {"track": 2, "path": "1", "confirm": True})]),
    # browser
    ("browse", {"query": "wavetable"}, [("browser.search", {"query": "wavetable", "limit": 25, "loadable_only": True})]),
    ("load_device", {"track": 2, "uri": "query:Synths#Wavetable"}, [("browser.load", {"uri": "query:Synths#Wavetable", "track": 2})]),
    # arrangement
    ("get_arrangement", {}, [("arrangement.get_overview", {"include_clips": True})]),
    ("add_clip_to_arrangement", {"track": 2, "slot": 0, "time": 16.0},
     [("arrangement.add_clip_from_slot", {"track": 2, "slot": 0, "time": 16.0, "delete_source": False})]),
    ("set_locator", {"time": 64.0, "name": "Drop"}, [("arrangement.set_locator", {"time": 64.0, "name": "Drop"})]),
    ("delete_locator", {"index": 0}, [("arrangement.delete_locator", {"index": 0})]),
    # automation
    ("get_automation", {"track": 2, "slot": 0, "device_path": "0", "parameter": "Filter Freq"},
     [("automation.get", {"track": 2, "slot": 0, "device_path": "0", "parameter": "Filter Freq", "resolution": 0.25})]),
    ("set_automation", {"track": 2, "slot": 0, "device_path": "mixer", "parameter": "Volume", "points": [{"time": 0.0, "value": 0.5}]},
     [("automation.set", {"track": 2, "slot": 0, "device_path": "mixer", "parameter": "Volume", "points": [{"time": 0.0, "value": 0.5}], "mode": "ramp", "resolution": 0.0625})]),
    ("clear_automation", {"track": 2, "slot": 0, "device_path": "0", "parameter": "Filter Freq"},
     [("automation.clear", {"track": 2, "slot": 0, "device_path": "0", "parameter": "Filter Freq"})]),
    # view
    ("get_selection", {}, [("view.get_selection", {})]),
    ("select", {"track": 2, "slot": 0, "show_clip_detail": True}, [("view.select", {"track": 2, "slot": 0, "show_clip_detail": True})]),
    ("show_view", {"view": "Arranger"}, [("view.show_view", {"view": "Arranger"})]),
]

# The 55 names from TOOLS.md, by section.
SPEC_TOOL_NAMES = {
    "ableton_status", "ableton_describe_api", "get_history",
    "get_session", "get_transport", "set_transport", "play", "stop", "continue_playing", "set_scale", "undo", "redo",
    "get_track", "create_midi_track", "create_audio_track", "create_return_track", "set_track", "delete_track",
    "create_scene", "set_scene", "fire_scene", "duplicate_scene", "delete_scene",
    "create_clip", "get_clip", "set_clip", "fire_clip", "stop_clip", "duplicate_clip", "duplicate_clip_loop", "delete_clip",
    "get_notes", "add_notes", "replace_notes", "remove_notes", "modify_notes", "quantize_notes", "transpose_notes",
    "get_devices", "set_parameter", "set_parameters", "set_device_enabled", "delete_device",
    "browse", "load_device",
    "get_arrangement", "add_clip_to_arrangement", "set_locator", "delete_locator",
    "get_automation", "set_automation", "clear_automation",
    "get_selection", "select", "show_view",
}
READ_TOOLS = {n for n in SPEC_TOOL_NAMES if n.startswith("get_") or n in {"ableton_status", "ableton_describe_api", "browse"}}
DESTRUCTIVE_TOOLS = {"delete_track", "delete_scene", "delete_clip", "delete_device", "clear_automation"}


def test_spec_has_55_tools() -> None:
    assert len(SPEC_TOOL_NAMES) == 55
    assert {c[0] for c in CASES} == SPEC_TOOL_NAMES
    assert len(CASES) == 55


async def test_tool_list_matches_spec(client) -> None:
    tools: list[Tool] = (await client.list_tools()).tools
    names = {t.name for t in tools}
    missing = SPEC_TOOL_NAMES - names
    extra = names - SPEC_TOOL_NAMES
    assert not missing and not extra, f"missing={sorted(missing)} extra={sorted(extra)}"
    assert len(tools) == 55


async def test_tool_metadata(client) -> None:
    for tool in (await client.list_tools()).tools:
        assert tool.title, tool.name
        assert tool.description and tool.description.count(". ") <= 3, f"{tool.name}: description too long"
        assert tool.outputSchema is not None, f"{tool.name} has no outputSchema (return type must be dict[str, Any])"
        ann = tool.annotations
        assert ann is not None, tool.name
        assert ann.openWorldHint is False, tool.name
        if tool.name in READ_TOOLS:
            assert ann.readOnlyHint is True, tool.name
            assert ann.destructiveHint is False, tool.name
        else:
            assert ann.readOnlyHint is False, tool.name
            assert ann.idempotentHint is False, tool.name
            assert ann.destructiveHint is (tool.name in DESTRUCTIVE_TOOLS), tool.name
        props = tool.inputSchema.get("properties", {})
        if tool.name not in READ_TOOLS and tool.name not in {"undo", "redo", "get_history"}:
            assert "why" in props, f"{tool.name} must accept why"
        if tool.name in DESTRUCTIVE_TOOLS:
            assert "confirm" in props, tool.name


@pytest.mark.parametrize(("tool", "args", "expected"), CASES, ids=[c[0] for c in CASES])
async def test_tool_maps_to_protocol(client, fake_script, tool: str, args: dict[str, Any], expected) -> None:
    result = await client.call_tool(tool, args)
    assert result.isError is False, result.content[0].text if result.content else result
    assert isinstance(result.structuredContent, dict), f"{tool}: no structuredContent"
    assert result.content and result.content[0].type == "text"
    assert json.loads(result.content[0].text) == result.structuredContent
    assert fake_script.calls == expected
    for req in fake_script.requests:
        assert req["jsonrpc"] == "2.0"
        assert isinstance(req["id"], int)
        assert "why" not in req["params"]


async def test_request_ids_increment(client, fake_script) -> None:
    await client.call_tool("get_transport", {})
    await client.call_tool("get_transport", {})
    await client.call_tool("undo", {"steps": 3})
    ids = [r["id"] for r in fake_script.requests]
    assert ids == list(range(ids[0], ids[0] + 5))
    assert fake_script.connections == 1  # one persistent connection


async def test_get_devices_with_path_uses_device_get(client, fake_script) -> None:
    result = await client.call_tool("get_devices", {"track": 2, "device_path": "0"})
    assert result.isError is False
    assert fake_script.calls == [("device.get", {"track": 2, "path": "0", "include_params": True})]
    assert result.structuredContent["name"] == "Wavetable"


async def test_clip_address_requires_exactly_one(client, fake_script) -> None:
    both = await client.call_tool("get_clip", {"track": 2, "slot": 0, "arrangement_index": 1})
    neither = await client.call_tool("get_clip", {"track": 2})
    for res in (both, neither):
        assert res.isError is True
        assert "INVALID_PARAMS:" in res.content[0].text
    assert fake_script.requests == []


async def test_undo_steps_validated(client, fake_script) -> None:
    res = await client.call_tool("undo", {"steps": 21})
    assert res.isError is True and "INVALID_PARAMS" in res.content[0].text
    assert fake_script.requests == []
    res = await client.call_tool("redo", {"steps": 2})
    assert res.structuredContent == {"ok": True, "steps": 2}


async def test_clear_automation_all_requires_confirm(client, fake_script) -> None:
    res = await client.call_tool("clear_automation", {"track": 2, "slot": 0})
    assert res.isError is True
    assert "CONFIRM_REQUIRED: clear_automation would delete every automation envelope" in res.content[0].text
    assert fake_script.requests == []
    res = await client.call_tool("clear_automation", {"track": 2, "slot": 0, "confirm": True})
    assert res.isError is False
    assert fake_script.calls == [("automation.clear", {"track": 2, "slot": 0, "confirm": True})]
    assert res.structuredContent == {"cleared": "all"}


async def test_set_parameter_requires_exactly_one_value(client, fake_script) -> None:
    res = await client.call_tool("set_parameter", {"track": 2, "device_path": "0", "parameter": 5})
    assert res.isError is True and "exactly one of value, normalized or display" in res.content[0].text
    res = await client.call_tool("set_parameter", {"track": 2, "device_path": "0", "parameter": 5, "value": 0.1, "display": "x"})
    assert res.isError is True
    assert fake_script.requests == []


async def test_track_type_passthrough(client, fake_script) -> None:
    res = await client.call_tool("set_track", {"track": 0, "track_type": "return", "volume": 0.5})
    assert res.isError is False
    assert fake_script.calls == [("track.set", {"track": 0, "track_type": "return", "volume": 0.5})]
