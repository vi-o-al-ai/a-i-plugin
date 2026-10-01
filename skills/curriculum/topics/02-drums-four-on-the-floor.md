# 02 · Drums: four-on-the-floor

**Goal.** A 4-bar synth-pop/disco drum loop at 120 BPM in a Drum Rack: kick on every beat, clap on 2 and 4, offbeat hats, open hat and a fill in bar 4, with velocities that breathe.

**Prerequisites.** 01 at confidence ≥ 1. Tempo 120 (`set_transport(tempo=120)`).

**Terms.** Drum Rack, pad, four-on-the-floor, backbeat, offbeat, velocity, fill.

## Reference pattern (per bar; beats as `start`)

| Element | Pad (Live label) | Starts | Velocity |
|---|---|---|---|
| Kick | 36 (C1) | 0.0, 1.0, 2.0, 3.0 | 120 |
| Clap | 39 (D#1) (or snare 38) | 1.0, 3.0 | 110 |
| Closed hat | 42 (F#1) | 0.5, 1.5, 2.5, 3.5 | 90 ± 10 |
| Open hat | 46 (A#1) | 3.5 in bar 4 only (beat 15.5 in a 16-beat clip) | 95 |
| Fill, bar 4 | clap or snare | 15.0, 15.25, 15.5, 15.75 | 80, 90, 100, 115 |

Durations 0.25 for all drum notes. Verify pad numbers against `drum_pads` before writing.

## Plan (15–20 min)

1. **Show me · a kit (3 min).** `create_midi_track(name="Drums", why="Drums get their own track")`, `set_track(track, color_index=14)`. `browse(query="Kit", categories=["drums"])`, pick a 909-style or clean electronic kit, `load_device(uri=<picked>, track, why="A bright electronic kit suits synth-pop")`. If the browse is slow or empty, `load_device(name="Drum Rack")` and ask the user to drag samples onto pads (Let me try). Read `get_devices(track, device_path="0")` → `drum_pads`; tell them which pad is kick, clap, hats. `select(track, device_path="0", show_device_detail=true)` so they see the pads.
2. **Show me · kick on every beat (2 min).** `create_clip(track, slot=0, length=4.0, name="Beat A")`; `add_notes` kicks at 0,1,2,3. `select(track, slot=0, show_clip_detail=true)`; `fire_clip`. "Four-on-the-floor: the kick is the pulse. On its own it is a metronome."
3. **Show me · backbeat (2 min).** `add_notes` clap at 1.0 and 3.0, why="Backbeat on 2 and 4 turns the pulse into a groove". Play. Ask: does it feel like it leans now?
4. **Show me · hats, A/B (4 min).** A: straight 8ths at every 0.5 (velocity 85). Play 2 bars. Then `remove_notes(track, slot=0, from_pitch=42, pitch_span=1)` and B: offbeats only (0.5, 1.5, 2.5, 3.5), why="Offbeat hats give the disco bounce". Play. Ask which bounces more. Keep their pick (usually B for this style); `undo` if they prefer A.
5. **Show me · 4 bars and a fill (3 min).** `duplicate_clip_loop` twice → `loop_end: 16.0`. In bar 4: `remove_notes(from_time=15.0, time_span=1.0, from_pitch=36, pitch_span=1)` to drop the last kick, and `add_notes` the clap fill at 15.0/15.25/15.5/15.75 with rising velocities, why="A fill at the end of bar 4 announces the repeat". Play the 4 bars.
6. **Let me try · open hat (3 min).** Task: "In Clip View, find the A#1 row (open hat; hover the row to see the pad name). Press B for Draw Mode, click at bar 4, the 'and' of 4 (ruler 4.4.3), press B again." Verify `get_notes(track, slot=0, from_pitch=46, pitch_span=1)` → one note at 15.5. Feedback: right (position) / change (velocity if < 80; or if it landed at 15.0, nudge right one grid step) / why (the open hat on the last offbeat lifts into bar 1).
7. **Show me · velocity breath (2 min).** `get_notes(from_pitch=42, pitch_span=1)`, then `modify_notes` alternating hat velocities 95/75 by id, why="Alternating hat velocity stops the loop sounding like a machine". Point at the velocity lane. Recap and journal.

## Exercise (Let me try)

Make "Beat B" in slot 1: `duplicate_clip` (Claude) then the user removes the kicks in bar 4 beats 3–4 (select the two C1 notes at 4.3 and 4.4, Delete) and adds a second clap layer on 2 and 4 (D1 row) at velocity ~60. Verify with `get_notes`: kicks in bar 4 at 12.0 and 13.0 only; D1 notes at 1,3,5,7,9,11,13,15.

## Verification

- Kick at every integer beat 0–15 except the deliberate gaps; velocity ≥ 110 and even.
- Clap at odd beats; fill in 15.0–15.75 with rising velocities.
- Hats only on x.5 positions (offbeat version); velocities vary ±10–20.
- Open hat at 15.5 only; nothing on pads with `has_chain: false`; nothing ≥ 16.0.
- `get_clip().loop_end == 16.0`.

## Recap

- Four-on-the-floor = kick on 1, 2, 3, 4; the clap on 2 and 4 is the backbeat; offbeat hats are the bounce.
- Bars 1–3 repeat, bar 4 changes: drop a kick, add a fill, open a hat.
- Velocity is the difference between a machine and a drummer.

## Go deeper

[05-chords-and-keys.md](05-chords-and-keys.md) or [04-bass-fundamentals.md](04-bass-fundamentals.md) to put something on top; [08-sidechain-and-space.md](08-sidechain-and-space.md) to make the kick push the pads; [10-transitions-and-automation.md](10-transitions-and-automation.md) for bigger fills. Contrast lesson: [03-drums-half-time-140.md](03-drums-half-time-140.md).
