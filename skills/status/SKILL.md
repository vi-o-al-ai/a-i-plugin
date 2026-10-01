---
name: status
description: Show whether Ableton Live is reachable and print a compact summary of the open set (tempo, key, tracks with instruments, scenes, selection).
disable-model-invocation: true
allowed-tools:
  - mcp__plugin_ableton-live_live__ableton_status
  - mcp__plugin_ableton-live_live__get_session
---

# Live status

This command is read-only. Never call a tool that changes the set, the transport or the view while running it.

1. Call `ableton_status`.
   - If `connected` is false: print the `diagnosis` and troubleshooting steps from the result in two or three lines, suggest `/ableton-live:setup`, and stop.
2. Call `get_session` with `include_clips=false` and `include_params=false` (keep `include_devices=true` and `include_returns=true`).
3. Print one compact block, with no preamble, shaped like this:

```
Live 12.1.5 · ClaudeLive 0.1.0 · 14 ms round trip
124 BPM · 4/4 · C Minor · stopped at bar 1
Tracks (4)
  0 Drums   [Drum Rack]               3 clips
  1 Bass    [Wavetable → Saturator]   2 clips   armed
  2 Pad     [Operator]                1 clip    muted
  3 Vocal   (audio)                   0 clips
Returns: A Reverb · B Delay          Scenes: 8
Selected: track 1 Bass · scene 0 Intro · clip "Bass 1"
```

Rules:
- Tempo and time signature come from `transport`; the key from `scale` (`root_name` + `scale_name`), or `no scale set` when it is null. Show `playing`/`stopped` from `is_playing` and convert `position` (beats) to a bar number using the time signature.
- One line per track: index, name, the instrument device (`type == "instrument"`) in brackets, followed by the audio effects after `→` when there are at most two (otherwise `+N fx`); write `(audio)` for audio tracks and `(group)` for group tracks. Add `armed`, `muted`, `solo` only when set. Use `clip_count` for the clip count, since clips were not fetched.
- Then the return track names, the scene count, and the `selection` (track, scene, detail clip, device when present).
- Skip master-track devices unless the user asks.
