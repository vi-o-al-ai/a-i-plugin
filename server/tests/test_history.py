"""Action history: JSONL + Markdown content, resolved names, failures, reads, get_history."""

from __future__ import annotations

import json
import re
from pathlib import Path

from ableton_live_mcp.history import ActionHistory

MD_LINE = re.compile(r"^(\d{2}:\d{2}:\d{2})  (\S+)\s+(.*)$")


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def md_lines(path: Path) -> list[str]:
    return [line for line in path.read_text(encoding="utf-8").splitlines()[1:] if line.strip()]


def test_files_are_created_lazily(tmp_path: Path) -> None:
    history = ActionHistory(tmp_path / "history", pid=4242)
    assert not (tmp_path / "history").exists()
    assert history.jsonl_path.name.endswith("_4242.jsonl")
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}_\d{6}_4242\.jsonl", history.jsonl_path.name)
    assert history.md_path.with_suffix("") == history.jsonl_path.with_suffix("")
    history.record("get_transport", "R", {}, None, {"tempo": 120.0}, None, 3.0)
    assert history.jsonl_path.exists() and history.md_path.exists()
    first_line = history.md_path.read_text(encoding="utf-8").splitlines()[0]
    assert re.fullmatch(r"# ClaudeLive session \d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}", first_line)
    assert read_jsonl(history.jsonl_path)[0]["tool"] == "get_transport"  # no header line in JSONL
    assert md_lines(history.md_path) == []  # reads are absent from the Markdown


def test_jsonl_entry_shape(tmp_path: Path) -> None:
    history = ActionHistory(tmp_path, pid=1)
    result = {"parameter": {"name": "Filter Freq", "display": "1.20 kHz", "value": 0.62}, "previous": {"value": 0.5, "display": "800 Hz"}, "clamped": False}
    entry = history.record(
        "set_parameter", "M",
        {"track": 2, "device_path": "0", "parameter": "Filter Freq", "value": 0.62, "track_type": None, "why": "ignored"},
        "Open the filter so the bass cuts through the pad", result, None, 131.4,
    )
    assert entry is not None
    on_disk = read_jsonl(history.jsonl_path)[0]
    assert on_disk == entry
    assert re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\.\d{3}Z", entry["ts"])
    assert entry["seq"] == 1
    assert entry["tool"] == "set_parameter"
    assert entry["flags"] == ["M"]
    assert entry["params"] == {"track": 2, "device_path": "0", "parameter": "Filter Freq", "value": 0.62}
    assert entry["resolved"] == {"parameter_name": "Filter Freq"}
    assert entry["why"] == "Open the filter so the bass cuts through the pad"
    assert entry["result_summary"] == {"previous": "800 Hz", "value": "1.20 kHz"}
    assert entry["ok"] is True
    assert entry["duration_ms"] == 131
    line = md_lines(history.md_path)[0]
    m = MD_LINE.match(line)
    assert m, line
    assert m.group(2) == "set_parameter"
    assert line[10:30] == "set_parameter       "  # tool padded to 20
    assert m.group(3) == "track 2 › device 0 › Filter Freq : 800 Hz → 1.20 kHz   — Open the filter so the bass cuts through the pad"


def test_resolved_names_from_cache(tmp_path: Path) -> None:
    history = ActionHistory(tmp_path, pid=1)
    overview = {
        "tracks": [{"index": 2, "track_type": "track", "name": "Bass", "clips": [{"track": 2, "slot": 0, "name": "Bass 1"}],
                    "devices": [{"path": "0", "name": "Wavetable", "chains": [{"index": 0, "devices": [{"path": "0/0/0", "name": "Operator"}]}]}]}],
        "scenes": [{"index": 0, "name": "Intro"}],
    }
    history.record("get_session", "R", {}, None, overview, None, 50)
    result = {"parameter": {"name": "Filter Freq", "display": "1.20 kHz"}, "previous": {"display": "800 Hz"}, "clamped": True}
    entry = history.record("set_parameter", "M", {"track": 2, "device_path": "0", "parameter": "Filter Freq", "value": 0.62}, "why", result, None, 10)
    assert entry["resolved"] == {"track_name": "Bass", "device_name": "Wavetable", "parameter_name": "Filter Freq"}
    assert md_lines(history.md_path)[-1].endswith("Bass › Wavetable › Filter Freq : 800 Hz → 1.20 kHz (clamped)   — why")

    entry = history.record("set_parameter", "M", {"track": 2, "device_path": "0/0/0", "parameter": 3, "normalized": 0.5}, None, {"parameter": {"name": "Coarse", "display": "4"}, "previous": {"display": "1"}}, None, 10)
    assert entry["resolved"] == {"track_name": "Bass", "device_name": "Operator", "parameter_name": "Coarse"}
    assert md_lines(history.md_path)[-1].endswith("Bass › Operator › Coarse : 1 → 4")  # no why -> no dash

    entry = history.record("add_notes", "M", {"track": 2, "slot": 0, "notes": [{"pitch": 60, "start": 0, "duration": 1}]}, "riff", {"added": 1, "note_count": 17}, None, 5)
    assert entry["resolved"] == {"track_name": "Bass", "clip_name": "Bass 1"}
    assert "Bass › Bass 1 : +1 notes (17 total)   — riff" in md_lines(history.md_path)[-1]

    entry = history.record("fire_scene", "M", {"scene": 0}, None, {"index": 0, "name": "Intro"}, None, 5)
    assert entry["resolved"] == {"scene_name": "Intro"}
    assert md_lines(history.md_path)[-1].endswith("Intro : fired")


def test_names_from_results(tmp_path: Path) -> None:
    history = ActionHistory(tmp_path, pid=1)
    load = {"loaded": {"path": "2", "name": "Wavetable"}, "track": {"index": 2, "track_type": "track", "name": "Bass"}, "devices": [], "method": "load_item"}
    entry = history.record("load_device", "M", {"track": 2, "name": "wavetable"}, "need a synth", load, None, 400)
    assert entry["resolved"] == {"track_name": "Bass", "device_name": "Wavetable"}
    assert entry["result_summary"]["loaded"] == "Wavetable"
    assert md_lines(history.md_path)[-1].endswith("Bass › Wavetable : loaded Wavetable   — need a synth")

    entry = history.record("delete_track", "MD", {"track": 2, "confirm": True}, "cleanup", {"deleted": "Bass", "track_count": 3}, None, 20)
    assert entry["flags"] == ["M", "D"]
    assert entry["resolved"] == {"track_name": "Bass"}
    assert md_lines(history.md_path)[-1].endswith("Bass : deleted   — cleanup")

    entry = history.record("set_track", "M", {"track": 1, "volume": 0.7, "mute": True}, None, {"index": 1, "track_type": "track", "name": "Snare", "volume": {"value": 0.7, "display": "-6.0 dB"}}, None, 20)
    assert entry["resolved"] == {"track_name": "Snare"}
    assert md_lines(history.md_path)[-1].endswith("Snare : volume → -6.0 dB, mute → on")

    entry = history.record("create_midi_track", "M", {"index": -1, "name": "Lead"}, None, {"index": 4, "track_type": "track", "name": "Lead"}, None, 20)
    assert md_lines(history.md_path)[-1].endswith("Lead : created at index 4")

    entry = history.record("select", "UI", {"track": 1, "slot": 0}, None, {"track": {"index": 1, "name": "Snare"}, "scene": {"index": 0, "name": "Intro"}, "clip_slot": {"track": 1, "slot": 0, "clip_name": "Snare 1"}}, None, 2)
    assert entry["flags"] == ["UI"]
    assert md_lines(history.md_path)[-1].endswith("Snare › Snare 1 : selected")


def test_failure_recorded(tmp_path: Path) -> None:
    history = ActionHistory(tmp_path, pid=1)
    entry = history.record("delete_clip", "MD", {"track": 9, "slot": 0, "confirm": True}, "oops", None, "NOT_FOUND: Track 9 does not exist (set has 4 tracks). Call get_session or get_track to refresh indices.", 7)
    assert entry["ok"] is False
    assert entry["error"].startswith("NOT_FOUND: Track 9 does not exist")
    assert entry["result_summary"] is None
    assert md_lines(history.md_path)[-1].endswith("track 9 › slot 0 : FAILED: NOT_FOUND: Track 9 does not exist (set has 4 tracks). Call get_session or get_track to refresh indices.   — oops")


def test_history_never_raises(tmp_path: Path) -> None:
    blocker = tmp_path / "file"
    blocker.write_text("not a dir")
    history = ActionHistory(blocker / "history", pid=1)  # mkdir will fail
    assert history.record("play", "M", {}, None, {"is_playing": True}, None, 1) is None
    history.record("play", "M", {"weird": object()}, None, {"is_playing": True}, None, 1)  # must not raise either
    assert len(history.entries) == 2  # kept in memory even though the files could not be written
    assert history.get()["count"] == 2


def test_get_filters_reads_and_limits(tmp_path: Path) -> None:
    history = ActionHistory(tmp_path, pid=1)
    for i in range(5):
        history.record("get_transport", "R", {}, None, {"tempo": 120.0}, None, 1)
        history.record("play", "M", {}, f"why {i}", {"is_playing": True}, None, 1)
    out = history.get(limit=3)
    assert [e["why"] for e in out["entries"]] == ["why 2", "why 3", "why 4"]
    assert out["count"] == 5 and out["total"] == 10
    out = history.get(limit=50, include_reads=True)
    assert len(out["entries"]) == 10
    assert out["history_jsonl"] == str(history.jsonl_path)


async def test_history_through_tools(client, app, fake_script, home: Path) -> None:
    await client.call_tool("get_session", {})
    await client.call_tool("set_track", {"track": 2, "mute": True, "why": "mute the bass while we fix the kick"})
    await client.call_tool("set_parameter", {"track": 2, "device_path": "0", "parameter": "Filter Freq", "value": 0.62, "why": "open the filter"})
    await client.call_tool("get_track", {"track": 9})  # NOT_FOUND
    await client.call_tool("delete_scene", {"scene": 1})  # CONFIRM_REQUIRED, no network
    await client.call_tool("show_view", {"view": "Arranger"})
    await client.call_tool("get_history", {})

    history = app.history
    assert history.jsonl_path.parent == home / "history"
    entries = read_jsonl(history.jsonl_path)
    assert [e["tool"] for e in entries] == ["get_session", "set_track", "set_parameter", "get_track", "delete_scene", "show_view"]
    assert [e["seq"] for e in entries] == [1, 2, 3, 4, 5, 6]
    assert entries[0]["flags"] == ["R"] and entries[0]["ok"] is True
    assert entries[1]["why"] == "mute the bass while we fix the kick"
    assert entries[1]["resolved"]["track_name"] == "Bass"
    assert entries[2]["resolved"] == {"track_name": "Bass", "device_name": "Wavetable", "parameter_name": "Filter Freq"}
    assert entries[2]["result_summary"] == {"previous": "800 Hz", "value": "1.20 kHz"}
    assert entries[3]["ok"] is False and entries[3]["error"].startswith("NOT_FOUND: Track 9 does not exist")
    assert entries[4]["ok"] is False and entries[4]["error"].startswith("CONFIRM_REQUIRED")
    assert entries[4]["flags"] == ["M", "D"]
    assert entries[5]["flags"] == ["UI"]
    assert "why" not in entries[1]["params"]

    lines = md_lines(history.md_path)
    tools_in_md = [MD_LINE.match(line).group(2) for line in lines]
    assert tools_in_md == ["set_track", "set_parameter", "delete_scene", "show_view"]  # reads absent
    assert "Bass : mute → on   — mute the bass while we fix the kick" in lines[0]
    assert "Bass › Wavetable › Filter Freq : 800 Hz → 1.20 kHz   — open the filter" in lines[1]
    assert "Verse : FAILED: CONFIRM_REQUIRED" in lines[2]
    assert lines[3].endswith("Arranger : shown")

    res = await client.call_tool("get_history", {"limit": 2})
    got = res.structuredContent
    assert [e["tool"] for e in got["entries"]] == ["delete_scene", "show_view"]
    assert got["count"] == 4 and got["history_md"] == str(history.md_path)
    res = await client.call_tool("get_history", {"include_reads": True})
    assert [e["tool"] for e in res.structuredContent["entries"]] == ["get_session", "set_track", "set_parameter", "get_track", "delete_scene", "show_view"]
