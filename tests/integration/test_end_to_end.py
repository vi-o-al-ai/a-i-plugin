"""End to end: MCP client -> real ableton-live-mcp subprocess -> TCP -> real ClaudeLive
Remote Script -> mock Live, with the thread guard proving every LOM touch happens on the
"Live main thread".

The module shares one Live set, one Remote Script and one server process (module-scoped
fixtures), so the tests run in file order: the production sequence first, the history
check that reads its trail next, then the per-tool smoke run and the negative cases.
"""
import json
import re
from pathlib import Path

import pytest

pytest.importorskip("mcp")

from Live import _core  # noqa: E402  (sys.path is prepared by conftest)
from factory import SCENE_NAMES  # noqa: E402

FACTORY_TRACKS = ["Drums", "Bass", "Pad", "Vox", "Synths", "Lead"]
NEW_TRACK_INDEX = len(FACTORY_TRACKS)  # the track the production sequence creates
VOX = 3  # audio track with "Vox Take 1" in slot 0

# Anything in an error text that means the two halves disagree on the contract.
CONTRACT_MISMATCH = re.compile(
    r"METHOD_NOT_FOUND|INVALID_PARAMS|INTERNAL_ERROR|-3260[123](?!\d)|Traceback \(most recent call last\)"
)

READ_TOOLS = {
    "ableton_status", "get_history", "get_session", "get_transport", "get_track",
    "get_clip", "get_notes", "get_devices", "browse", "get_arrangement", "get_automation", "get_selection",
}

WHY_TRACK = "Add a second lead for the drop"
WHY_NOTES = "Lay down the hook rhythm"
WHY_FILTER = "Open the filter so the lead cuts through"


def drum_grid():
    """14 notes: kicks, snares, closed hats, and four off-grid ghost hats to quantize."""
    notes = [{"pitch": 36, "start": float(beat), "duration": 0.25, "velocity": 110} for beat in range(4)]
    notes += [{"pitch": 38, "start": 1.0, "duration": 0.25, "velocity": 100},
              {"pitch": 38, "start": 3.0, "duration": 0.25, "velocity": 100}]
    notes += [{"pitch": 42, "start": beat + 0.5, "duration": 0.25, "velocity": 80} for beat in range(4)]
    notes += [{"pitch": 42, "start": start, "duration": 0.125, "velocity": 60} for start in (0.27, 1.74, 2.23, 3.76)]
    assert len(notes) == 14
    return notes


OFF_GRID_COUNT = 4


def by_id(notes_result):
    return {n["id"]: n for n in notes_result["notes"]}


# --------------------------------------------------------------------------
# 0. harness sanity
# --------------------------------------------------------------------------

def test_thread_guard_is_armed(remote_script, live_set):
    """The tick thread is the mock's main thread; the pytest thread may not touch the LOM."""
    assert _core.MAIN_THREAD is remote_script.thread
    assert remote_script.thread.is_alive()
    with pytest.raises(AssertionError, match="off main thread"):
        live_set.song.tempo  # noqa: B018 - deliberate off-thread read
    assert _core.VIOLATIONS[-1][0] == "tempo"
    _core.VIOLATIONS.pop()  # the fixture teardown asserts nothing else was recorded


# --------------------------------------------------------------------------
# 1. status
# --------------------------------------------------------------------------

def test_status(mcp_session):
    status = mcp_session.ok("ableton_status")
    assert status["connected"] is True
    assert status["script_version"] and status["protocol_version"] == 1
    assert status["live_version"] == "12.1.5"
    assert isinstance(status["python_version"], str)
    assert isinstance(status["round_trip_ms"], (int, float)) and status["round_trip_ms"] >= 0
    assert status["port"] == mcp_session.port
    assert status["history_jsonl"].startswith(str(mcp_session.home))
    assert "warning" not in status and "config_warnings" not in status


def test_tool_schemas_follow_the_contract(mcp_session):
    tools = {tool.name: tool for tool in mcp_session.list_tools()}

    def props(name):
        return set(tools[name].inputSchema.get("properties", {}))

    assert not props("set_transport") & {"record_mode", "session_record"}  # TOOLS.md: not exposed
    assert props("ableton_describe_api") == set()  # the script chooses the path
    assert tools["ableton_describe_api"].annotations.readOnlyHint is False
    assert "confirm" in props("remove_notes") and "confirm" in props("add_clip_to_arrangement")
    assert "clear_tempo" in props("set_scene") and "track_type" in props("delete_track")
    for name in ("get_session", "get_track", "get_arrangement"):
        assert "include_note_counts" in props(name), name
    for name in ("replace_notes", "remove_notes", "delete_locator", "clear_automation", "delete_track"):
        assert tools[name].annotations.destructiveHint is True, name
    for name in READ_TOOLS:
        assert tools[name].annotations.readOnlyHint is True, name


def test_describe_api_writes_under_the_script_home(mcp_session, remote_script):
    res = mcp_session.ok("ableton_describe_api")
    path = Path(res["path"])
    assert path.suffix == ".md" and path.is_file(), res
    assert res["classes"] > 0 and res["bytes"] > 0 and path.stat().st_size > 0
    api_dir = (remote_script.home / ".claude-live" / "api").resolve()
    assert path.resolve().parent == api_dir, (path, api_dir)
    assert path.read_text(encoding="utf-8").lstrip().startswith("#")


# --------------------------------------------------------------------------
# 2. session overview
# --------------------------------------------------------------------------

def test_session_overview(mcp_session):
    session = mcp_session.ok("get_session")
    assert [t["name"] for t in session["tracks"]] == FACTORY_TRACKS
    assert [t["type"] for t in session["tracks"]] == ["midi", "midi", "midi", "audio", "group", "midi"]
    assert len(session["scenes"]) == len(SCENE_NAMES)
    assert [s["name"] for s in session["scenes"]] == list(SCENE_NAMES)
    assert [r["name"] for r in session["return_tracks"]] == ["A-Reverb", "B-Delay"]
    assert session["master"]["type"] == "master"
    assert session["selection"]["track"]["name"] == "Bass"
    assert session["selection"]["scene"]["index"] == 0
    assert isinstance(session["live_version"], str) and session["live_version"]
    assert session["transport"]["tempo"] == 120.0
    assert session["scale"]["scale_name"] == "Major"
    drums = session["tracks"][0]
    assert [c["name"] for c in drums["clips"]] == ["Drums 1", "Drums 2"]
    assert [d["name"] for d in drums["devices"]] == ["Drum Rack", "Compressor"]
    assert drums["devices"][0]["is_rack"] and drums["devices"][0]["chains"][0]["name"] == "Kick 909"


# --------------------------------------------------------------------------
# 3. a realistic production sequence
# --------------------------------------------------------------------------

def test_production_sequence(mcp_session):
    s = mcp_session
    t = NEW_TRACK_INDEX

    # -- a new MIDI track -----------------------------------------------------------
    track = s.ok("create_midi_track", name="Lead 2", why=WHY_TRACK)
    assert track["index"] == t and track["name"] == "Lead 2" and track["type"] == "midi"
    got = s.ok("get_track", track=t)
    assert got["name"] == "Lead 2" and got["clips"] == [] and got["devices"] == []

    # -- load an instrument by name -------------------------------------------------
    loaded = s.ok("load_device", name="Wavetable", track=t, why="The lead needs a wavetable synth")
    assert loaded["matched"]["name"] == "Wavetable" and loaded["matched"]["uri"]
    assert loaded["loaded"] is not None
    assert loaded["loaded"]["name"] == "Wavetable" and loaded["loaded"]["path"] == "0"
    assert loaded["track"]["index"] == t and loaded["method"] == "load_item"
    devices = s.ok("get_devices", track=t)
    assert [d["name"] for d in devices["devices"]] == ["Wavetable"]
    assert [p["name"] for p in devices["mixer"]["parameters"]][:2] == ["Volume", "Pan"]
    detail = s.ok("get_devices", track=t, device_path="0")
    assert detail["name"] == "Wavetable" and detail["parameters"]
    param = next(p for p in detail["parameters"] if "Freq" in p["name"] and not p["is_quantized"])
    param_name, pmin, pmax = param["name"], param["min"], param["max"]

    # -- a clip with notes ----------------------------------------------------------
    clip = s.ok("create_clip", track=t, slot=0, length=4.0, name="Hook", why="Four-beat hook")
    assert clip["track"] == t and clip["slot"] == 0 and clip["name"] == "Hook"
    assert clip["length"] == 4.0 and clip["note_count"] == 0 and clip["is_midi"] is True

    added = s.ok("add_notes", track=t, slot=0, notes=drum_grid(), why=WHY_NOTES)
    assert added["added"] == 14 and added["note_count"] == 14
    notes = s.ok("get_notes", track=t, slot=0)
    assert notes["count"] == 14 and len(notes["notes"]) == 14 and notes["clip_length"] == 4.0
    ids = [n["id"] for n in notes["notes"]]
    assert all(isinstance(i, int) for i in ids) and len(set(ids)) == 14
    assert notes["notes"] == sorted(notes["notes"], key=lambda n: (n["start"], n["pitch"]))

    first = notes["notes"][0]
    assert first["pitch"] == 36 and first["start"] == 0.0
    modified = s.ok("modify_notes", track=t, slot=0, changes=[{"id": first["id"], "velocity": 64, "duration": 0.75}])
    assert modified == {"modified": 1, "missing_ids": []}
    after = by_id(s.ok("get_notes", track=t, slot=0))
    assert after[first["id"]]["velocity"] == 64 and after[first["id"]]["duration"] == 0.75
    assert after[first["id"]]["pitch"] == 36 and len(after) == 14

    quantized = s.ok("quantize_notes", track=t, slot=0, grid=0.25, amount=1.0, why="Tighten the ghost hats")
    assert quantized["modified"] == OFF_GRID_COUNT
    starts = [n["start"] for n in s.ok("get_notes", track=t, slot=0)["notes"]]
    assert all(abs(start / 0.25 - round(start / 0.25)) < 1e-9 for start in starts), starts

    before = by_id(s.ok("get_notes", track=t, slot=0))
    transposed = s.ok("transpose_notes", track=t, slot=0, semitones=2)
    assert transposed["modified"] == 14
    after = by_id(s.ok("get_notes", track=t, slot=0))
    assert {k: v["pitch"] for k, v in after.items()} == {k: v["pitch"] + 2 for k, v in before.items()}

    # -- parameters: device and mixer -----------------------------------------------
    res = s.ok("set_parameter", track=t, device_path="0", parameter=param_name, normalized=0.75, why=WHY_FILTER)
    assert res["parameter"]["name"] == param_name
    assert res["previous"]["display"] and res["previous"]["value"] == param["value"]
    assert res["parameter"]["display"] and res["parameter"]["display"] != res["previous"]["display"]
    assert abs(res["parameter"]["value"] - (pmin + 0.75 * (pmax - pmin))) < 1e-9
    assert res["clamped"] is False

    vol = s.ok("set_parameter", track=t, device_path="mixer", parameter="Volume", value=0.85)
    assert vol["parameter"]["name"] == "Volume" and vol["parameter"]["value"] == 0.85
    assert "dB" in vol["parameter"]["display"] and "dB" in vol["previous"]["display"]

    # -- track settings -------------------------------------------------------------
    tr = s.ok("set_track", track=t, name="Lead", color_index=5, mute=True, why="Mute it while arranging")
    assert tr["name"] == "Lead" and tr["color_index"] == 5 and tr["mute"] is True
    assert tr["color"].startswith("#") and len(tr["color"]) == 7
    got = s.ok("get_track", track=t)
    assert got["name"] == "Lead" and got["color_index"] == 5 and got["mute"] is True
    assert got["clip_count"] == 1 and got["device_count"] == 1

    # -- scenes ---------------------------------------------------------------------
    scene = s.ok("create_scene", name="Drop", why="A scene for the drop")
    drop = scene["index"]
    assert drop == len(SCENE_NAMES) and scene["name"] == "Drop"
    scene = s.ok("set_scene", scene=drop, color_index=12, tempo=128.0)
    assert scene["index"] == drop and scene["color_index"] == 12 and scene["tempo"] == 128.0
    scene = s.ok("set_scene", scene=drop, clear_tempo=True, why="Back to the set tempo")  # scene.set tempo: null
    assert scene["index"] == drop and scene["tempo"] is None and scene["color_index"] == 12
    fired = s.ok("fire_scene", scene=drop)
    assert fired["index"] == drop and fired["name"] == "Drop"
    assert s.ok("get_selection")["scene"]["index"] == drop  # launching a scene selects it

    # -- duplicating clips ----------------------------------------------------------
    dup = s.ok("duplicate_clip", track=t, slot=0, target_slot=1)
    assert dup["track"] == t and dup["slot"] == 1 and dup["name"] == "Hook" and dup["note_count"] == 14
    looped = s.ok("duplicate_clip_loop", track=t, slot=1)
    assert looped["length"] == 8.0 and looped["loop_end"] == 8.0 and looped["note_count"] == 28
    assert s.ok("get_clip", track=t, slot=0)["length"] == 4.0  # the source is untouched

    # -- arrangement ----------------------------------------------------------------
    arr = s.ok("add_clip_to_arrangement", track=t, slot=0, time=16.0, why="Place the hook at bar 5")
    assert arr["start_time"] == 16.0 and arr["end_time"] == 20.0
    assert arr["is_arrangement_clip"] is True and arr["arrangement_index"] == 0 and arr["slot"] is None
    text = s.err("add_clip_to_arrangement", track=t, slot=0, time=24.0, delete_source=True)  # needs confirm
    assert "CONFIRM_REQUIRED" in text and "delete_source" in text, text
    assert s.ok("get_clip", track=t, slot=0)["name"] == "Hook"  # the session clip is still there
    assert [c["start_time"] for c in s.ok("get_arrangement")["tracks"][t]["clips"]] == [16.0]  # nothing placed
    locator = s.ok("set_locator", time=16.0, name="Drop", why="Mark the drop")
    assert locator["name"] == "Drop" and locator["time"] == 16.0
    overview = s.ok("get_arrangement")
    assert {"name": "Drop", "time": 16.0} in [{"name": c["name"], "time": c["time"]} for c in overview["locators"]]
    lead_arr = next(x for x in overview["tracks"] if x["index"] == t)
    assert lead_arr["name"] == "Lead" and [c["start_time"] for c in lead_arr["clips"]] == [16.0]
    assert overview["song_length"] >= 20.0

    # -- automation -----------------------------------------------------------------
    auto = s.ok(
        "set_automation", track=t, slot=0, device_path="0", parameter=param_name,
        points=[{"time": 0.0, "value": pmin}, {"time": 4.0, "value": pmax}], mode="ramp",
        why="Sweep the filter over the hook",
    )
    assert auto["exists"] is True and auto["inserted"] > 2 and auto["mode"] == "ramp"
    read = s.ok("get_automation", track=t, slot=0, device_path="0", parameter=param_name)
    assert read["exists"] is True and read["parameter"]["name"] == param_name
    values = [p["value"] for p in read["points"]]
    assert len(values) >= 4 and values[0] == pmin
    assert all(later > earlier for earlier, later in zip(values, values[1:])), values
    assert values[-1] <= pmax

    text = s.err("clear_automation", track=t, slot=0)  # clearing every envelope needs confirm
    assert "CONFIRM_REQUIRED" in text and "every automation envelope" in text, text
    text = s.err("clear_automation", track=t, slot=0, device_path="0", confirm=True)  # PROTOCOL: -32602
    assert "INVALID_PARAMS" in text and "both device_path and parameter" in text, text
    assert s.ok("get_automation", track=t, slot=0, device_path="0", parameter=param_name)["exists"] is True
    cleared = s.ok("clear_automation", track=t, slot=0, confirm=True, why="Reset the sweep")
    assert cleared["cleared"] == "all"
    assert s.ok("get_automation", track=t, slot=0, device_path="0", parameter=param_name)["exists"] is False

    # -- view -----------------------------------------------------------------------
    sel = s.ok("select", track=t, slot=0, show_clip_detail=True, why="Show the hook")
    assert sel["track"]["index"] == t and sel["track"]["name"] == "Lead"
    assert sel["clip_slot"] == {"track": t, "slot": 0, "has_clip": True, "clip_name": "Hook"}
    assert sel["detail_clip"] == {"track": t, "slot": 0, "name": "Hook"}
    assert sel["scene"]["index"] == 0
    assert s.ok("show_view", view="Arranger") == {"view": "Arranger", "visible": True}

    # -- transport ------------------------------------------------------------------
    transport = s.ok("set_transport", tempo=124, why="Drop tempo")
    assert transport["tempo"] == 124
    assert s.ok("get_transport")["tempo"] == 124
    assert s.ok("play")["is_playing"] is True
    text = s.err("set_locator", time=48.0, name="Nope")  # PROTOCOL: locators cannot be set while playing
    assert "INVALID_STATE" in text, text
    assert not CONTRACT_MISMATCH.search(text), text
    assert s.ok("stop")["is_playing"] is False
    assert s.ok("get_transport")["is_playing"] is False
    assert "Nope" not in [c["name"] for c in s.ok("get_arrangement", include_clips=False)["locators"]]

    # -- scale ----------------------------------------------------------------------
    scale = s.ok("set_scale", root_note="F", scale_name="Minor")
    assert scale["root_name"] == "F" and scale["root_note"] == 5 and scale["scale_name"] == "Minor"
    assert scale["scale_intervals"] == [0, 2, 3, 5, 7, 8, 10]
    read_back = s.ok("get_session", include_clips=False, include_devices=False)["scale"]
    assert read_back["root_name"] == "F" and read_back["scale_name"] == "Minor"

    # -- undo -----------------------------------------------------------------------
    assert s.ok("undo")["ok"] is True

    # -- destructive: refused without confirm, then done ----------------------------
    _structured, text, is_error = s.call("delete_clip", track=t, slot=1)
    assert is_error and "CONFIRM_REQUIRED" in text, text
    assert s.ok("get_clip", track=t, slot=1)["name"] == "Hook"  # nothing was deleted
    deleted = s.ok("delete_clip", track=t, slot=1, confirm=True, why="Drop the doubled copy")
    assert deleted["deleted"] == "Hook"
    assert [c["slot"] for c in s.ok("get_track", track=t)["clips"]] == [0]

    # -- browser --------------------------------------------------------------------
    hits = s.ok("browse", query="Reverb")
    assert hits["items"] and all(item["uri"] for item in hits["items"])
    assert hits["items"][0]["name"] == "Reverb" and hits["items"][0]["category"] == "audio_effects"
    assert "Hybrid Reverb" in [item["name"] for item in hits["items"]]

    # -- removing notes -------------------------------------------------------------
    removed = s.ok("remove_notes", track=t, slot=0, from_pitch=44, pitch_span=1)  # the hats (42 + 2)
    assert removed["removed"] == 8 and removed["note_count"] == 6
    assert s.ok("get_notes", track=t, slot=0)["count"] == 6
    text = s.err("remove_notes", track=t, slot=0)  # no note_ids, no window: removes everything, needs confirm
    assert "CONFIRM_REQUIRED" in text and "every note in the clip" in text, text
    assert s.ok("get_notes", track=t, slot=0)["count"] == 6  # refused before reaching Live
    hook = [{"pitch": 38, "start": 0.0, "duration": 1.0}, {"pitch": 45, "start": 2.0, "duration": 1.0, "velocity": 90}]
    replaced = s.ok("replace_notes", track=t, slot=0, notes=hook, why="Start the hook over")
    assert replaced["removed"] == 6 and replaced["added"] == 2 and replaced["note_count"] == 2
    assert [n["pitch"] for n in s.ok("get_notes", track=t, slot=0)["notes"]] == [38, 45]
    wiped = s.ok("remove_notes", track=t, slot=0, confirm=True, why="Wipe the hook")
    assert wiped == {"removed": 2, "note_count": 0}
    assert s.ok("get_notes", track=t, slot=0) == {"notes": [], "count": 0, "clip_length": 4.0}


# --------------------------------------------------------------------------
# 4. action history
# --------------------------------------------------------------------------

def test_history_records_the_sequence(mcp_session):
    hist = mcp_session.ok("get_history", limit=200)
    entries = hist["entries"]
    tools = [e["tool"] for e in entries]
    for name in ("create_midi_track", "load_device", "create_clip", "add_notes", "set_parameter",
                 "set_track", "create_scene", "set_automation", "delete_clip", "replace_notes"):
        assert name in tools, name
    assert not (set(tools) & READ_TOOLS), tools

    def entry(tool, **where):
        return next(e for e in entries if e["tool"] == tool and all(e["params"].get(k) == v for k, v in where.items()))

    created = entry("create_midi_track")
    assert created["resolved"]["track_name"] == "Lead 2" and created["why"] == WHY_TRACK and created["ok"]
    assert created["flags"] == ["M"] and created["duration_ms"] >= 0

    notes = entry("add_notes")
    assert notes["resolved"]["track_name"] == "Lead 2" and notes["resolved"]["clip_name"] == "Hook"
    assert notes["why"] == WHY_NOTES and notes["result_summary"]["added"] == 14

    filt = entry("set_parameter", device_path="0")
    assert filt["resolved"]["track_name"] == "Lead 2" and filt["resolved"]["device_name"] == "Wavetable"
    assert filt["resolved"]["parameter_name"] and filt["why"] == WHY_FILTER
    assert filt["result_summary"]["previous"] and filt["result_summary"]["value"]

    renamed = entry("set_track")
    assert renamed["resolved"]["track_name"] == "Lead"

    refused = next(e for e in entries if e["tool"] == "delete_clip" and not e["ok"])
    assert "CONFIRM_REQUIRED" in refused["error"] and refused["flags"] == ["M", "D"]
    done = next(e for e in entries if e["tool"] == "delete_clip" and e["ok"])
    assert done["resolved"]["clip_name"] == "Hook" and done["params"]["confirm"] is True
    wiped = next(e for e in entries if e["tool"] == "remove_notes" and e["params"].get("confirm"))
    assert wiped["ok"] and wiped["flags"] == ["M", "D"] and wiped["result_summary"]["removed"] == 2
    refused_wipe = next(e for e in entries if e["tool"] == "remove_notes" and not e["ok"])
    assert "CONFIRM_REQUIRED" in refused_wipe["error"] and refused_wipe["flags"] == ["M", "D"]

    whys = [e["why"] for e in entries if e.get("why")]
    assert len(whys) >= 2 and WHY_TRACK in whys and WHY_NOTES in whys

    # The files live under CLAUDE_LIVE_HOME/history.
    history_dir = mcp_session.home / "history"
    jsonl_path, md_path = Path(hist["history_jsonl"]), Path(hist["history_md"])
    assert jsonl_path.parent == history_dir and md_path.parent == history_dir
    assert jsonl_path.is_file() and md_path.is_file()
    lines = [json.loads(line) for line in jsonl_path.read_text(encoding="utf-8").splitlines() if line.strip()]
    assert len(lines) == hist["total"] and lines[-1]["seq"] == hist["total"]
    assert any(line["tool"] == "get_session" for line in lines)  # reads are in the JSONL only

    md = md_path.read_text(encoding="utf-8")
    assert md.startswith("# ClaudeLive session ")
    assert WHY_TRACK in md and WHY_NOTES in md and WHY_FILTER in md
    md_tools = [line.split()[1] for line in md.splitlines() if re.match(r"^\d\d:\d\d:\d\d  ", line)]
    assert md_tools and not (set(md_tools) & READ_TOOLS), md_tools
    assert "Lead 2 › Wavetable ›" in md


# --------------------------------------------------------------------------
# 4b. the other addressing modes (PROTOCOL.md section 5)
# --------------------------------------------------------------------------

def test_return_master_and_arrangement_addressing(mcp_session):
    s = mcp_session
    ret = s.ok("get_track", track=0, track_type="return")
    assert ret["name"] == "A-Reverb" and ret["track_type"] == "return" and ret["type"] == "return"
    assert [d["name"] for d in ret["devices"]] == ["Reverb"] and ret["can_be_armed"] is False
    master = s.ok("get_track", track=0, track_type="master")
    assert master["type"] == "master" and [d["name"] for d in master["devices"]] == ["Limiter"]

    res = s.ok("set_parameter", track=1, track_type="return", device_path="mixer", parameter="Volume", value=0.5,
               why="Pull the delay return down")
    assert res["parameter"]["value"] == 0.5 and "dB" in res["parameter"]["display"]
    assert s.ok("get_track", track=1, track_type="return")["volume"]["value"] == 0.5
    res = s.ok("set_parameter", track=0, track_type="master", device_path="0", parameter="Ceiling", value=-1.0)
    assert res["parameter"]["name"] == "Ceiling" and res["parameter"]["value"] == -1.0

    arr = s.ok("get_clip", track=0, arrangement_index=0)
    assert arr["is_arrangement_clip"] is True and arr["start_time"] == 0.0 and arr["slot"] is None
    assert s.ok("get_notes", track=0, arrangement_index=0)["count"] == 10  # the "Drums 1" copy

    _structured, text, is_error = s.call("get_clip", track=0)  # neither slot nor arrangement_index
    assert is_error and "INVALID_PARAMS" in text and "exactly one of slot" in text


def test_delete_track_by_track_type(mcp_session):
    s = mcp_session
    created = s.ok("create_return_track", name="C-Temp", why="A return to delete again")
    assert created["track_type"] == "return"
    returns = s.ok("get_session", include_clips=False, include_devices=False)["return_tracks"]
    index = next(r["index"] for r in returns if r["name"] == "C-Temp")
    text = s.err("delete_track", track=index, track_type="return")  # confirm is still required
    assert "CONFIRM_REQUIRED" in text and "return track" in text, text
    text = s.err("delete_track", track=0, track_type="master", confirm=True)  # rejected locally
    assert "INVALID_PARAMS" in text and '"track" or "return"' in text, text
    deleted = s.ok("delete_track", track=index, track_type="return", confirm=True, why="Done with it")
    assert deleted["deleted"] == "C-Temp" and deleted["track_type"] == "return"
    assert deleted["track_count"] == len(returns) - 1
    names = [r["name"] for r in s.ok("get_session", include_clips=False, include_devices=False)["return_tracks"]]
    assert "C-Temp" not in names and names == [r["name"] for r in returns if r["name"] != "C-Temp"]


def test_include_note_counts(mcp_session):
    """List-style reads leave note_count null unless asked (counting is expensive); clip.get always fills it."""
    s = mcp_session
    plain = s.ok("get_session")
    drums = plain["tracks"][0]
    assert drums["type"] == "midi" and drums["clips"]
    assert all(c["note_count"] is None for c in drums["clips"]), drums["clips"]
    counted = s.ok("get_session", include_note_counts=True)["tracks"][0]["clips"]
    assert all(isinstance(c["note_count"], int) for c in counted), counted
    assert counted[0]["note_count"] == s.ok("get_notes", track=0, slot=0)["count"]
    assert s.ok("get_clip", track=0, slot=0)["note_count"] == counted[0]["note_count"]

    assert all(c["note_count"] is None for c in s.ok("get_track", track=0)["clips"])
    assert [c["note_count"] for c in s.ok("get_track", track=0, include_note_counts=True)["clips"]] == [c["note_count"] for c in counted]
    assert all(c["note_count"] is None for c in s.ok("get_track", track=VOX, include_note_counts=True)["clips"])  # audio

    arr_plain = next(t for t in s.ok("get_arrangement")["tracks"] if t["index"] == 0)["clips"]
    assert arr_plain and all(c["note_count"] is None for c in arr_plain)
    arr_counted = next(t for t in s.ok("get_arrangement", include_note_counts=True)["tracks"] if t["index"] == 0)["clips"]
    assert all(isinstance(c["note_count"], int) for c in arr_counted)
    assert arr_counted[0]["note_count"] == s.ok("get_notes", track=0, arrangement_index=0)["count"]


# --------------------------------------------------------------------------
# 5. every tool once
# --------------------------------------------------------------------------

def _last_track(s):
    return {"track": len(s.ok("get_session", include_clips=False, include_devices=False)["tracks"]) - 1, "confirm": True}


def _last_scene(s):
    return {"scene": len(s.ok("get_session", include_clips=False, include_devices=False)["scenes"]) - 1, "confirm": True}


def _first_drum_note_change(s):
    first = s.ok("get_notes", track=0, slot=0)["notes"][0]
    return {"track": 0, "slot": 0, "changes": [{"id": first["id"], "velocity": 70}]}


def _outro_locator(s):
    locators = s.ok("get_arrangement", include_clips=False)["locators"]
    outro = next((c for c in locators if c["name"] == "Outro"), locators[-1])
    return {"index": outro["index"]}


# (tool, args) in TOOLS.md order; args may be a callable(session) -> args when they depend on
# the current state. Targets are the factory tracks 0-3 (untouched by the sequence) and
# objects created earlier in this table, so each row stays valid in file order.
SMOKE = [
    # status and diagnostics
    ("ableton_status", {}),
    ("ableton_describe_api", {}),
    ("get_history", {"limit": 10, "include_reads": True}),
    # session and transport
    ("get_session", {"include_params": True}),
    ("get_transport", {}),
    ("set_transport", {"tempo": 120.0, "metronome": True, "loop_enabled": True, "loop_start": 0.0, "loop_length": 32.0,
                       "signature_numerator": 4, "signature_denominator": 4, "position": 8.0}),
    ("play", {"from_start": True}),
    ("continue_playing", {}),
    ("stop", {}),  # last, so the transport is stopped when the locator rows run
    ("set_scale", {"root_note": 0, "scale_name": "Dorian"}),
    ("undo", {"steps": 2}),
    ("redo", {}),
    # tracks
    ("get_track", {"track": 0, "include_params": True}),
    ("create_midi_track", {"name": "Smoke MIDI"}),
    ("create_audio_track", {"name": "Smoke Audio"}),
    ("create_return_track", {"name": "C-Smoke"}),
    ("set_track", {"track": 1, "solo": False, "arm": True, "volume": 0.7, "pan": -0.25, "sends": [{"index": 0, "value": 0.2}]}),
    ("delete_track", _last_track),
    # scenes
    ("create_scene", {"name": "Smoke Scene", "index": -1}),
    ("set_scene", {"scene": 1, "name": "Verse 1", "color_index": 20}),
    ("fire_scene", {"scene": 0}),
    ("duplicate_scene", {"scene": 1}),
    ("delete_scene", _last_scene),
    # clips (Bass = track 1 has clips in slots 0, 1 and, after duplicate_scene, 2)
    ("create_clip", {"track": 1, "slot": 6, "length": 2.0, "name": "Smoke Clip"}),
    ("get_clip", {"track": 0, "arrangement_index": 0}),
    ("set_clip", {"track": 1, "slot": 0, "name": "Bass 1", "color_index": 14, "looping": True, "loop_start": 0.0,
                  "loop_end": 4.0, "launch_quantization": "q_bar"}),
    ("fire_clip", {"track": 1, "slot": 0}),
    ("stop_clip", {"track": 1}),
    ("duplicate_clip", {"track": 1, "slot": 0, "target_slot": 7}),
    ("duplicate_clip_loop", {"track": 1, "slot": 1}),
    ("delete_clip", {"track": 2, "slot": 0, "confirm": True}),
    # notes (Drums 1 in track 0 slot 0)
    ("get_notes", {"track": 0, "slot": 0, "from_time": 0.0, "time_span": 4.0}),
    ("add_notes", {"track": 0, "slot": 0, "notes": [{"pitch": 39, "start": 2.5, "duration": 0.25, "velocity": 90}]}),
    ("replace_notes", {"track": 0, "slot": 1, "notes": [{"pitch": 36, "start": float(b), "duration": 0.5} for b in range(4)]}),
    ("remove_notes", {"track": 0, "slot": 0, "from_pitch": 42, "pitch_span": 1}),
    ("modify_notes", _first_drum_note_change),
    ("quantize_notes", {"track": 0, "slot": 0, "grid": 0.5, "amount": 0.5, "swing": 0.2}),
    ("transpose_notes", {"track": 0, "slot": 0, "semitones": -12}),
    # devices and parameters (Bass = Operator; Pad = racks; Drums = Drum Rack + Compressor; Vox = EQ Eight + Reverb)
    ("get_devices", {"track": 2, "include_params": True, "depth": 2}),
    ("set_parameter", {"track": 1, "device_path": "0", "parameter": "Filter Freq", "normalized": 0.5}),
    ("set_parameters", {"track": 1, "device_path": "0", "values": [
        {"parameter": "Filter Res", "value": 0.3}, {"parameter": "Osc-A Wave", "display": "Saw D"},
        {"parameter": "Volume", "normalized": 0.8}]}),
    ("set_device_enabled", {"track": 0, "device_path": "1", "enabled": False}),
    ("delete_device", {"track": VOX, "device_path": "1", "confirm": True}),
    # browser
    ("browse", {"categories": ["audio_effects"], "limit": 5}),
    ("load_device", {"track": VOX, "uri": "query:AudioFx#Saturator"}),
    # arrangement
    ("get_arrangement", {"include_clips": True}),
    ("add_clip_to_arrangement", {"track": 1, "slot": 7, "time": 32.0, "delete_source": True, "confirm": True}),  # slot 7: the duplicate_clip copy
    ("set_locator", {"time": 96.0, "name": "Outro"}),
    ("delete_locator", _outro_locator),
    # automation
    ("get_automation", {"track": 1, "slot": 0, "device_path": "0", "parameter": "Filter Freq"}),
    ("set_automation", {"track": 1, "slot": 0, "device_path": "mixer", "parameter": "Volume",
                        "points": [{"time": 0.0, "value": 0.5}, {"time": 2.0, "value": 0.85}], "mode": "steps"}),
    ("clear_automation", {"track": 1, "slot": 0, "device_path": "mixer", "parameter": "Volume"}),
    # view
    ("get_selection", {}),
    ("select", {"track": 1, "device_path": "0", "show_device_detail": True}),
    ("show_view", {"view": "Session"}),
]


def test_smoke_table_covers_every_tool(mcp_session):
    listed = {tool.name for tool in mcp_session.list_tools()}
    assert len(listed) == 55, sorted(listed)
    table = [name for name, _args in SMOKE]
    assert len(table) == len(set(table)), "duplicate rows in SMOKE"
    assert listed - set(table) == set(), "tools missing from SMOKE: %s" % sorted(listed - set(table))
    assert set(table) - listed == set(), "SMOKE names unknown tools: %s" % sorted(set(table) - listed)


@pytest.mark.parametrize(("tool", "args"), SMOKE, ids=[row[0] for row in SMOKE])
def test_every_tool_once(mcp_session, tool, args):
    if callable(args):
        args = args(mcp_session)
    structured, text, is_error = mcp_session.call(tool, **args)
    if is_error:
        assert not CONTRACT_MISMATCH.search(text), "%s(%r): contract mismatch between the halves:\n%s" % (tool, args, text)
    assert not is_error, "%s(%r) failed:\n%s" % (tool, args, text)
    assert isinstance(structured, dict) and structured, "%s returned no structured object: %r" % (tool, text)


def test_delete_source_moved_the_session_clip(mcp_session):
    """After the SMOKE row: the copy sits in the arrangement and slot 7 on Bass is empty again."""
    s = mcp_session
    bass = next(t for t in s.ok("get_arrangement")["tracks"] if t["index"] == 1)
    assert 32.0 in [c["start_time"] for c in bass["clips"]]
    text = s.err("get_notes", track=1, slot=7)
    assert "INVALID_STATE" in text and not CONTRACT_MISMATCH.search(text), text
    assert 7 not in [c["slot"] for c in s.ok("get_track", track=1)["clips"]]


def test_delete_locator_fails_while_playing(mcp_session):
    s = mcp_session
    locator = s.ok("set_locator", time=120.0, name="Tail")
    try:
        assert s.ok("play")["is_playing"] is True
        text = s.err("delete_locator", index=locator["index"])
        assert "INVALID_STATE" in text and not CONTRACT_MISMATCH.search(text), text
    finally:
        s.ok("stop")
    locators = s.ok("get_arrangement", include_clips=False)["locators"]
    tail = next(c for c in locators if c["name"] == "Tail")
    assert s.ok("delete_locator", index=tail["index"])["deleted"] == "Tail"


# --------------------------------------------------------------------------
# 6. negative cases
# --------------------------------------------------------------------------

def test_not_found_names_the_index(mcp_session):
    text = mcp_session.err("get_track", track=99)
    assert "NOT_FOUND" in text and "99" in text, text
    assert not CONTRACT_MISMATCH.search(text), text


def test_notes_on_an_audio_clip_is_invalid_state(mcp_session):
    assert mcp_session.ok("get_clip", track=VOX, slot=0)["is_audio"] is True
    text = mcp_session.err("get_notes", track=VOX, slot=0)
    assert "INVALID_STATE" in text, text
    assert not CONTRACT_MISMATCH.search(text), text
