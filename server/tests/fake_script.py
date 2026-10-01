"""A fake ClaudeLive Remote Script: newline-delimited JSON-RPC over TCP with canned results.

Records every request, supports scripted errors, delays, connection drops and wrong ids.
Result shapes follow PROTOCOL.md section 6.
"""

from __future__ import annotations

import asyncio
import json
from typing import Any, Callable

TRACK_NAMES = ["Kick", "Snare", "Bass", "Pad"]
SCENE_NAMES = ["Intro", "Verse", "Chorus", "Drop"]
DEVICE_NAMES = {"0": "Wavetable", "1": "Reverb", "0/0/0": "Operator"}
DESTRUCTIVE = {"song.delete_track", "song.delete_scene", "clip.delete", "device.delete"}
NOTE_RANGE_KEYS = ("from_time", "time_span", "from_pitch", "pitch_span")
RETRY_TIMEOUT = (-32006, "Browser traversal hit its time budget; the same call again continues", {"retry": True, "nodes_visited": 1234})

BROWSER_ITEMS = [
    {"name": "Wavetable", "uri": "query:Synths#Wavetable", "category": "instruments", "path": ["Instruments", "Wavetable"]},
    {"name": "Wavetable Bass", "uri": "query:Sounds#Bass:Wavetable%20Bass", "category": "sounds", "path": ["Sounds", "Bass", "Wavetable Bass"]},
    {"name": "Operator", "uri": "query:Synths#Operator", "category": "instruments", "path": ["Instruments", "Operator"]},
    {"name": "Reverb", "uri": "query:AudioFx#Reverb", "category": "audio_effects", "path": ["Audio Effects", "Reverb"]},
    {"name": "Hybrid Reverb", "uri": "query:AudioFx#Hybrid%20Reverb", "category": "audio_effects", "path": ["Audio Effects", "Hybrid Reverb"]},
    {"name": "Drift", "uri": "query:Synths#Drift", "category": "instruments", "path": ["Instruments", "Drift"]},
    {"name": "Arpeggiator", "uri": "query:MidiFx#Arpeggiator", "category": "midi_effects", "path": ["MIDI Effects", "Arpeggiator"]},
]


def browser_item(base: dict[str, Any]) -> dict[str, Any]:
    return {**base, "is_loadable": True, "is_folder": False, "is_device": base["category"] != "sounds"}


def track_summary(index: int = 2, name: str | None = None, track_type: str = "track", type_: str = "midi", **over: Any) -> dict[str, Any]:
    if name is None:
        name = TRACK_NAMES[index] if track_type == "track" and 0 <= index < len(TRACK_NAMES) else f"{track_type} {index}"
    d = {
        "index": index, "track_type": track_type, "name": name, "type": type_,
        "color_index": 14, "color": "#FF9A00",
        "mute": False, "solo": False, "arm": False, "can_be_armed": type_ in ("midi", "audio"),
        "is_foldable": False, "is_grouped": False, "group_track_index": None,
        "volume": {"value": 0.85, "display": "0.0 dB"}, "pan": {"value": 0.0, "display": "C"},
        "sends": [{"index": 0, "name": "A-Reverb", "value": 0.0, "display": "-inf dB"}],
        "playing_slot_index": -1, "fired_slot_index": -1, "clip_count": 1, "device_count": 2,
    }
    d.update(over)
    return d


def clip_summary(track: int = 2, slot: int | None = 0, name: str | None = None, arrangement_index: int | None = None, **over: Any) -> dict[str, Any]:
    if name is None:
        name = f"{TRACK_NAMES[track] if 0 <= track < len(TRACK_NAMES) else 'Clip'} {(slot or 0) + 1}"
    d = {
        "track": track, "slot": slot, "arrangement_index": arrangement_index,
        "name": name, "color_index": 14, "color": "#FF9A00",
        "is_midi": True, "is_audio": False, "is_arrangement_clip": arrangement_index is not None,
        "length": 4.0, "loop_start": 0.0, "loop_end": 4.0, "looping": True,
        "start_marker": 0.0, "end_marker": 4.0, "start_time": None, "end_time": None,
        "is_playing": False, "is_recording": False, "is_triggered": False,
        "signature_numerator": 4, "signature_denominator": 4, "note_count": 16,
    }
    d.update(over)
    return d


def device_summary(path: str = "0", name: str | None = None, **over: Any) -> dict[str, Any]:
    name = name or DEVICE_NAMES.get(path, f"Device {path}")
    type_ = "audio_effect" if "Reverb" in name else "instrument"
    d = {
        "path": path, "name": name, "class_name": "InstrumentVector" if name == "Wavetable" else name,
        "class_display_name": name, "type": type_, "is_active": True, "is_rack": False,
        "can_have_drum_pads": False, "chain_count": 0, "parameter_count": 93,
    }
    d.update(over)
    return d


def parameter(index: int = 5, name: str = "Filter Freq", value: float = 0.62, display: str = "1.20 kHz", **over: Any) -> dict[str, Any]:
    d = {
        "index": index, "name": name, "original_name": name, "value": value, "min": 0.0, "max": 1.0, "default": 0.5,
        "display": display, "is_quantized": False, "value_items": None, "is_enabled": True, "automation_state": "none",
    }
    d.update(over)
    return d


def scene_summary(index: int = 0, name: str | None = None, **over: Any) -> dict[str, Any]:
    name = name or (SCENE_NAMES[index] if 0 <= index < len(SCENE_NAMES) else f"Scene {index}")
    d = {"index": index, "name": name, "color_index": 0, "color": "#000000", "is_triggered": False, "tempo": None, "is_empty": False}
    d.update(over)
    return d


def transport(**over: Any) -> dict[str, Any]:
    d = {
        "tempo": 124.0, "signature_numerator": 4, "signature_denominator": 4, "is_playing": False, "position": 0.0,
        "loop": {"enabled": False, "start": 0.0, "length": 16.0}, "metronome": False, "record_mode": False,
        "session_record": False, "song_length": 128.0,
    }
    d.update(over)
    return d


def scale(root_note: Any = 0, scale_name: str | None = None) -> dict[str, Any]:
    names = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]
    root_name = root_note if isinstance(root_note, str) else names[int(root_note) % 12]
    return {"root_note": names.index(root_name) if root_name in names else 0, "root_name": root_name,
            "scale_name": scale_name or "Minor", "scale_intervals": [0, 2, 3, 5, 7, 8, 10]}


def selection(track: int = 2, scene: int = 0, slot: int | None = 0, device_path: str | None = "0", track_type: str = "track") -> dict[str, Any]:
    tname = TRACK_NAMES[track] if 0 <= track < len(TRACK_NAMES) else f"Track {track}"
    return {
        "track": {"index": track, "track_type": track_type, "name": tname},
        "scene": {"index": scene, "name": SCENE_NAMES[scene] if scene < len(SCENE_NAMES) else f"Scene {scene}"},
        "clip_slot": {"track": track, "slot": slot if slot is not None else scene, "has_clip": True, "clip_name": f"{tname} 1"},
        "detail_clip": {"track": track, "slot": slot if slot is not None else scene, "name": f"{tname} 1"},
        "device": {"path": device_path, "name": DEVICE_NAMES.get(device_path or "", "Device")} if device_path else None,
        "parameter": None,
    }


def cue_point(index: int = 0, name: str = "Drop", time: float = 64.0) -> dict[str, Any]:
    return {"index": index, "name": name, "time": time}


def note(id_: int, pitch: int, start: float) -> dict[str, Any]:
    return {"id": id_, "pitch": pitch, "start": start, "duration": 0.5, "velocity": 100, "mute": False,
            "probability": 1.0, "velocity_deviation": 0.0, "release_velocity": 64}


class FakeScript:
    """Start with ``await start()``; ``port`` is then the ephemeral port it listens on."""

    def __init__(self) -> None:
        self.port: int = 0
        self.requests: list[dict[str, Any]] = []
        self.connections = 0
        self.errors: dict[str, tuple[int, str, Any]] = {}  # method -> (code, message, data)
        self.delays: dict[str, float] = {}  # method -> seconds before answering
        self.drop_next = False  # close the connection instead of answering the next request
        self.wrong_id_next = False  # answer the next request with a mismatched id
        self.garbage_next = False  # answer the next request with a non-JSON line
        self.note_count = 16
        # browser.search: the first N calls answer truncated=true (the script's resumable
        # traversal). Call k (0-based) returns the hits among search_pages[k] when given, else a
        # cumulative slice of BROWSER_ITEMS (2 more items per call); later calls scan everything.
        self.search_truncated_calls = 0
        self.search_pages: list[list[dict[str, Any]]] = []
        self.search_calls = 0
        # method -> how many leading calls answer -32006 TIMEOUT with {"retry": true}
        self.retry_timeouts: dict[str, int] = {}
        self.ping_result: dict[str, Any] = {
            "script_version": "0.1.0", "protocol_version": 1, "live_version": "12.1.5", "live_major": 12,
            "live_minor": 1, "python_version": "3.11.4", "tick_count": 1234,
        }
        self._server: asyncio.base_events.Server | None = None
        self._tasks: set[asyncio.Task[Any]] = set()
        self.handlers: dict[str, Callable[[dict[str, Any]], dict[str, Any]]] = self._build_handlers()

    # -- lifecycle --------------------------------------------------------------------

    async def start(self) -> "FakeScript":
        self._server = await asyncio.start_server(self._serve, "127.0.0.1", 0)
        self.port = self._server.sockets[0].getsockname()[1]
        return self

    async def stop(self) -> None:
        if self._server is not None:
            self._server.close()
            await self._server.wait_closed()
        for task in list(self._tasks):
            task.cancel()
        if self._tasks:
            await asyncio.gather(*self._tasks, return_exceptions=True)

    # -- helpers for tests --------------------------------------------------------------

    def requests_for(self, method: str) -> list[dict[str, Any]]:
        return [r for r in self.requests if r.get("method") == method]

    @property
    def calls(self) -> list[tuple[str, dict[str, Any]]]:
        return [(r.get("method"), r.get("params", {})) for r in self.requests]

    # -- protocol -----------------------------------------------------------------------

    async def _serve(self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter) -> None:
        self.connections += 1
        task = asyncio.current_task()
        if task is not None:
            self._tasks.add(task)
        try:
            while True:
                line = await reader.readline()
                if not line:
                    break
                await self._handle_line(line, writer)
        except (asyncio.CancelledError, ConnectionError):
            pass
        finally:
            if task is not None:
                self._tasks.discard(task)
            try:
                writer.close()
            except Exception:  # noqa: BLE001
                pass

    async def _handle_line(self, line: bytes, writer: asyncio.StreamWriter) -> None:
        try:
            req = json.loads(line)
        except ValueError:
            await self._send(writer, {"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": "Parse error"}})
            return
        self.requests.append(req)
        req_id = req.get("id")
        method = req.get("method")
        params = req.get("params") or {}

        if self.drop_next:
            self.drop_next = False
            writer.close()
            return
        if method in self.delays:
            await asyncio.sleep(self.delays[method])
        if self.garbage_next:
            self.garbage_next = False
            writer.write(b"this is not json\n")
            await writer.drain()
            return
        if self.wrong_id_next:
            self.wrong_id_next = False
            req_id = 999999

        error = self._scripted_error(method, params)
        if error is not None:
            code, message, data = error
            body: dict[str, Any] = {"code": code, "message": message}
            if data is not None:
                body["data"] = data
            await self._send(writer, {"jsonrpc": "2.0", "id": req_id, "error": body})
            return
        handler = self.handlers.get(method)
        if handler is None:
            await self._send(writer, {"jsonrpc": "2.0", "id": req_id, "error": {"code": -32601, "message": f"Method not found: {method}"}})
            return
        await self._send(writer, {"jsonrpc": "2.0", "id": req_id, "result": handler(params)})

    async def _send(self, writer: asyncio.StreamWriter, obj: dict[str, Any]) -> None:
        try:
            writer.write((json.dumps(obj, separators=(",", ":")) + "\n").encode("utf-8"))
            await writer.drain()
        except (ConnectionError, RuntimeError):
            pass

    def _scripted_error(self, method: str, params: dict[str, Any]) -> tuple[int, str, Any] | None:
        if method in self.errors:
            return self.errors[method]
        if self.retry_timeouts.get(method, 0) > 0:
            self.retry_timeouts[method] -= 1
            return RETRY_TIMEOUT
        if params.get("track") == 9:
            return (-32000, "Track 9 does not exist (set has 4 tracks)", {"kind": "track", "index": 9, "count": 4})
        confirm_needed = method in DESTRUCTIVE
        if method == "notes.remove" and not params.get("note_ids") and not any(k in params for k in NOTE_RANGE_KEYS):
            confirm_needed = True  # PROTOCOL.md: removing every note needs confirm
        if method == "arrangement.add_clip_from_slot" and params.get("delete_source"):
            confirm_needed = True  # PROTOCOL.md: deleting the session clip needs confirm
        if confirm_needed and params.get("confirm") is not True:
            return (-32002, f"{method} is destructive and requires confirm: true", {"method": method})
        return None

    # -- canned results -----------------------------------------------------------------

    def _build_handlers(self) -> dict[str, Callable[[dict[str, Any]], dict[str, Any]]]:
        ok = lambda p: {"ok": True}  # noqa: E731

        def track_full(index: int, track_type: str = "track") -> dict[str, Any]:
            t = track_summary(index, track_type=track_type, type_="midi" if track_type == "track" else track_type)
            t["clips"] = [clip_summary(index, 0)] if track_type == "track" else []
            t["devices"] = [device_summary("0"), device_summary("1")] if track_type == "track" else []
            return t

        def overview(p: dict[str, Any]) -> dict[str, Any]:
            return {
                "transport": transport(), "scale": scale(),
                "tracks": [track_full(i) for i in range(len(TRACK_NAMES))],
                "return_tracks": [track_full(0, "return")], "master": track_full(0, "master"),
                "scenes": [scene_summary(i) for i in range(len(SCENE_NAMES))],
                "selection": selection(), "live_version": "12.1.5",
            }

        def set_track(p: dict[str, Any]) -> dict[str, Any]:
            over: dict[str, Any] = {k: p[k] for k in ("mute", "solo", "arm", "color_index") if k in p}
            if "volume" in p:
                over["volume"] = {"value": p["volume"], "display": f"{20 * (p['volume'] - 0.85) * 5:.1f} dB"}
            if "pan" in p:
                over["pan"] = {"value": p["pan"], "display": f"{abs(p['pan']) * 50:.0f}{'L' if p['pan'] < 0 else 'R'}" if p["pan"] else "C"}
            return track_summary(p["track"], p.get("name"), p.get("track_type", "track"), **over)

        def notes_add(p: dict[str, Any]) -> dict[str, Any]:
            self.note_count += len(p.get("notes", []))
            return {"added": len(p.get("notes", [])), "note_count": self.note_count}

        def notes_replace(p: dict[str, Any]) -> dict[str, Any]:
            removed, self.note_count = self.note_count, len(p.get("notes", []))
            return {"removed": removed, "added": self.note_count, "note_count": self.note_count}

        def notes_remove(p: dict[str, Any]) -> dict[str, Any]:
            removed = len(p["note_ids"]) if p.get("note_ids") else self.note_count
            self.note_count = max(0, self.note_count - removed)
            return {"removed": removed, "note_count": self.note_count}

        def set_parameter(p: dict[str, Any]) -> dict[str, Any]:
            name = p["parameter"] if isinstance(p["parameter"], str) else "Filter Freq"
            return {"parameter": parameter(name=name, value=p.get("value", 0.62)), "previous": {"value": 0.5, "display": "800 Hz"}, "clamped": False}

        def set_parameters(p: dict[str, Any]) -> dict[str, Any]:
            return {"results": [set_parameter({"parameter": v["parameter"], "value": v.get("value", 0.5)}) for v in p["values"]], "errors": []}

        def search(p: dict[str, Any]) -> dict[str, Any]:
            q = p["query"].lower()
            cats = p.get("categories")
            call = self.search_calls
            self.search_calls += 1
            truncated = call < self.search_truncated_calls
            if truncated:
                pool = self.search_pages[call] if call < len(self.search_pages) else BROWSER_ITEMS[: 2 * (call + 1)]
            else:
                pool = BROWSER_ITEMS
            hits = [i for i in pool if q in i["name"].lower() and (not cats or i["category"] in cats)]
            rank = lambda i: (0 if i["name"].lower() == q else 1 if i["name"].lower().startswith(q) else 2)  # noqa: E731
            hits.sort(key=rank)
            return {
                "items": [browser_item(i) for i in hits[: p.get("limit", 25)]],
                "truncated": truncated,
                "nodes_visited": len(pool),
                "total_matches": len(hits),
            }

        def listing(p: dict[str, Any]) -> dict[str, Any]:
            cat = p.get("category")
            items = [browser_item(i) for i in BROWSER_ITEMS if not cat or i["category"] == cat]
            return {"items": items[: p.get("limit", 100)], "truncated": False}

        def load(p: dict[str, Any]) -> dict[str, Any]:
            item = next((i for i in BROWSER_ITEMS if i["uri"] == p["uri"]), None)
            name = item["name"] if item else p["uri"].rsplit("#", 1)[-1]
            loaded = device_summary("2", name) if not item or item["category"] != "sounds" else None
            devices = [device_summary("0"), device_summary("1")] + ([loaded] if loaded else [])
            return {"loaded": loaded, "track": track_summary(p.get("track", 2), track_type=p.get("track_type", "track")), "devices": devices, "method": "load_item"}

        def arrangement_overview(p: dict[str, Any]) -> dict[str, Any]:
            return {
                "song_length": 128.0, "loop": {"enabled": False, "start": 0.0, "length": 16.0},
                "locators": [cue_point()],
                "tracks": [{"index": i, "name": n, "clips": [clip_summary(i, None, f"{n} arr", 0, start_time=0.0, end_time=16.0)]} for i, n in enumerate(TRACK_NAMES)],
            }

        return {
            "sys.ping": lambda p: dict(self.ping_result),
            # The script chooses the path (PROTOCOL.md sys.describe_api); params are ignored.
            "sys.describe_api": lambda p: {"path": "/Users/me/.claude-live/api/live_api_12.1.5.md", "classes": 42, "bytes": 12345},
            "sys.log": ok,
            "song.get_overview": overview,
            "song.get_transport": lambda p: transport(),
            "song.set_transport": lambda p: transport(**{k: v for k, v in p.items() if k in ("tempo", "metronome", "position", "record_mode", "session_record")}),
            "song.play": lambda p: transport(is_playing=True),
            "song.stop": lambda p: transport(is_playing=False),
            "song.continue": lambda p: transport(is_playing=True, position=8.0),
            "song.stop_all_clips": ok,
            "song.get_scale": lambda p: scale(),
            "song.set_scale": lambda p: scale(p.get("root_note", 0), p.get("scale_name")),
            "song.undo": ok,
            "song.redo": ok,
            "song.create_midi_track": lambda p: track_summary(4 if p.get("index", -1) == -1 else p["index"], p.get("name") or "5-MIDI"),
            "song.create_audio_track": lambda p: track_summary(4 if p.get("index", -1) == -1 else p["index"], p.get("name") or "5-Audio", type_="audio"),
            "song.create_return_track": lambda p: track_summary(1, p.get("name") or "B-Return", "return", "return"),
            "song.delete_track": lambda p: {
                "deleted": TRACK_NAMES[p["track"]] if p.get("track_type", "track") == "track" else f"{chr(65 + p['track'])}-Return",
                "track_type": p.get("track_type", "track"), "track_count": 3,
            },
            "song.create_scene": lambda p: scene_summary(4 if p.get("index", -1) == -1 else p["index"], p.get("name") or "New Scene"),
            "song.duplicate_scene": lambda p: scene_summary(p["scene"] + 1, f"{SCENE_NAMES[p['scene']]} copy"),
            "song.delete_scene": lambda p: {"deleted": SCENE_NAMES[p["scene"]], "scene_count": 3},
            "view.get_selection": lambda p: selection(),
            "view.select": lambda p: selection(p.get("track", 2), p.get("scene", 0), p.get("slot"), p.get("device_path"), p.get("track_type", "track")),
            "view.show_view": lambda p: {"view": p["view"], "visible": True},
            "track.get": lambda p: track_full(p["track"], p.get("track_type", "track")),
            "track.set": set_track,
            "track.stop_clips": ok,
            "scene.set": lambda p: scene_summary(p["scene"], p.get("name"), **({"tempo": p["tempo"]} if "tempo" in p else {})),
            "scene.fire": lambda p: scene_summary(p["scene"], is_triggered=True),
            "clip.create": lambda p: clip_summary(p["track"], p["slot"], p.get("name"), length=p["length"], loop_end=p["length"], end_marker=p["length"], note_count=0),
            "clip.get": lambda p: clip_summary(p["track"], p.get("slot"), None, p.get("arrangement_index")),
            "clip.set": lambda p: clip_summary(p["track"], p.get("slot"), p.get("name"), p.get("arrangement_index"), **{k: p[k] for k in ("looping", "loop_start", "loop_end") if k in p}),
            "clip.fire": lambda p: clip_summary(p["track"], p["slot"], is_triggered=True),
            "clip.stop": ok,
            "clip.duplicate": lambda p: clip_summary(p.get("target_track", p["track"]), p["target_slot"], f"{TRACK_NAMES[p['track']]} {p['slot'] + 1}"),
            "clip.duplicate_loop": lambda p: clip_summary(p["track"], p["slot"], length=8.0, loop_end=8.0, end_marker=8.0, note_count=32),
            "clip.delete": lambda p: {"deleted": f"{TRACK_NAMES[p['track']]} {(p.get('slot') or 0) + 1}"},
            "notes.get": lambda p: {"notes": [note(1, 36, 0.0), note(2, 38, 1.0)], "count": 2, "clip_length": 4.0},
            "notes.add": notes_add,
            "notes.replace": notes_replace,
            "notes.remove": notes_remove,
            "notes.modify": lambda p: {"modified": len(p["changes"]), "missing_ids": []},
            "notes.quantize": lambda p: {"modified": self.note_count},
            "notes.transpose": lambda p: {"modified": self.note_count},
            "device.list": lambda p: {"devices": [device_summary("0"), device_summary("1")], "mixer": {"path": "mixer", "parameters": [parameter(0, "Volume", 0.85, "0.0 dB")]}},
            "device.get": lambda p: {**device_summary(p["path"]), "parameters": [parameter()], "chains": [], "drum_pads": []},
            "device.get_parameter": lambda p: parameter(),
            "device.set_parameter": set_parameter,
            "device.set_parameters": set_parameters,
            "device.set_enabled": lambda p: {"is_active": p["enabled"]},
            "device.delete": lambda p: {"deleted": DEVICE_NAMES.get(p["path"], f"Device {p['path']}")},
            "browser.search": search,
            "browser.list": listing,
            "browser.load": load,
            "arrangement.get_overview": arrangement_overview,
            "arrangement.get_clips": lambda p: {"clips": [clip_summary(p["track"], None, None, 0, start_time=0.0, end_time=16.0)]},
            "arrangement.add_clip_from_slot": lambda p: clip_summary(p["track"], None, None, 0, start_time=p["time"], end_time=p["time"] + 4.0),
            "arrangement.set_locator": lambda p: cue_point(0, p.get("name") or "Locator", p["time"]),
            "arrangement.delete_locator": lambda p: {"deleted": "Drop"},
            "automation.get": lambda p: {"exists": True, "points": [{"time": 0.0, "value": 0.5}, {"time": 2.0, "value": 0.8}], "parameter": parameter()},
            "automation.set": lambda p: {"inserted": len(p["points"]), "exists": True, "mode": p.get("mode", "ramp")},
            "automation.clear": lambda p: {"cleared": p.get("parameter") or "all"},
        }
