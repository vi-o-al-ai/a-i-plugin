"""Action history: one JSONL file (every tool call) and one Markdown file (mutations only).

Format per TOOLS.md "Action history". Names in the Markdown target path come from protocol
results seen in this session (``TrackSummary.name``, ``ClipSummary.name``, ...); the server
never issues extra reads to resolve them. Nothing here ever raises into a tool.
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

log = logging.getLogger("ableton_live_mcp.history")

MUTATING_FLAGS = frozenset({"M", "D", "UI"})

TRACK_RESULT_TOOLS = frozenset({"get_track", "set_track", "create_midi_track", "create_audio_track", "create_return_track"})
SCENE_RESULT_TOOLS = frozenset({"create_scene", "set_scene", "fire_scene", "duplicate_scene"})
CLIP_RESULT_TOOLS = frozenset(
    {"create_clip", "get_clip", "set_clip", "fire_clip", "duplicate_clip", "duplicate_clip_loop", "add_clip_to_arrangement"}
)
DELETE_TOOLS = {
    "delete_track": "track_name",
    "delete_scene": "scene_name",
    "delete_clip": "clip_name",
    "delete_device": "device_name",
    "delete_locator": "locator_name",
}
ADDRESS_KEYS = frozenset(
    {"track", "track_type", "slot", "arrangement_index", "scene", "device_path", "parameter", "confirm", "index"}
)


def parse_flags(flags: str | list[str] | tuple[str, ...] | None) -> list[str]:
    """``"MD"`` -> ``["M", "D"]``, ``"UI"`` -> ``["UI"]``, ``"R"`` -> ``["R"]``."""
    if not isinstance(flags, str):
        return list(flags or [])
    out: list[str] = []
    i = 0
    while i < len(flags):
        if flags.startswith("UI", i):
            out.append("UI")
            i += 2
        else:
            out.append(flags[i])
            i += 1
    return out


def _is_scalar(value: Any) -> bool:
    return value is None or isinstance(value, (str, int, float, bool))


def _fmt(value: Any) -> str:
    if isinstance(value, float):
        return f"{value:g}"
    if isinstance(value, bool):
        return "on" if value else "off"
    if isinstance(value, dict):
        return value.get("display") or value.get("name") or json.dumps(value, separators=(",", ":"), default=str)
    if isinstance(value, list):
        return ", ".join(_fmt(v) for v in value)
    return str(value)


# ---------------------------------------------------------------------------------------
# Name cache: remembers names seen in results so later Markdown lines can show them.
# ---------------------------------------------------------------------------------------


class NameCache:
    """Index -> name lookups learned from protocol results (no extra round trips)."""

    def __init__(self) -> None:
        self.tracks: dict[tuple[str, int | None], str] = {}
        self.scenes: dict[int, str] = {}
        self.clips: dict[tuple[int, int | None, int | None], str] = {}
        self.devices: dict[tuple[str, int | None, str], str] = {}

    # -- learning -------------------------------------------------------------------

    def _learn_track(self, d: Any, track_type: str | None = None) -> None:
        if not isinstance(d, dict) or not d.get("name"):
            return
        tt = d.get("track_type") or track_type or "track"
        index = d.get("index")
        self.tracks[(tt, index)] = d["name"]
        for clip in d.get("clips") or []:
            self._learn_clip(clip)
        for dev in d.get("devices") or []:
            self._learn_device(tt, index, dev)

    def _learn_clip(self, d: Any) -> None:
        if not isinstance(d, dict) or not d.get("name") or d.get("track") is None:
            return
        self.clips[(d["track"], d.get("slot"), d.get("arrangement_index"))] = d["name"]

    def _learn_device(self, track_type: str, track: int | None, d: Any) -> None:
        if not isinstance(d, dict) or not d.get("name") or d.get("path") is None:
            return
        self.devices[(track_type, track, str(d["path"]))] = d["name"]
        for chain in d.get("chains") or []:
            for sub in (chain or {}).get("devices") or []:
                self._learn_device(track_type, track, sub)

    def _learn_scene(self, d: Any) -> None:
        if isinstance(d, dict) and d.get("name") and d.get("index") is not None:
            self.scenes[d["index"]] = d["name"]

    def _forget_track_tree(self) -> None:
        self.tracks.clear()
        self.clips.clear()
        self.devices.clear()

    def _forget_devices(self, track_type: str, track: int | None) -> None:
        for key in [k for k in self.devices if k[0] == track_type and k[1] == track]:
            del self.devices[key]

    def learn(self, tool: str, params: dict[str, Any], result: Any) -> None:
        """Update the cache from a successful ``tool`` call."""
        if not isinstance(result, dict):
            return
        tt = params.get("track_type") or "track"
        track = params.get("track")

        if tool == "get_session":
            for t in result.get("tracks") or []:
                self._learn_track(t, "track")
            for t in result.get("return_tracks") or []:
                self._learn_track(t, "return")
            self._learn_track(result.get("master"), "master")
            for s in result.get("scenes") or []:
                self._learn_scene(s)
            self._learn_selection(result.get("selection"))
        elif tool in ("create_midi_track", "create_audio_track", "create_return_track"):
            self._forget_track_tree()  # indices may shift
            self._learn_track(result)
        elif tool == "delete_track":
            self._forget_track_tree()
        elif tool in TRACK_RESULT_TOOLS:
            self._learn_track(result, tt)
        elif tool == "get_devices":
            if params.get("device_path") is not None:
                self._learn_device(tt, track, result)
            else:
                for dev in result.get("devices") or []:
                    self._learn_device(tt, track, dev)
        elif tool == "delete_device":
            self._forget_devices(tt, track)
        elif tool == "load_device":
            self._learn_track(result.get("track"), tt)
            self._forget_devices(tt, track)
            for dev in result.get("devices") or []:
                self._learn_device(tt, track, dev)
            self._learn_device(tt, track, result.get("loaded"))
        elif tool in ("create_scene", "duplicate_scene", "delete_scene"):
            self.scenes.clear()
            self.clips.clear()  # slot numbering shifts with scenes
            self._learn_scene(result)
        elif tool in SCENE_RESULT_TOOLS:
            self._learn_scene(result)
        elif tool == "delete_clip":
            self.clips.pop((track, params.get("slot"), params.get("arrangement_index")), None)
        elif tool in CLIP_RESULT_TOOLS:
            self._learn_clip(result)
        elif tool == "get_arrangement":
            for t in result.get("tracks") or []:
                if isinstance(t, dict) and t.get("name") and t.get("index") is not None:
                    self.tracks[("track", t["index"])] = t["name"]
                for clip in (t or {}).get("clips") or []:
                    self._learn_clip(clip)
        elif tool in ("get_selection", "select"):
            self._learn_selection(result)

    def _learn_selection(self, sel: Any) -> None:
        if not isinstance(sel, dict):
            return
        t = sel.get("track")
        if isinstance(t, dict) and t.get("name"):
            self.tracks[(t.get("track_type") or "track", t.get("index"))] = t["name"]
        self._learn_scene(sel.get("scene"))
        slot = sel.get("clip_slot")
        if isinstance(slot, dict) and slot.get("clip_name") and slot.get("track") is not None:
            self.clips[(slot["track"], slot.get("slot"), None)] = slot["clip_name"]
        dev = sel.get("device")
        if isinstance(t, dict) and isinstance(dev, dict) and dev.get("name") and dev.get("path") is not None:
            self.devices[(t.get("track_type") or "track", t.get("index"), str(dev["path"]))] = dev["name"]

    # -- lookup ---------------------------------------------------------------------

    def resolve(self, params: dict[str, Any]) -> dict[str, str]:
        """Names for whatever ``params`` addresses, when known."""
        out: dict[str, str] = {}
        tt = params.get("track_type") or "track"
        track = params.get("track")
        if track is not None or tt == "master":
            name = self.tracks.get((tt, track))
            if name is None and tt == "master":
                name = next((v for k, v in self.tracks.items() if k[0] == "master"), None)
            if name:
                out["track_name"] = name
        if track is not None:
            if params.get("slot") is not None:
                name = self.clips.get((track, params["slot"], None))
                if name:
                    out["clip_name"] = name
            elif params.get("arrangement_index") is not None:
                name = self.clips.get((track, None, params["arrangement_index"]))
                if name:
                    out["clip_name"] = name
            if params.get("device_path") is not None:
                name = self.devices.get((tt, track, str(params["device_path"])))
                if name:
                    out["device_name"] = name
        if params.get("scene") is not None:
            name = self.scenes.get(params["scene"])
            if name:
                out["scene_name"] = name
        return out


# ---------------------------------------------------------------------------------------
# Per-tool extraction: resolved names and compact result summaries.
# ---------------------------------------------------------------------------------------


def names_from_result(tool: str, params: dict[str, Any], result: Any) -> dict[str, Any]:
    """Names carried by the result itself (take precedence over the cache)."""
    out: dict[str, Any] = {}
    if not isinstance(result, dict):
        return out
    if tool in TRACK_RESULT_TOOLS:
        out["track_name"] = result.get("name")
    elif tool in SCENE_RESULT_TOOLS:
        out["scene_name"] = result.get("name")
    elif tool in CLIP_RESULT_TOOLS:
        out["clip_name"] = result.get("name")
    elif tool == "set_parameter":
        out["parameter_name"] = (result.get("parameter") or {}).get("name")
    elif tool == "set_parameters":
        names = [(r.get("parameter") or {}).get("name") for r in result.get("results") or [] if isinstance(r, dict)]
        out["parameter_names"] = [n for n in names if n]
    elif tool == "load_device":
        out["track_name"] = (result.get("track") or {}).get("name")
        out["device_name"] = (result.get("loaded") or {}).get("name")
    elif tool in DELETE_TOOLS:
        out[DELETE_TOOLS[tool]] = result.get("deleted")
    elif tool == "set_locator":
        out["locator_name"] = result.get("name")
    elif tool == "clear_automation":
        cleared = result.get("cleared")
        if cleared and cleared != "all":
            out["parameter_name"] = cleared
    elif tool == "get_automation":
        out["parameter_name"] = (result.get("parameter") or {}).get("name")
    elif tool == "get_devices" and params.get("device_path") is not None:
        out["device_name"] = result.get("name")
    elif tool in ("select", "get_selection"):
        out["track_name"] = (result.get("track") or {}).get("name")
        out["scene_name"] = (result.get("scene") or {}).get("name")
        out["device_name"] = (result.get("device") or {}).get("name")
        out["clip_name"] = (result.get("clip_slot") or {}).get("clip_name")
    return {k: v for k, v in out.items() if v}


def _changed(params: dict[str, Any], result: Any, display_keys: tuple[str, ...] = ()) -> dict[str, Any]:
    """The fields a set_* tool changed, using Live's display strings when the result has them."""
    out: dict[str, Any] = {}
    for key, value in params.items():
        if key in ADDRESS_KEYS:
            continue
        if isinstance(result, dict) and key in display_keys and isinstance(result.get(key), dict):
            out[key] = result[key].get("display", value)
        else:
            out[key] = value
    return out


def summarize_result(tool: str, params: dict[str, Any], result: Any) -> dict[str, Any] | None:
    """Compact ``result_summary`` for the JSONL entry."""
    if not isinstance(result, dict):
        return None
    r = result
    if tool == "set_parameter":
        prev = (r.get("previous") or {}).get("display")
        new = (r.get("parameter") or {}).get("display")
        out: dict[str, Any] = {"previous": prev, "value": new}
        if r.get("clamped"):
            out["clamped"] = True
        return out
    if tool == "set_parameters":
        values = {}
        for item in r.get("results") or []:
            p = (item or {}).get("parameter") or {}
            if p.get("name"):
                values[p["name"]] = p.get("display")
        return {"set": len(r.get("results") or []), "errors": len(r.get("errors") or []), "values": values}
    if tool in DELETE_TOOLS:
        return {k: v for k, v in r.items() if _is_scalar(v)}
    if tool in TRACK_RESULT_TOOLS:
        out = {"index": r.get("index"), "name": r.get("name"), "type": r.get("type")}
        if tool == "set_track":
            out["changed"] = _changed(params, r, ("volume", "pan"))
        return out
    if tool in SCENE_RESULT_TOOLS:
        out = {"index": r.get("index"), "name": r.get("name")}
        if tool == "set_scene":
            out["changed"] = _changed(params, r)
        return out
    if tool in CLIP_RESULT_TOOLS:
        out = {"name": r.get("name"), "track": r.get("track"), "length": r.get("length")}
        if r.get("slot") is not None:
            out["slot"] = r["slot"]
        if r.get("arrangement_index") is not None:
            out["arrangement_index"] = r["arrangement_index"]
        if r.get("start_time") is not None:
            out["start_time"] = r["start_time"]
        if tool == "set_clip":
            out["changed"] = _changed(params, r)
        return out
    if tool in ("set_transport", "play", "stop", "continue_playing", "get_transport"):
        out = {"tempo": r.get("tempo"), "is_playing": r.get("is_playing"), "position": r.get("position")}
        if tool == "set_transport":
            out["changed"] = _changed(params, r)
        return out
    if tool == "set_scale":
        return {"root_name": r.get("root_name"), "scale_name": r.get("scale_name")}
    if tool == "load_device":
        loaded = r.get("loaded") or {}
        return {"loaded": loaded.get("name"), "path": loaded.get("path"), "device_count": len(r.get("devices") or [])}
    if tool == "browse":
        return {"count": len(r.get("items") or []), "truncated": r.get("truncated", False)}
    if tool == "get_session":
        return {
            "tracks": len(r.get("tracks") or []),
            "scenes": len(r.get("scenes") or []),
            "tempo": (r.get("transport") or {}).get("tempo"),
        }
    if tool in ("select", "get_selection"):
        return {k: (v or {}).get("name") if isinstance(v, dict) else v for k, v in r.items() if k in ("track", "scene", "device")}
    # generic: scalar fields only
    out = {k: v for k, v in r.items() if _is_scalar(v)}
    for key in ("missing_ids", "errors"):
        if isinstance(r.get(key), list):
            out[key] = len(r[key])
    return dict(list(out.items())[:12])


def _track_label(params: dict[str, Any]) -> str:
    tt = params.get("track_type") or "track"
    if tt == "master":
        return "master"
    if tt == "return":
        return f"return {params.get('track')}"
    return f"track {params.get('track')}"


def target_path(tool: str, params: dict[str, Any], resolved: dict[str, Any]) -> str:
    """``Bass › Wavetable › Filter Freq`` or ``track 2 › device 0 › Filter Freq``."""
    segs: list[str] = []
    if tool in ("set_transport", "play", "stop", "continue_playing"):
        return "transport"
    if tool == "set_scale":
        return "scale"
    if tool in ("undo", "redo"):
        return "song"
    if tool == "show_view":
        return str(params.get("view", "view"))
    if tool in ("set_locator", "delete_locator"):
        if resolved.get("locator_name"):
            return f"locator {resolved['locator_name']}"
        if params.get("index") is not None:
            return f"locator {params['index']}"
        return f"locator @ {_fmt(params.get('time'))}"

    if params.get("track") is not None or params.get("track_type") == "master":
        segs.append(resolved.get("track_name") or _track_label(params))
    elif resolved.get("track_name"):
        segs.append(resolved["track_name"])

    if params.get("slot") is not None:
        segs.append(resolved.get("clip_name") or f"slot {params['slot']}")
    elif params.get("arrangement_index") is not None:
        segs.append(resolved.get("clip_name") or f"arrangement clip {params['arrangement_index']}")
    elif tool in CLIP_RESULT_TOOLS and resolved.get("clip_name"):
        segs.append(resolved["clip_name"])

    if params.get("device_path") is not None:
        path = str(params["device_path"])
        segs.append(resolved.get("device_name") or ("mixer" if path == "mixer" else f"device {path}"))
    elif tool == "load_device" and resolved.get("device_name"):
        segs.append(resolved["device_name"])

    if params.get("parameter") is not None:
        segs.append(resolved.get("parameter_name") or str(params["parameter"]))
    elif tool == "set_parameters" and resolved.get("parameter_names"):
        names = resolved["parameter_names"]
        segs.append(", ".join(names[:3]) + (f" (+{len(names) - 3})" if len(names) > 3 else ""))
    elif tool == "clear_automation" and params.get("parameter") is None:
        segs.append("all envelopes")

    if params.get("scene") is not None:
        segs.append(resolved.get("scene_name") or f"scene {params['scene']}")
    elif tool in SCENE_RESULT_TOOLS and resolved.get("scene_name"):
        segs.append(resolved["scene_name"])

    return " › ".join(segs)


def summary_text(tool: str, params: dict[str, Any], summary: dict[str, Any] | None, result: Any) -> str:
    """Human summary for the Markdown line."""
    s = summary or {}
    r = result if isinstance(result, dict) else {}
    changed = s.get("changed")
    if tool == "set_parameter":
        text = f"{s.get('previous')} → {s.get('value')}"
        return text + (" (clamped)" if s.get("clamped") else "")
    if tool == "set_parameters":
        values = s.get("values") or {}
        if 0 < len(values) <= 4:
            text = ", ".join(f"{k} → {v}" for k, v in values.items())
        else:
            text = f"{s.get('set', 0)} parameters set"
        return text + (f", {s['errors']} failed" if s.get("errors") else "")
    if tool == "set_device_enabled":
        return "on" if r.get("is_active", params.get("enabled")) else "off"
    if tool in DELETE_TOOLS:
        return "deleted"
    if tool in ("create_midi_track", "create_audio_track", "create_return_track", "create_scene"):
        return f"created at index {s.get('index')}" if s.get("index") is not None else "created"
    if tool == "create_clip":
        return f"created ({_fmt(s.get('length'))} beats)"
    if tool in ("set_track", "set_scene", "set_clip", "set_transport"):
        if changed:
            return ", ".join(f"{k} → {_fmt(v)}" for k, v in changed.items())
        return "updated"
    if tool in ("fire_clip", "fire_scene"):
        return "fired (empty slot)" if r.get("fired_empty_slot") else "fired"
    if tool == "stop_clip":
        return "stopped" if params.get("slot") is not None else "all clips stopped"
    if tool == "play":
        return "playing from start" if params.get("from_start") else "playing"
    if tool == "stop":
        return "stopped"
    if tool == "continue_playing":
        return "continued"
    if tool in ("undo", "redo"):
        return f"{tool} ×{r.get('steps', params.get('steps', 1))}"
    if tool == "set_scale":
        return f"{s.get('root_name')} {s.get('scale_name')}"
    if tool == "add_notes":
        return f"+{r.get('added')} notes ({r.get('note_count')} total)"
    if tool == "replace_notes":
        return f"replaced {r.get('removed')} → {r.get('added')} notes"
    if tool == "remove_notes":
        return f"-{r.get('removed')} notes ({r.get('note_count')} left)"
    if tool == "modify_notes":
        return f"modified {r.get('modified')} notes"
    if tool == "quantize_notes":
        return f"quantized {r.get('modified')} notes (grid {_fmt(params.get('grid'))}, amount {_fmt(params.get('amount'))})"
    if tool == "transpose_notes":
        semis = params.get("semitones", 0)
        return f"transposed {r.get('modified')} notes by {semis:+d}" if isinstance(semis, int) else f"transposed {r.get('modified')} notes"
    if tool == "duplicate_clip":
        return f"copied to track {s.get('track')} slot {s.get('slot')}"
    if tool == "duplicate_clip_loop":
        return f"loop doubled → {_fmt(s.get('length'))} beats"
    if tool == "duplicate_scene":
        return f"duplicated → scene {s.get('index')}"
    if tool == "load_device":
        return f"loaded {s.get('loaded')}" if s.get("loaded") else "loaded (not a device)"
    if tool == "add_clip_to_arrangement":
        text = f"placed at beat {_fmt(params.get('time'))}"
        return text + (" (moved)" if params.get("delete_source") else "")
    if tool == "set_locator":
        return f"set at beat {_fmt(r.get('time', params.get('time')))}"
    if tool == "set_automation":
        return f"{r.get('inserted')} points ({params.get('mode', 'ramp')})"
    if tool == "clear_automation":
        return f"cleared {r.get('cleared')}"
    if tool == "select":
        return "selected"
    if tool == "show_view":
        return "shown"
    if s:
        return ", ".join(f"{k}={_fmt(v)}" for k, v in list(s.items())[:4])
    return "ok"


# ---------------------------------------------------------------------------------------
# The recorder
# ---------------------------------------------------------------------------------------


class ActionHistory:
    """Records every tool call; writes files lazily on the first record."""

    def __init__(self, history_dir: Path | str, *, pid: int | None = None):
        self.dir = Path(history_dir)
        self.pid = os.getpid() if pid is None else pid
        self.started_at = datetime.now().astimezone()
        stamp = self.started_at.strftime("%Y-%m-%d_%H%M%S")
        self.jsonl_path = self.dir / f"{stamp}_{self.pid}.jsonl"
        self.md_path = self.dir / f"{stamp}_{self.pid}.md"
        self.entries: list[dict[str, Any]] = []
        self.names = NameCache()
        self._seq = 0
        self._files_ready = False
        self._write_failed = False

    @property
    def files_created(self) -> bool:
        return self._files_ready

    # -- recording ------------------------------------------------------------------

    def record(
        self,
        tool: str,
        flags: str | list[str] | tuple[str, ...],
        params: dict[str, Any] | None,
        why: str | None,
        result: Any,
        error: str | None,
        duration_ms: float,
    ) -> dict[str, Any] | None:
        """Append one entry. Never raises."""
        try:
            return self._record(tool, flags, params, why, result, error, duration_ms)
        except Exception:  # noqa: BLE001 - history must never break a tool call
            log.exception("history: failed to record %s", tool)
            return None

    def _record(
        self,
        tool: str,
        flags: str | list[str] | tuple[str, ...],
        params: dict[str, Any] | None,
        why: str | None,
        result: Any,
        error: str | None,
        duration_ms: float,
    ) -> dict[str, Any]:
        flag_list = parse_flags(flags)
        clean_params = {k: v for k, v in (params or {}).items() if v is not None and k != "why"}
        ok = error is None
        now_utc = datetime.now(timezone.utc)
        self._seq += 1

        if ok:
            try:
                self.names.learn(tool, clean_params, result)
            except Exception:  # noqa: BLE001
                log.debug("history: name cache update failed for %s", tool, exc_info=True)
        resolved = self.names.resolve(clean_params)
        if ok:
            resolved.update(names_from_result(tool, clean_params, result))

        entry: dict[str, Any] = {
            "ts": now_utc.strftime("%Y-%m-%dT%H:%M:%S.") + f"{now_utc.microsecond // 1000:03d}Z",
            "seq": self._seq,
            "tool": tool,
            "flags": flag_list,
            "params": clean_params,
            "resolved": resolved,
            "why": why,
            "result_summary": summarize_result(tool, clean_params, result) if ok else None,
            "ok": ok,
            "duration_ms": int(round(duration_ms)),
        }
        if not ok:
            entry["error"] = error
        self.entries.append(entry)

        self._ensure_files()
        self._append(self.jsonl_path, json.dumps(entry, ensure_ascii=False, default=str) + "\n")
        if MUTATING_FLAGS & set(flag_list):
            self._append(self.md_path, self._markdown_line(entry, result) + "\n")
        return entry

    def _markdown_line(self, entry: dict[str, Any], result: Any) -> str:
        local_time = datetime.now().astimezone().strftime("%H:%M:%S")
        tool = entry["tool"]
        target = target_path(tool, entry["params"], entry["resolved"])
        if entry["ok"]:
            summary = summary_text(tool, entry["params"], entry.get("result_summary"), result)
        else:
            summary = f"FAILED: {entry.get('error')}"
        body = f"{target} : {summary}" if target else summary
        if entry.get("why"):
            body += f"   — {entry['why']}"
        return f"{local_time}  {tool:<20}  {body}"

    # -- files ----------------------------------------------------------------------

    def _ensure_files(self) -> None:
        if self._files_ready:
            return
        self.dir.mkdir(parents=True, exist_ok=True)
        if not self.jsonl_path.exists():
            self.jsonl_path.touch()
        if not self.md_path.exists():
            header = self.started_at.strftime("# ClaudeLive session %Y-%m-%d %H:%M:%S")
            self.md_path.write_text(header + "\n\n", encoding="utf-8")
        self._files_ready = True
        log.info("history: %s", self.jsonl_path)

    def _append(self, path: Path, text: str) -> None:
        try:
            with path.open("a", encoding="utf-8") as fh:
                fh.write(text)
        except OSError:
            if not self._write_failed:
                self._write_failed = True
                log.exception("history: cannot write %s (further write errors suppressed)", path)

    # -- querying -------------------------------------------------------------------

    def get(self, limit: int = 50, include_reads: bool = False) -> dict[str, Any]:
        """Entries for ``get_history``: most recent last."""
        entries = self.entries if include_reads else [e for e in self.entries if MUTATING_FLAGS & set(e["flags"])]
        limit = max(1, int(limit)) if limit else len(entries)
        return {
            "entries": entries[-limit:],
            "count": len(entries),
            "total": len(self.entries),
            "history_jsonl": str(self.jsonl_path),
            "history_md": str(self.md_path),
            "files_created": self._files_ready,
        }
