# Tool cheatsheet (55 tools, from docs/TOOLS.md)

Flags: **M** mutating (recorded, undoable) · **D** destructive (`confirm=true`) · **UI** view-only (recorded, not undoable) · **R** read-only.
Every mutating tool also accepts `why: str` (history only). Clip address = `track` + exactly one of `slot` / `arrangement_index`.
`track_type` is `"track"` (default) | `"return"` | `"master"`.

## Status and diagnostics
- `ableton_status()` — R. Is Live reachable? Versions, round-trip ms, history paths; `connected: false` + `diagnosis` on failure (never raises).
- `ableton_describe_api(path?)` — R (writes a file). Dump the real Live API from inside Live for debugging.
- `get_history(limit=50, include_reads=false)` — R. This session's recorded actions (most recent last) and history file paths.

## Session and transport
- `get_session(include_clips=true, include_devices=true, include_params=false, include_returns=true)` — R. Whole set: transport, scale, tracks (+clips, devices), returns, master, scenes, selection. Heavy with `include_params`.
- `get_transport()` — R. Tempo, signature, playing, position, loop, metronome, record flags, song_length.
- `set_transport(tempo?, metronome?, loop_enabled?, loop_start?, loop_length?, position?, record_mode?, session_record?, signature_numerator?, signature_denominator?)` — M.
- `play(from_start=false)` — M. `stop()` — M. `continue_playing()` — M.
- `set_scale(root_note?: int|"C".."B", scale_name?)` — M. Live 12 only; bad name → error with `available`.
- `undo(steps=1)` — M. `redo(steps=1)` — M.

## Tracks
- `get_track(track, track_type?, include_clips=true, include_devices=true, include_params=false)` — R.
- `create_midi_track(name?, index=-1)` — M. Returns TrackSummary with the new `index`.
- `create_audio_track(name?, index=-1)` — M.
- `create_return_track(name?)` — M.
- `set_track(track, track_type?, name?, color_index?, mute?, solo?, arm?, volume?, pan?, sends?: [{index, value}], fold?)` — M. `arm` on an un-armable track → INVALID_STATE.
- `delete_track(track, confirm)` — M D.

## Scenes
- `create_scene(name?, index=-1)` — M.
- `set_scene(scene, name?, color_index?, tempo?)` — M.
- `fire_scene(scene)` — M.
- `duplicate_scene(scene)` — M. Returns the new scene.
- `delete_scene(scene, confirm)` — M D.

## Clips
- `create_clip(track, slot, length=4.0, name?)` — M. INVALID_STATE if slot occupied or track is audio.
- `get_clip(track, slot? | arrangement_index?)` — R.
- `set_clip(track, slot? | arrangement_index?, name?, color_index?, loop_start?, loop_end?, looping?, start_marker?, end_marker?, launch_quantization?)` — M. Applied in order looping, loop_end, loop_start, end_marker, start_marker.
- `fire_clip(track, slot)` — M. Empty slot acts as a stop button.
- `stop_clip(track, slot?)` — M. Without `slot`, stops all clips on the track.
- `duplicate_clip(track, slot, target_slot, target_track?)` — M. INVALID_STATE if target occupied.
- `duplicate_clip_loop(track, slot)` — M. Doubles loop length and copies content.
- `delete_clip(track, slot? | arrangement_index?, confirm)` — M D.

## Notes
Note item: `{pitch, start, duration, velocity=100, mute=false, probability=1.0, velocity_deviation=0.0, release_velocity=64}`. Server chunks at 500, splits up to 5000 per call.
- `get_notes(track, slot? | arrangement_index?, from_time?, time_span?, from_pitch?, pitch_span?)` — R. Sorted by start then pitch; returns `notes`, `count`, `clip_length`.
- `add_notes(track, slot? | arrangement_index?, notes)` — M. Returns `added`, `note_count`.
- `replace_notes(track, slot? | arrangement_index?, notes)` — M. Removes all, then adds.
- `remove_notes(track, slot? | arrangement_index?, note_ids?, from_time?, time_span?, from_pitch?, pitch_span?)` — M. No filters = remove all.
- `modify_notes(track, slot? | arrangement_index?, changes: [{id, pitch?, start?, duration?, velocity?, mute?, probability?, velocity_deviation?, release_velocity?}])` — M. In place by id.
- `quantize_notes(track, slot? | arrangement_index?, grid=0.25, amount=1.0, swing=0.0)` — M. `swing` 0–1 delays every second grid step by up to half a grid.
- `transpose_notes(track, slot? | arrangement_index?, semitones, from_time?, time_span?, from_pitch?, pitch_span?)` — M. Clamped to 0–127.

## Devices and parameters
- `get_devices(track, track_type?, device_path?, include_params=false, depth=2)` — R. No path: list of devices + `mixer` parameters. With path: one DeviceDetail (parameters, chains, drum_pads).
- `set_parameter(track, device_path, parameter, value? | normalized? | display?, track_type?)` — M. Exactly one of value/normalized/display. Returns `parameter`, `previous`, `clamped`.
- `set_parameters(track, device_path, values: [{parameter, value? | normalized? | display?}], track_type?)` — M. Partial success; check `errors`.
- `set_device_enabled(track, device_path, enabled, track_type?)` — M. Via `Device On`.
- `delete_device(track, device_path, confirm, track_type?)` — M D.

## Browser
Categories: `instruments`, `sounds`, `drums`, `audio_effects`, `midi_effects`, `plugins`, `max_for_live`, `packs`, `user_library`, `samples`, `clips`.
- `browse(query?, categories?, uri?, limit=25, loadable_only=true)` — R. Search by `query` (exact → prefix → substring), or list children of `uri`/category. Returns `items` (`name`, `uri`, `category`, `path`, `is_loadable`, `is_device`), `truncated`.
- `load_device(uri? | name?, track, track_type?, after_device_path?, category?)` — M. With `name`, searches then loads the best match; returns `loaded`, `matched`, `alternatives`.

## Arrangement
- `get_arrangement(include_clips=true)` — R. song_length, loop, locators, per-track arrangement clips with start_time/end_time.
- `add_clip_to_arrangement(track, slot, time, delete_source=false)` — M. Copies a session clip to song-beat `time`.
- `set_locator(time, name?)` — M. Creates (or renames) a locator at `time`.
- `delete_locator(index)` — M.

## Automation
`device_path` may be `"mixer"`. Session clips in v1 (arrangement clips where Live allows).
- `get_automation(track, slot? | arrangement_index?, device_path, parameter, from_time?, time_span?, resolution=0.25)` — R. Samples the envelope; `exists`, `points`, `parameter`.
- `set_automation(track, slot? | arrangement_index?, device_path, parameter, points: [{time, value}], mode="ramp" | "steps", resolution=0.0625)` — M. Raw parameter units; last point holds to clip end.
- `clear_automation(track, slot? | arrangement_index?, device_path?, parameter?, confirm=false)` — M (D when clearing all envelopes).

## View
- `get_selection()` — R. Selected track, scene, clip slot, detail clip, device, parameter.
- `select(track?, track_type?, scene?, slot?, device_path?, show_clip_detail?, show_device_detail?)` — UI. Selecting a slot also selects its track and scene.
- `show_view(view: "Session" | "Arranger" | "Detail/Clip" | "Detail/DeviceChain" | "Browser")` — UI.
