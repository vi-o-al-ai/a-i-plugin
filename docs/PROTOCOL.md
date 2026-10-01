# ClaudeLive wire protocol

This document is the contract between the two halves of the plugin:

- **ClaudeLive Remote Script** — runs inside Ableton Live 12 (embedded Python 3.11, stdlib only). Owns a TCP listener on localhost and executes every Live Object Model (LOM) call on Live's main thread.
- **ableton-live-mcp** — the MCP server launched by Claude Code on the same machine. A thin client that turns MCP tool calls into protocol requests.

Both are built from this file. If the code and this file disagree, fix one of them.

## 1. Transport

| Item | Value |
|---|---|
| Transport | TCP, `127.0.0.1` only. Never bind to other interfaces. |
| Default port | `9892` (override via `remote-script/ClaudeLive/config.json` and `CLAUDE_LIVE_PORT` on the server side; both must match) |
| Framing | Newline-delimited JSON. One message per line, terminated by `\n`. UTF-8. A message never contains a raw newline (standard `json.dumps` output). |
| Max line | 4 MiB. Longer lines are rejected with `-32600` and the connection stays open. |
| Clients | Multiple concurrent connections allowed. Each connection has its own request-id space. Requests from all connections are executed in arrival order on Live's main thread. |
| Keep-alive | None required. A client may hold one connection for its lifetime. The script tolerates abrupt disconnects. |

## 2. Message format — JSON-RPC 2.0

Request:

```json
{"jsonrpc": "2.0", "id": 7, "method": "notes.add", "params": {"track": 2, "slot": 0, "notes": [...]}}
```

Success:

```json
{"jsonrpc": "2.0", "id": 7, "result": {"added": 16, "note_count": 16}}
```

Error:

```json
{"jsonrpc": "2.0", "id": 7, "error": {"code": -32000, "message": "Track 9 does not exist (set has 4 tracks)", "data": {"kind": "track", "index": 9, "count": 4}}}
```

Rules:

- `id` is an integer or string chosen by the client. Responses echo it exactly.
- `params` is always a JSON object (named parameters). Missing optional params take the documented defaults.
- `result` is always a JSON object (never a bare scalar or array) so fields can be added later without breaking clients.
- Notifications (requests without `id`) are reserved for a future event stream. The v1 script ignores them.
- Batch arrays are not supported in v1.

## 3. Error codes

Standard JSON-RPC codes:

| Code | Meaning |
|---|---|
| -32700 | Parse error (invalid JSON on the line) |
| -32600 | Invalid request (not an object, missing `method`, bad `jsonrpc`, line too long) |
| -32601 | Method not found |
| -32602 | Invalid params (wrong type, out of range value, missing required param) |
| -32603 | Internal error in the script itself (bug) |

Application codes:

| Code | Name | When | `data` |
|---|---|---|---|
| -32000 | `NOT_FOUND` | A track, scene, slot, clip, device, chain, parameter, cue point or browser item does not exist | `{"kind": "track", "index": 9, "count": 4}` or `{"kind": "parameter", "name": "Cutoff", "available": [...]}` |
| -32001 | `INVALID_STATE` | Object exists but the operation does not apply: slot has no clip, clip is audio not MIDI, track cannot be armed, slot already has a clip, device has no chains | `{"reason": "slot_empty"}` etc. |
| -32002 | `CONFIRM_REQUIRED` | A destructive method was called without `"confirm": true` | `{"method": "song.delete_track", "target": "Bass (track 2)"}` |
| -32003 | `UNSUPPORTED` | The installed Live version lacks the API needed | `{"needs": "Live 12", "have": "11.3.4"}` |
| -32004 | `LIVE_ERROR` | The LOM raised an exception | `{"exception": "RuntimeError", "detail": "..."}` |
| -32005 | `TOO_LARGE` | Request exceeds a batch limit (e.g. > 1000 notes in one `notes.add`) | `{"limit": 1000, "got": 2400}` |
| -32006 | `TIMEOUT` | Browser traversal or another bounded operation hit its internal time/node budget before finishing. Partial results are NOT returned via error; see `browser.search` which returns `truncated: true` instead. Reserved. | |

`message` is always a human-readable sentence that Claude can act on. Prefer "Track 9 does not exist (set has 4 tracks)" over "index error".

## 4. Threading model (script side)

1. A daemon thread owns the listening socket, accepts connections, reads lines, parses JSON, and pushes `(connection, request)` onto a thread-safe queue. It never touches the LOM.
2. A recurring main-thread tick (scheduled via the ControlSurface framework, ~100 ms period) drains the queue, dispatches each request to its handler, and writes the response line back to the connection. Only this path touches the LOM.
3. Per tick, the drain loop processes at most `MAX_REQUESTS_PER_TICK` (default 32) requests and stops early if it has spent more than `MAX_TICK_MS` (default 50 ms), so Live's UI never stalls. Remaining requests wait for the next tick.
4. Any exception inside a handler is caught and converted to a JSON-RPC error. An exception in the tick loop itself is logged and the tick is rescheduled; the script never dies silently.
5. On `disconnect()` the socket is closed and all client connections are dropped.

Expected latency: one tick (~100 ms) plus handler time. Clients should budget accordingly (see §8).

## 5. Addressing conventions

| Concept | Convention |
|---|---|
| Track | `"track": <int>` indexes `song.tracks` (regular tracks including group tracks; excludes returns and master). Optional `"track_type": "track" \| "return" \| "master"` (default `"track"`). For `"return"`, `track` indexes `song.return_tracks`. For `"master"`, `track` is ignored. |
| Scene / slot | `"scene": <int>` indexes `song.scenes`. `"slot": <int>` indexes `track.clip_slots` (same numbering as scenes). |
| Clip | Session clip: `track` + `slot`. Arrangement clip: `track` + `"arrangement_index": <int>` into `track.arrangement_clips`. Exactly one of `slot` / `arrangement_index` must be given where a clip is addressed. |
| Device path | String of `/`-separated integers alternating device index and chain index, starting at the track's device list: `"0"` = `track.devices[0]`; `"0/1/2"` = `track.devices[0].chains[1].devices[2]`; `"0/1/2/0/0"` goes one level deeper. The special path `"mixer"` addresses the track's mixer device (parameters `Volume`, `Pan`, `Send A`, `Send B`, …, `Track Activator`). |
| Parameter | `"parameter": <int \| string>` — index into `device.parameters`, or a case-insensitive exact match on `parameter.name` (then `original_name`). If several share a name, the first wins and the response includes `"ambiguous": true`. |
| Time | Beats as float. Note times are relative to clip start. Arrangement times and the playhead are in song beats from 0. `1 bar at 4/4 = 4.0`. |
| Pitch | MIDI note number 0–127. |
| Velocity | 1–127 (float accepted, stored as Live stores it). |
| Volume / sends | Normalized `0.0–1.0` (Live's fader range; `0.85 ≈ 0 dB`, `1.0 = +6 dB`). Responses always include `display` (e.g. `"-6.0 dB"`) from Live. |
| Pan | `-1.0` (left) to `1.0` (right). |
| Color | `"color_index": 0–69` (Live palette index) is the settable field. Responses also include `"color": "#RRGGBB"`. |
| Confirm | Destructive methods require `"confirm": true` or fail with `-32002`. |

Index validation: every index is checked before use and produces `NOT_FOUND` with `count` so the client can self-correct.

## 6. Common result fragments

These shapes are reused across methods.

```jsonc
// TrackSummary
{"index": 2, "track_type": "track", "name": "Bass", "type": "midi",      // "midi" | "audio" | "group" | "return" | "master"
 "color_index": 14, "color": "#FF9A00",
 "mute": false, "solo": false, "arm": true, "can_be_armed": true,
 "is_foldable": false, "is_grouped": false, "group_track_index": null,
 "volume": {"value": 0.85, "display": "0.0 dB"}, "pan": {"value": 0.0, "display": "C"},
 "sends": [{"index": 0, "name": "A-Reverb", "value": 0.0, "display": "-inf dB"}],
 "playing_slot_index": -1, "fired_slot_index": -1,
 "clip_count": 3, "device_count": 2}

// ClipSummary
{"track": 2, "slot": 0, "arrangement_index": null,
 "name": "Bass 1", "color_index": 14, "color": "#FF9A00",
 "is_midi": true, "is_audio": false, "is_arrangement_clip": false,
 "length": 4.0, "loop_start": 0.0, "loop_end": 4.0, "looping": true,
 "start_marker": 0.0, "end_marker": 4.0,
 "start_time": null, "end_time": null,                 // arrangement clips only (song beats)
 "is_playing": false, "is_recording": false, "is_triggered": false,
 "signature_numerator": 4, "signature_denominator": 4,
 "note_count": 16}                                     // MIDI clips only; null for audio

// Note
{"id": 1234, "pitch": 60, "start": 0.0, "duration": 0.5, "velocity": 100,
 "mute": false, "probability": 1.0, "velocity_deviation": 0.0, "release_velocity": 64}

// NoteSpec (input to notes.add / notes.replace) — id is ignored if present
{"pitch": 60, "start": 0.0, "duration": 0.5, "velocity": 100,              // velocity default 100
 "mute": false, "probability": 1.0, "velocity_deviation": 0.0, "release_velocity": 64}

// DeviceSummary
{"path": "0", "name": "Wavetable", "class_name": "InstrumentVector", "class_display_name": "Wavetable",
 "type": "instrument",                                 // "instrument" | "audio_effect" | "midi_effect" | "unknown"
 "is_active": true, "is_rack": false, "can_have_drum_pads": false,
 "chain_count": 0, "parameter_count": 93}

// DeviceDetail = DeviceSummary + 
{"parameters": [Parameter...],
 "chains": [{"index": 0, "name": "Kick", "devices": [DeviceSummary...]}],   // racks only
 "drum_pads": [{"note": 36, "name": "Kick 909", "has_chain": true}]}        // drum racks only

// Parameter
{"index": 5, "name": "Filter Freq", "original_name": "Filter Freq",
 "value": 0.62, "min": 0.0, "max": 1.0, "default": 0.5,
 "display": "1.20 kHz", "is_quantized": false, "value_items": null,        // value_items: [str] when quantized
 "is_enabled": true, "automation_state": "none"}                           // "none" | "playing" | "overridden"

// SceneSummary
{"index": 0, "name": "Intro", "color_index": 0, "color": "#...", "is_triggered": false, "tempo": null, "is_empty": false}

// Selection
{"track": {"index": 2, "track_type": "track", "name": "Bass"},
 "scene": {"index": 0, "name": "Intro"},
 "clip_slot": {"track": 2, "slot": 0, "has_clip": true, "clip_name": "Bass 1"},
 "detail_clip": {"track": 2, "slot": 0, "name": "Bass 1"} ,                // or null
 "device": {"path": "0", "name": "Wavetable"},                              // or null
 "parameter": {"name": "Filter Freq", "device_path": "0"}}                 // or null

// Transport
{"tempo": 124.0, "signature_numerator": 4, "signature_denominator": 4,
 "is_playing": false, "position": 0.0,
 "loop": {"enabled": false, "start": 0.0, "length": 16.0},
 "metronome": false, "record_mode": false, "session_record": false,
 "song_length": 128.0}                                                     // last arrangement clip end, beats

// Scale (Live 12)
{"root_note": 0, "root_name": "C", "scale_name": "Minor", "scale_intervals": [0,2,3,5,7,8,10]}

// CuePoint (locator)
{"index": 0, "name": "Drop", "time": 64.0}
```

## 7. Methods

Namespaces: `sys`, `song`, `view`, `track`, `scene`, `clip`, `notes`, `device`, `browser`, `arrangement`, `automation`.
**M** = mutates the set (recorded in history, undoable). **D** = destructive, requires `confirm: true`. **UI** = changes view/selection only (recorded, not undoable).

### sys

| Method | Params | Result | Notes |
|---|---|---|---|
| `sys.ping` | — | `{"script_version", "protocol_version": 1, "live_version": "12.1.5", "live_major": 12, "live_minor": 1, "python_version", "tick_count"}` | Handshake. |
| `sys.describe_api` | `{"path"?: str, "classes"?: [str]}` | `{"path": "...", "classes": 42, "bytes": 12345}` | Introspects the `Live` module (and `_Framework.ControlSurface`) via `dir()`/`__doc__` and writes a Markdown dump to `path` (default: `<script dir>/live_api_dump.md`). Ground truth for debugging. |
| `sys.log` | `{"message": str}` | `{"ok": true}` | Writes `[ClaudeLive] message` to Live's Log.txt. |

### song

| Method | Params | Result | Flags |
|---|---|---|---|
| `song.get_overview` | `{"include_clips"?: true, "include_devices"?: true, "include_params"?: false, "include_returns"?: true}` | `{"transport": Transport, "scale": Scale\|null, "tracks": [TrackSummary + "clips": [ClipSummary], "devices": [DeviceSummary]], "return_tracks": [...], "master": TrackSummary + devices, "scenes": [SceneSummary], "selection": Selection, "live_version": str}` | Heavy; `include_params` adds `parameters` to each device. |
| `song.get_transport` | — | `Transport` | |
| `song.set_transport` | `{"tempo"?, "metronome"?, "loop_enabled"?, "loop_start"?, "loop_length"?, "record_mode"?, "session_record"?, "position"?, "signature_numerator"?, "signature_denominator"?}` | `Transport` | **M** (position/metronome changes are not undoable but recorded) |
| `song.play` | `{"from_start"?: false}` | `Transport` | `start_playing()`; with `from_start`, set position 0 first. |
| `song.stop` | — | `Transport` | `stop_playing()` |
| `song.continue` | — | `Transport` | `continue_playing()` |
| `song.stop_all_clips` | — | `{"ok": true}` | |
| `song.get_scale` | — | `Scale` | `UNSUPPORTED` below Live 12. |
| `song.set_scale` | `{"root_note"?: 0-11 \| "C".."B", "scale_name"?: str}` | `Scale` | **M**. Invalid scale name → `-32602` with `available` list. |
| `song.undo` | — | `{"ok": true}` | |
| `song.redo` | — | `{"ok": true}` | |
| `song.create_midi_track` | `{"index"?: -1, "name"?: str}` | `TrackSummary` | **M** |
| `song.create_audio_track` | `{"index"?: -1, "name"?: str}` | `TrackSummary` | **M** |
| `song.create_return_track` | `{"name"?: str}` | `TrackSummary` | **M** |
| `song.delete_track` | `{"track", "confirm"}` | `{"deleted": "Bass", "track_count": 3}` | **M D** |
| `song.create_scene` | `{"index"?: -1, "name"?: str}` | `SceneSummary` | **M** |
| `song.duplicate_scene` | `{"scene"}` | `SceneSummary` (the new scene) | **M** |
| `song.delete_scene` | `{"scene", "confirm"}` | `{"deleted": "Intro", "scene_count": 7}` | **M D** |

### view

| Method | Params | Result | Flags |
|---|---|---|---|
| `view.get_selection` | — | `Selection` | |
| `view.select` | `{"track"?, "track_type"?, "scene"?, "slot"?, "device_path"?, "show_clip_detail"?: bool, "show_device_detail"?: bool}` | `Selection` | **UI**. Selecting a slot also selects its track and scene. |
| `view.show_view` | `{"view": "Session" \| "Arranger" \| "Detail/Clip" \| "Detail/DeviceChain" \| "Browser"}` | `{"view": ..., "visible": true}` | **UI** |

### track

| Method | Params | Result | Flags |
|---|---|---|---|
| `track.get` | `{"track", "track_type"?, "include_clips"?: true, "include_devices"?: true, "include_params"?: false}` | `TrackSummary + clips + devices` | |
| `track.set` | `{"track", "track_type"?, "name"?, "color_index"?, "mute"?, "solo"?, "arm"?, "volume"?, "pan"?, "sends"?: [{"index", "value"}], "fold"?: bool}` | `TrackSummary` | **M**. Rejects `arm` on tracks that cannot be armed with `INVALID_STATE`. |
| `track.stop_clips` | `{"track"}` | `{"ok": true}` | **M** |

### scene

| Method | Params | Result | Flags |
|---|---|---|---|
| `scene.set` | `{"scene", "name"?, "color_index"?, "tempo"?: float\|null}` | `SceneSummary` | **M** |
| `scene.fire` | `{"scene"}` | `SceneSummary` | **M** |

### clip

Clip address = `track` + (`slot` | `arrangement_index`).

| Method | Params | Result | Flags |
|---|---|---|---|
| `clip.create` | `{"track", "slot", "length": float, "name"?}` | `ClipSummary` | **M**. `INVALID_STATE` if slot occupied or track is audio. |
| `clip.get` | `{clip address}` | `ClipSummary` | |
| `clip.set` | `{clip address, "name"?, "color_index"?, "loop_start"?, "loop_end"?, "looping"?, "start_marker"?, "end_marker"?, "launch_quantization"?}` | `ClipSummary` | **M**. Order of application: `looping`, `loop_end`, `loop_start`, `end_marker`, `start_marker` (Live rejects loop_start ≥ loop_end). |
| `clip.fire` | `{"track", "slot"}` | `ClipSummary \| {"fired_empty_slot": true}` | **M**. Fires the slot (works on empty slots as a stop button). |
| `clip.stop` | `{"track", "slot"?}` | `{"ok": true}` | **M**. Without `slot`, stops all clips on the track. |
| `clip.duplicate` | `{"track", "slot", "target_track"?: same, "target_slot"}` | `ClipSummary` (the copy) | **M**. `INVALID_STATE` if target occupied. |
| `clip.duplicate_loop` | `{"track", "slot"}` | `ClipSummary` | **M**. Doubles clip loop content (`Clip.duplicate_loop`). |
| `clip.delete` | `{clip address, "confirm"}` | `{"deleted": "Bass 1"}` | **M D** |

### notes

All take a clip address; `INVALID_STATE` if the clip is not MIDI. `notes.add`/`notes.replace` limit 1000 notes per request (`TOO_LARGE`).

| Method | Params | Result | Flags |
|---|---|---|---|
| `notes.get` | `{clip address, "from_time"?: 0, "time_span"?: clip loop_end or 1e6, "from_pitch"?: 0, "pitch_span"?: 128}` | `{"notes": [Note], "count", "clip_length"}` | Sorted by start then pitch. |
| `notes.add` | `{clip address, "notes": [NoteSpec]}` | `{"added", "note_count"}` | **M** |
| `notes.replace` | `{clip address, "notes": [NoteSpec]}` | `{"removed", "added", "note_count"}` | **M**. Removes all notes, then adds. |
| `notes.remove` | `{clip address, "note_ids"?: [int], "from_time"?, "time_span"?, "from_pitch"?, "pitch_span"?}` | `{"removed", "note_count"}` | **M**. With `note_ids`, removes exactly those. Otherwise removes the range (defaults = all). |
| `notes.modify` | `{clip address, "changes": [{"id", "pitch"?, "start"?, "duration"?, "velocity"?, "mute"?, "probability"?, "velocity_deviation"?, "release_velocity"?}]}` | `{"modified", "missing_ids": []}` | **M**. In place via note ids. |
| `notes.quantize` | `{clip address, "grid": 0.25, "amount": 1.0, "swing"?: 0.0, "quantize_ends"?: false}` | `{"modified"}` | **M**. Implemented via `notes.modify` semantics in the script. `swing` 0–1 delays every second grid step by up to half a grid. |
| `notes.transpose` | `{clip address, "semitones": int, "from_time"?, "time_span"?, "from_pitch"?, "pitch_span"?}` | `{"modified"}` | **M**. Clamps to 0–127. |

### device

| Method | Params | Result | Flags |
|---|---|---|---|
| `device.list` | `{"track", "track_type"?, "include_params"?: false, "depth"?: 2}` | `{"devices": [DeviceSummary or DeviceDetail], "mixer": {"path": "mixer", "parameters": [Parameter]}}` | `depth` limits rack recursion. |
| `device.get` | `{"track", "track_type"?, "path", "include_params"?: true}` | `DeviceDetail` | |
| `device.get_parameter` | `{"track", "track_type"?, "path", "parameter"}` | `Parameter` | |
| `device.set_parameter` | `{"track", "track_type"?, "path", "parameter", "value"?: float, "normalized"?: 0..1, "display"?: str}` | `{"parameter": Parameter, "previous": {"value", "display"}, "clamped": bool}` | **M**. Exactly one of `value` / `normalized` / `display`. `display` matches `value_items` for quantized params (case-insensitive) or fails `-32602`. Values outside `[min,max]` are clamped and reported. |
| `device.set_parameters` | `{"track", "track_type"?, "path", "values": [{"parameter", "value"? , "normalized"?, "display"?}]}` | `{"results": [... as above ...], "errors": [{"parameter", "code", "message"}]}` | **M**. Partial success allowed. |
| `device.set_enabled` | `{"track", "track_type"?, "path", "enabled": bool}` | `{"is_active": bool}` | **M**. Via the `Device On` parameter. |
| `device.delete` | `{"track", "track_type"?, "path", "confirm"}` | `{"deleted": "Reverb"}` | **M D** |

### browser

Categories: `instruments`, `sounds`, `drums`, `audio_effects`, `midi_effects`, `plugins`, `max_for_live`, `packs`, `user_library`, `samples`, `clips`.

| Method | Params | Result | Flags |
|---|---|---|---|
| `browser.search` | `{"query": str, "categories"?: [str] (default: instruments, drums, audio_effects, midi_effects, sounds), "limit"?: 25, "loadable_only"?: true, "max_nodes"?: 5000}` | `{"items": [{"name", "uri", "category", "path": ["Instruments","Wavetable",...], "is_loadable", "is_folder", "is_device"}], "truncated": bool, "nodes_visited"}` | Case-insensitive substring over `name`; results ordered: exact name match, then prefix, then substring. Traversal bounded by `max_nodes` and ~40 ms per tick; may span several ticks internally but returns one response. |
| `browser.list` | `{"category"?: str, "uri"?: str, "limit"?: 100}` | `{"items": [...], "truncated"}` | Children of a category root or of the node with `uri`. |
| `browser.load` | `{"uri": str, "track"?, "track_type"?, "after_device_path"?: str}` | `{"loaded": DeviceSummary \| null, "track": TrackSummary, "devices": [DeviceSummary], "method": "load_item"}` | **M**. Selects the target track (and device, if `after_device_path`) first, then `browser.load_item`. `loaded` is derived by diffing the device list before/after; null if the item was not a device (e.g. a clip or sample). |

### arrangement

| Method | Params | Result | Flags |
|---|---|---|---|
| `arrangement.get_overview` | `{"include_clips"?: true}` | `{"song_length", "loop": {...}, "locators": [CuePoint], "tracks": [{"index", "name", "clips": [ClipSummary (with start_time/end_time)]}]}` | The "composition view". |
| `arrangement.get_clips` | `{"track"}` | `{"clips": [ClipSummary]}` | |
| `arrangement.add_clip_from_slot` | `{"track", "slot", "time": float, "delete_source"?: false}` | `ClipSummary` (the arrangement clip) | **M**. `Track.duplicate_clip_to_arrangement`. |
| `arrangement.set_locator` | `{"time": float, "name"?: str}` | `CuePoint` | **M**. Creates a locator at `time` (or renames the one already there). |
| `arrangement.delete_locator` | `{"index"}` | `{"deleted": "Drop"}` | **M** |

### automation

`device_path` may be `"mixer"`. Session clips only in v1 (arrangement clip envelopes also work via `arrangement_index` where Live allows).

| Method | Params | Result | Flags |
|---|---|---|---|
| `automation.get` | `{clip address, "device_path", "parameter", "from_time"?: 0, "time_span"?: clip length, "resolution"?: 0.25}` | `{"exists": bool, "points": [{"time", "value"}], "parameter": Parameter}` | Samples `value_at_time`. |
| `automation.set` | `{clip address, "device_path", "parameter", "points": [{"time", "value"}], "mode"?: "steps" \| "ramp", "resolution"?: 0.0625}` | `{"inserted": int, "exists": true}` | **M**. Creates the envelope if needed. `steps`: each point holds until the next. `ramp`: linear interpolation between points, written as steps at `resolution`. Last point holds to clip end. |
| `automation.clear` | `{clip address, "device_path"?, "parameter"?, "confirm"?}` | `{"cleared": "Filter Freq" \| "all"}` | **M**. Clearing all envelopes (no parameter) requires `confirm` (**D**). |

## 8. Client guidance (MCP server side)

| Class of method | Timeout |
|---|---|
| Reads (`get_*`, `list`, `ping`) | 5 s |
| Mutations | 15 s |
| `browser.*`, `song.get_overview` with params, `sys.describe_api` | 60 s |

Connection errors must be translated into a message that names the likely cause, in this order:
1. Connection refused → "Live is not running, or the ClaudeLive control surface is not selected (Preferences → Link, Tempo & MIDI → Control Surface)."
2. Timeout → "Live is not responding. It may be showing a modal dialog, loading a set, or frozen."
3. Protocol error → include the raw line for debugging.

The client reconnects transparently on the next call after a failure.

## 9. Versioning

`protocol_version` is an integer, currently `1`. Additive changes (new methods, new optional params, new result fields) do not bump it. Renames or removals do. The MCP server checks `sys.ping` on first use and warns if versions differ.
