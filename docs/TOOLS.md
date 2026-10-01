# MCP tool surface (v1)

The MCP server `ableton-live-mcp` exposes the tools below to Claude. Each tool maps to one protocol method in `PROTOCOL.md` unless noted. Tool names are what Claude sees; Claude Code prefixes them as `mcp__plugin_ableton-live_live__<tool>` (plugin `ableton-live`, server key `live`).

Conventions that apply to every tool:

- **Addressing** follows PROTOCOL.md §5: `track` (int), `track_type` (`"track"`|`"return"`|`"master"`, default `"track"`), `slot`, `arrangement_index`, `device_path` (string like `"0/1/2"` or `"mixer"`), `parameter` (name or index).
- **`why`** — every mutating tool accepts an optional `why: str`. It is not sent to Live; it is recorded in the action history so the log reads as a narrative. The mentor skill asks Claude to fill it in when teaching.
- **`confirm`** — destructive tools declare `confirm: bool = False` and require `confirm=True`; otherwise they fail locally without touching Live, and the error text explains what would be deleted. The script checks again on its side.
- **Return values** are JSON objects (structured content). Errors raise a tool error whose message is `"<CODE>: <message>. <hint>"`.
- **Descriptions** in the server code must stay under ~2 sentences each; the skills carry the long-form guidance.
- Tool annotations: reads are `readOnlyHint=true`; deletes are `destructiveHint=true`; everything else `destructiveHint=false, idempotentHint=false`.

Flags: **M** mutating (recorded in history), **D** destructive (confirm), **UI** view-only (recorded, not undoable), **R** read-only.

## Status and diagnostics

| Tool | Params | Protocol | Flags | Purpose |
|---|---|---|---|---|
| `ableton_status` | — | `sys.ping` + local checks | R | Is Live reachable? Returns script/protocol/Live versions, round-trip ms, history file paths, and troubleshooting steps on failure (never raises; returns `connected: false` with `diagnosis`). |
| `ableton_describe_api` | — | `sys.describe_api` | M (writes a file under `~/.claude-live/api/`) | Dump the real Live API from inside the user's Live for debugging. The path is chosen by the script, never by the model. |
| `get_history` | `limit?: int = 50, include_reads?: bool = false` | local | R | Return the current session's recorded actions (most recent last) and the history file paths. |

## Session and transport

| Tool | Params | Protocol | Flags |
|---|---|---|---|
| `get_session` | `include_clips?=true, include_devices?=true, include_params?=false, include_returns?=true, include_note_counts?=false` | `song.get_overview` | R |
| `get_transport` | — | `song.get_transport` | R |
| `set_transport` | `tempo?, metronome?, loop_enabled?, loop_start?, loop_length?, position?, signature_numerator?, signature_denominator?, why?` | `song.set_transport` | M. Record controls are deliberately not exposed. |
| `play` | `from_start?=false, why?` | `song.play` | M |
| `stop` | `why?` | `song.stop` | M |
| `continue_playing` | `why?` | `song.continue` | M |
| `set_scale` | `root_note?: int\|str, scale_name?: str, why?` | `song.set_scale` | M |
| `undo` | `steps?: int = 1` (1–20) | `song.undo` ×n | M. Description warns that it also undoes the user's own most recent edits. |
| `redo` | `steps?: int = 1` | `song.redo` ×n | M |

## Tracks

| Tool | Params | Protocol | Flags |
|---|---|---|---|
| `get_track` | `track, track_type?, include_clips?=true, include_devices?=true, include_params?=false, include_note_counts?=false` | `track.get` | R |
| `create_midi_track` | `name?, index?=-1, why?` | `song.create_midi_track` | M |
| `create_audio_track` | `name?, index?=-1, why?` | `song.create_audio_track` | M |
| `create_return_track` | `name?, why?` | `song.create_return_track` | M |
| `set_track` | `track, track_type?, name?, color_index?, mute?, solo?, arm?, volume?, pan?, sends?: list[{index, value}], fold?, why?` | `track.set` | M |
| `delete_track` | `track, track_type?="track" ("track" or "return"), confirm, why?` | `song.delete_track` | M D |

## Scenes

| Tool | Params | Protocol | Flags |
|---|---|---|---|
| `create_scene` | `name?, index?=-1, why?` | `song.create_scene` | M |
| `set_scene` | `scene, name?, color_index?, tempo?, clear_tempo?=false, why?` | `scene.set` (`clear_tempo` sends `tempo: null`) | M |
| `fire_scene` | `scene, why?` | `scene.fire` | M |
| `duplicate_scene` | `scene, why?` | `song.duplicate_scene` | M |
| `delete_scene` | `scene, confirm, why?` | `song.delete_scene` | M D |

## Clips

| Tool | Params | Protocol | Flags |
|---|---|---|---|
| `create_clip` | `track, slot, length: float = 4.0, name?, why?` | `clip.create` | M |
| `get_clip` | `track, slot?, arrangement_index?` | `clip.get` | R |
| `set_clip` | `track, slot?, arrangement_index?, name?, color_index?, loop_start?, loop_end?, looping?, start_marker?, end_marker?, launch_quantization?: str (q_global … q_thirtysecond, see PROTOCOL.md), why?` | `clip.set` | M |
| `fire_clip` | `track, slot, why?` | `clip.fire` | M |
| `stop_clip` | `track, slot?, why?` | `clip.stop` | M |
| `duplicate_clip` | `track, slot, target_slot, target_track?, why?` | `clip.duplicate` | M |
| `duplicate_clip_loop` | `track, slot, why?` | `clip.duplicate_loop` | M |
| `delete_clip` | `track, slot?, arrangement_index?, confirm, why?` | `clip.delete` | M D |

## Notes

`notes` items: `{pitch, start, duration, velocity?=100, mute?=false, probability?=1.0, velocity_deviation?=0.0, release_velocity?=64}`. The server chunks writes at 500 notes per protocol request and enforces the 1000-note limit per tool call by splitting; it never fails a call for size alone unless above 5000.

| Tool | Params | Protocol | Flags |
|---|---|---|---|
| `get_notes` | `track, slot?, arrangement_index?, from_time?, time_span?, from_pitch?, pitch_span?` | `notes.get` | R |
| `add_notes` | `track, slot?, arrangement_index?, notes: list, why?` | `notes.add` | M |
| `replace_notes` | `track, slot?, arrangement_index?, notes: list, why?` | `notes.replace` | M (`destructiveHint=true`; description says it replaces every note in the clip; undoable) |
| `remove_notes` | `track, slot?, arrangement_index?, note_ids?, from_time?, time_span?, from_pitch?, pitch_span?, confirm?=false, why?` | `notes.remove` | M (D when no `note_ids` and no range given: that removes every note and needs `confirm`) |
| `modify_notes` | `track, slot?, arrangement_index?, changes: list[{id, ...}], why?` | `notes.modify` | M |
| `quantize_notes` | `track, slot?, arrangement_index?, grid: float = 0.25, amount: float = 1.0, swing?: float = 0.0, why?` | `notes.quantize` | M |
| `transpose_notes` | `track, slot?, arrangement_index?, semitones: int (required, −127..127, non-zero), from_time?, time_span?, from_pitch?, pitch_span?, why?` | `notes.transpose` | M |

## Devices and parameters

| Tool | Params | Protocol | Flags |
|---|---|---|---|
| `get_devices` | `track, track_type?, device_path?, include_params?: bool (default false without `device_path`, true with it), depth?=2` | `device.list` (no path) / `device.get` (path) | R |
| `set_parameter` | `track, device_path, parameter, value?, normalized?, display?, track_type?, why?` | `device.set_parameter` | M |
| `set_parameters` | `track, device_path, values: list[{parameter, value?, normalized?, display?}], track_type?, why?` | `device.set_parameters` | M |
| `set_device_enabled` | `track, device_path, enabled: bool, track_type?, why?` | `device.set_enabled` | M |
| `delete_device` | `track, device_path, confirm, track_type?, why?` | `device.delete` | M D |

## Browser

| Tool | Params | Protocol | Flags |
|---|---|---|---|
| `browse` | `query?: str, categories?: list[str], uri?: str, limit?=25, loadable_only?=true` | `browser.search` when `query` (looped while `truncated`, up to 25 calls, merged by `uri`); `browser.list` when `uri`/`categories` only (retried on `TIMEOUT`) | R |
| `load_device` | `track, uri?: str, name?: str, track_type?, after_device_path?, category?: str, why?` | `browser.search` (if `name`; looped while `truncated` until an exact case-insensitive name match is found or the traversal finishes) then `browser.load` (retried on `TIMEOUT`) | M. With `name`, the server never picks a non-exact match from an unfinished traversal; the result includes `matched` and `alternatives` so Claude can correct a wrong pick. |

## Arrangement

| Tool | Params | Protocol | Flags |
|---|---|---|---|
| `get_arrangement` | `include_clips?=true, include_note_counts?=false` | `arrangement.get_overview` | R |
| `add_clip_to_arrangement` | `track, slot, time: float, delete_source?=false, confirm?=false, why?` | `arrangement.add_clip_from_slot` | M (D when `delete_source`: needs `confirm`) |
| `set_locator` | `time: float, name?: str, why?` | `arrangement.set_locator` | M. Fails with INVALID_STATE while playing. |
| `delete_locator` | `index: int, why?` | `arrangement.delete_locator` | M (`destructiveHint=true`, no confirm: locators are cheap to recreate). Fails with INVALID_STATE while playing. |

## Automation

| Tool | Params | Protocol | Flags |
|---|---|---|---|
| `get_automation` | `track, slot?, arrangement_index?, device_path, parameter, from_time?, time_span?, resolution?=0.25` | `automation.get` | R |
| `set_automation` | `track, slot?, arrangement_index?, device_path, parameter, points: list[{time, value}], mode?="ramp", resolution?=0.0625, why?` | `automation.set` | M |
| `clear_automation` | `track, slot?, arrangement_index?, device_path?, parameter?, confirm?=false, why?` | `automation.clear` | M (D when clearing all; `device_path` without `parameter` is rejected locally as INVALID_PARAMS; `destructiveHint=true`) |

## View

| Tool | Params | Protocol | Flags |
|---|---|---|---|
| `get_selection` | — | `view.get_selection` | R |
| `select` | `track?, track_type?, scene?, slot?, device_path?, show_clip_detail?, show_device_detail?, why?` | `view.select` | UI |
| `show_view` | `view: str, why?` | `view.show_view` | UI |

Total: 55 tools.

## Action history

The server records to `${CLAUDE_LIVE_HOME:-~/.claude-live}/history/<YYYY-MM-DD>_<HHMMSS>_<pid>.jsonl` and a sibling `.md`. One session = one server process.

JSONL entry:

```json
{"ts": "2026-10-01T14:03:22.118Z", "seq": 12, "tool": "set_parameter", "flags": ["M"],
 "params": {"track": 2, "device_path": "0", "parameter": "Filter Freq", "value": 0.62},
 "resolved": {"track_name": "Bass", "device_name": "Wavetable", "parameter_name": "Filter Freq"},
 "why": "Open the filter so the bass cuts through the pad",
 "result_summary": {"previous": "800 Hz", "value": "1.20 kHz"},
 "ok": true, "duration_ms": 131}
```

Markdown rendering (one line per mutating action, reads omitted unless `include_reads`; the file starts with a `# ClaudeLive session <date> <time>` header; tool name padded to 20 columns; times are local clock time, JSONL `ts` is UTC):

```
14:03:22  set_parameter         Bass › Wavetable › Filter Freq : 800 Hz → 1.20 kHz   — Open the filter so the bass cuts through the pad
```

Rules:
- Reads are recorded in JSONL (for debugging) but not in Markdown.
- `resolved` names come from the protocol response where available (e.g. `TrackSummary.name`); the server does not issue extra reads just to resolve names.
- Failures are recorded with `ok: false` and the error message.
- Nothing is ever sent off the machine.
- Names from the set (tracks, clips, devices, browser items) are truncated to 200 characters before recording. The in-memory session history keeps the last 2000 entries; the files keep everything.
- The history directory is created with mode 0700.

## Environment variables (server)

| Var | Default | Purpose |
|---|---|---|
| `CLAUDE_LIVE_HOST` | `127.0.0.1` | Script host. Only loopback addresses are accepted; anything else is ignored with a warning surfaced by `ableton_status`. |
| `CLAUDE_LIVE_PORT` | `9892` | Script port (must match `config.json` in the Remote Script) |
| `CLAUDE_LIVE_HOME` | `~/.claude-live` | History, logs, API dumps, journal. Must resolve to an absolute path; relative values are ignored with a warning. |
| `CLAUDE_LIVE_LOG_LEVEL` | `INFO` | Server log level (stderr + `$CLAUDE_LIVE_HOME/logs/server.log`) |
