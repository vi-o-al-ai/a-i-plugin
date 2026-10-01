---
name: ableton-live
description: Operating manual for driving Ableton Live 12 through the ableton-live MCP tools (ableton_status, get_session, create_clip, add_notes, set_parameter, load_device, set_automation, select, etc.). Load whenever the user wants anything done or inspected inside Live: tracks, clips, notes, devices, parameters, mixer, sends, scenes, arrangement, automation or transport, or before any mcp__ableton-live tool call. Covers the session-start ritual, addressing and value conventions, beat math, the write-then-verify loop, confirm/undo safety, the why field, error recovery and step-by-step recipes.
---

# Ableton Live: tool operating manual

Read this before touching any `ableton-live` tool. Devices and their parameters are in the
`live-devices` skill; note-writing recipes are in `midi-writing`. Quick lookups:
[reference/tool-cheatsheet.md](reference/tool-cheatsheet.md), [reference/errors.md](reference/errors.md).

## 1. Session start ritual

1. Call `ableton_status`. It never raises; check `connected`.
2. If `connected: false`, relay `diagnosis` and tell the user the exact fix, then **stop**:
   - Is Live 12 running with a set open?
   - Preferences → Link, Tempo & MIDI → Control Surface: is **ClaudeLive** selected in a slot?
   - Port: `CLAUDE_LIVE_PORT` (server, default 9892) must equal `port` in the Remote Script's `config.json`.
   - If Live is open but silent: dismiss any modal dialog (save prompt, plug-in window, crash report).
3. Once connected, call `get_session(include_devices=true, include_clips=true, include_params=false)`
   before the first mutation. Keep the result as your map of names → indices.
4. Re-read (`get_session`, or `get_track` for one track) whenever the user says they changed
   something by hand, after you create/delete/reorder tracks, scenes or devices, and whenever a
   `NOT_FOUND` error arrives. Indices shift; names do not.

## 2. Addressing (PROTOCOL.md §5)

| Thing | How to address it |
|---|---|
| Track | `track` = index into regular tracks (groups included; returns/master excluded). `track_type="return"` → index into return tracks; `track_type="master"` → `track` ignored. |
| Scene / slot | `scene` and `slot` share one numbering: slot *n* on a track sits in scene *n*. |
| Clip | Session: `track` + `slot`. Arrangement: `track` + `arrangement_index`. Give exactly one. |
| Device | `device_path` string: `"0"` = first device; `"0/1/2"` = device 0 → chain 1 → device 2 (racks). `"mixer"` = the track mixer (`Volume`, `Pan`, `Send A`, `Send B`…, `Track Activator`). |
| Parameter | `parameter` = exact name (case-insensitive) or index into `parameters`. Duplicate names → first wins, response has `ambiguous: true`; use the index then. |

Rules: always map user-facing names ("the Bass track", "the pad's reverb") to indices from the
**latest** read. Never guess an index, never assume the new track landed at the end (use the index
returned by `create_*`). `create_midi_track(index=-1)` appends; otherwise it inserts at `index`
and shifts everything after it.

## 3. Values

- **Volume / sends**: `0.0–1.0` fader range. `0.85 ≈ 0 dB`, `1.0 = +6 dB`, `0 = -inf`. Read
  back `display` for the dB value. Good defaults: new tracks 0.85, bass 0.80, pads 0.70.
- **Pan**: `-1.0` left … `0.0` centre … `1.0` right.
- **Tempo**: float BPM (`set_transport(tempo=124.0)`).
- **Colors**: `color_index` 0–69 is the only settable field; the response's `color` gives the hex so
  you can describe it ("orange").
- **Device parameters** — read before you write. `get_devices(track, device_path=..., include_params=true)`
  returns each parameter's exact `name`, `min`, `max`, `default`, `display`, `is_quantized`, `value_items`.
  Then pick one of:
  - `value` — raw units within `[min, max]` (0–1 for most knobs, but e.g. EQ gain is dB, Transpose is semitones).
  - `normalized` — 0–1 mapped onto `[min, max]`; use when you only know "about 60 % open".
  - `display` — a `value_items` string for quantized parameters (`"Lowpass"`, `"On"`, `"1/8"`). Prefer this for switches and menus.
  UI labels and LOM names differ: UI "Position" is `Osc 1 Pos`, UI "Cutoff" may be `Filter 1 Freq`.
  If a name is not found, the `NOT_FOUND` data lists `available` names; pick the closest and retry.
  Out-of-range values are clamped and the response says `clamped: true`.

## 4. Beat math

Live's beat unit is the quarter note, everywhere, regardless of time signature.

| Unit | Beats | Unit | Beats |
|---|---|---|---|
| 1 bar of 4/4 | 4.0 | 1 bar of 3/4 or 6/8 | 3.0 |
| quarter | 1.0 | dotted quarter | 1.5 |
| 8th | 0.5 | dotted 8th | 0.75 |
| 16th | 0.25 | dotted 16th | 0.375 |
| 32nd | 0.125 | quarter triplet | 0.6667 |
| 8th triplet | 0.3333 | 16th triplet | 0.1667 |

- Bar *N* (as Live's ruler shows it, 1-based) starts at arrangement time `(N-1) × bar_length`; bar 17 of 4/4 = `64.0`.
- Note `start` is relative to the clip's start (0.0), not to the song.
- Seconds per beat = `60 / tempo`. At 140 BPM a quarter is 0.4286 s; a 1/8 delay ≈ 214 ms.
- `create_clip(length=4.0)` gives `loop_start=0`, `loop_end=4.0`, `end_marker=4.0`. Notes with
  `start ≥ loop_end` are stored but **silent** until you extend the loop:
  `set_clip(loop_end=8.0, end_marker=8.0)`. `duplicate_clip_loop` doubles the loop *and* copies the notes.
- Swing: `quantize_notes(grid=0.25, swing=s)` delays every second 16th by `s × 0.125` beats.
  `s=0.2–0.4` ≈ 55–60 % MPC swing; `s=0.67` is a full triplet feel.

## 5. Write → verify loop

Every mutation gets a read-back; say what you found.

- `add_notes` / `replace_notes` → `get_notes` and check `count` and that min/max `start` and pitch
  match your intent. Off-by-one bars and notes beyond `loop_end` are the common bugs.
- `set_parameter` → the response carries `parameter.display` and `previous`; quote the display
  ("Filter Freq: 800 Hz → 2.4 kHz"). For `set_parameters`, inspect `errors` — partial success is allowed.
- `load_device(name=...)` → check `matched.name`. If it is not the device you meant, look at
  `alternatives`, delete the wrong one (`delete_device`, `confirm=true` — you loaded it this turn)
  and reload by `uri`. Prefer `category` (`"instruments"`, `"audio_effects"`, `"midi_effects"`, `"drums"`) to disambiguate.
- `create_clip` / `duplicate_clip` → use the returned `ClipSummary` (slot, length) rather than assuming.
- `set_automation` → `get_automation` if the result matters (it samples `value_at_time`).

## 6. Chunking and limits

- ≤ 500 notes per `add_notes` call is comfortable; the server splits up to 5000 and rejects more (`TOO_LARGE`).
- Big sets: call `get_session(include_clips=false)` first, then `get_track(track, include_clips=true)` for the tracks you need.
- `include_params=true` on `get_session` is heavy; read parameters per device with `get_devices(device_path=...)`.
- `browse` returns ≤ `limit` items and `truncated`; narrow `query` or `categories` instead of raising the limit.
- Reads time out at 5 s, mutations 15 s, browser/overview 60 s.

## 7. Safety

- Destructive tools (`delete_track`, `delete_scene`, `delete_clip`, `delete_device`, `clear_automation` with no parameter)
  need `confirm=true`. **Ask first** unless the user explicitly requested that exact deletion in this turn.
  Say what will be deleted (name + index) and wait.
- There is no save tool, on purpose. Never try to save; remind the user to Cmd+S when they are happy.
- Everything mutating is undoable: Live's Cmd+Z, or the `undo` tool (`steps=n`). View/selection changes are not.
- Report changes in Live terms the user can find: "Track 3 *Pad* › device 1 *Compressor* › Threshold −24 dB",
  "Scene 2 *Chorus*, slot on *Drums*". Never report only indices.
- Do not arm tracks, start recording or change `record_mode` unless asked.

## 8. The `why` field

Every mutating tool accepts `why`. Fill it on every mutating call when teaching or when the user asked
for a history. One clause, under 100 characters, musical not technical:
`why="Snare on 3 gives the half-time riddim feel"`, `why="Cut lows so the pad leaves room for the sub"`.
It is written to the session history (`get_history`), which reads as a narrative of the session.

## 9. Error recovery

| Error | Do |
|---|---|
| `NOT_FOUND` | Re-read (`get_session` / `get_track` / `get_devices`), re-map names → indices, retry once. For parameters, use `data.available`. |
| `INVALID_STATE` | Explain the state (slot occupied, audio track, not MIDI). Pick another slot/track or ask. Never delete to make room without asking. |
| `CONFIRM_REQUIRED` | Ask the user; retry with `confirm=true` only after a yes. |
| `LIVE_ERROR` | Report `detail`, retry a smaller operation (fewer notes, one parameter). |
| `TOO_LARGE` | Split the note list. |
| `UNSUPPORTED` | Feature needs a newer Live; tell the user the version it reports. |
| Timeout | Live is busy or showing a modal dialog. Ask the user to look at Live, then `ableton_status`. |
| Connection refused | Live not running or ClaudeLive not selected as Control Surface. See §1. |

Details in [reference/errors.md](reference/errors.md).

## 10. Recipes (tool sequences)

**New MIDI track with an instrument**
1. `create_midi_track(name="Lead")` → note returned `index`.
2. `load_device(name="Wavetable", track=index, category="instruments")` → verify `matched`.
3. `get_devices(track=index, device_path="0", include_params=true)` → learn parameter names before shaping the sound.
4. `select(track=index, device_path="0", show_device_detail=true)` so the user sees it.

**1-bar drum loop in a new clip**
1. Find or create a Drum Rack track; `get_devices(track, device_path="0")` → `drum_pads` tells you which pitch is kick/snare/hat.
2. `create_clip(track, slot, length=4.0, name="Drums 1")`.
3. `add_notes(track, slot, notes=[...])` (patterns in `midi-writing/drums.md`).
4. `get_notes` → check count. 5. `fire_clip` and ask how it feels.

**Sidechain compressor on a pad, keyed from the kick**
1. `load_device(name="Compressor", track=pad, category="audio_effects")`.
2. Tell the user the one step the API cannot do in v1: open the Compressor, click the ▸ to show the
   Sidechain section, turn **Audio From** on and choose the kick track (or the Drum Rack's kick chain,
   "Post FX") in the dropdown. Wait for them to confirm.
3. `set_parameters(track=pad, device_path=<comp>, values=[{"parameter":"Threshold","value":...}, {"parameter":"Ratio",...}, {"parameter":"Attack",...}, {"parameter":"Release",...}])`
   — read the parameter list first; ranges and recipe in `live-devices/effects/compressor.md`.
4. `play`, ask them to listen for the pump; adjust Release to the groove.

**Scene-based song skeleton**
1. `create_scene(name="Intro")`, `"Verse"`, `"Pre"`, `"Chorus"`, `"Break"`, `"Drop"` … (`index=-1` appends in order).
2. Write the core clips in the first scene that uses them.
3. `duplicate_clip(track, slot=src, target_slot=dst)` into later scenes, then vary (`transpose_notes`, `remove_notes` by range, `add_notes`).
4. `set_scene(scene, color_index=...)` to colour sections; `fire_scene` to audition.

**Move a session clip into the arrangement at bar N**
1. `time = (N-1) × 4.0` (4/4). 2. `add_clip_to_arrangement(track, slot, time=time)`.
3. Repeat per track; `set_locator(time, name="Drop")` to mark sections; `show_view("Arranger")`.

**Filter sweep over a 4-bar build**
1. Read the parameter (`get_devices(..., include_params=true)`) to get its `min`/`max` and name (e.g. Auto Filter `Frequency`).
2. The clip must be 16 beats long (`set_clip(loop_end=16.0, end_marker=16.0)` or create it so).
3. `set_automation(track, slot, device_path, parameter="Frequency", points=[{"time":0.0,"value":<low>},{"time":16.0,"value":<high>}], mode="ramp")`.
   Values are raw parameter units; use the read `min`/`max` as bounds. The last point holds to clip end.
4. `fire_clip`, ask the user to listen, then `get_automation` if you need to confirm.

**A/B a parameter**
1. Read current `value`/`display`. 2. `set_parameter` to the candidate; `play`; ask the user to listen.
3. `set_parameter` back to the previous `value`; ask again. 4. Keep whichever they prefer and say which it was.

## 11. View etiquette for teaching

- `select(track=…, slot=…, show_clip_detail=true)` before talking about a clip; `select(track=…, device_path=…, show_device_detail=true)` before a device.
- `show_view("Session")` for clips/scenes, `"Arranger"` for timeline work, `"Detail/Clip"` for notes, `"Detail/DeviceChain"` for parameters, `"Browser"` when you want them to see the browser.
- Selection changes are recorded but not undoable, so use them freely. Fill `why` so the history shows what you were pointing at.
