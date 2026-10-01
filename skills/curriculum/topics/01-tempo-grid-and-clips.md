# 01 · Tempo, grid and clips

**Goal.** The user can set a tempo, read bars and beats as numbers (1 bar = 4.0 beats; a 16th = 0.25), set a clip's length and loop, duplicate clips and scenes, and knows why a fired clip waits for the bar.

**Prerequisites.** 00 at confidence ≥ 1.

**Terms.** BPM, beat, bar, grid, loop brace, launch quantization, scene.

## Plan (15–20 min)

1. **Show me · tempo (2 min).** `get_transport()`; say the current tempo. `set_transport(tempo=120, why="Synth-pop tempo; one bar is exactly 2 seconds")`. Point to the tempo field at the left of the Control Bar. The maths once: 120 beats per minute → 0.5 s per beat → 2 s per bar of 4. Riddim later: 140 → 0.4286 s → 1.714 s per bar.
2. **Show me · beats as numbers (4 min).** On a MIDI track (reuse the 00 track or `create_midi_track(name="Grid")` + `load_device(name="Drift")`), `create_clip(track, slot=0, length=4.0, name="Grid 1 bar")`. `add_notes` with four notes on the beats: starts 0.0, 1.0, 2.0, 3.0, duration 0.25, pitch 60. Then four more on the offbeats: 0.5, 1.5, 2.5, 3.5, pitch 67, velocity 80. `select(track, slot=0, show_clip_detail=true)`. Read the ruler with them: "1.1 is beat 1 (0.0), 1.2 is beat 2 (1.0), 1.2.3 is the and of 2 (1.5)." Right-click the piano roll background → Fixed Grid → 1/16: each small column is 0.25.
3. **Show me · clip length and the loop brace (3 min).** `get_clip(track, slot=0)` → `length: 4.0, loop_end: 4.0`. `duplicate_clip_loop(track, slot=0, why="Double the loop so bar 2 can differ from bar 1")`; read back `loop_end: 8.0`; point at the loop brace now spanning two bars. `set_clip(track, slot=0, name="Grid 2 bars")`. Explain: the loop brace is what repeats; notes outside it never play.
4. **Show me · clips and scenes multiply (3 min).** `duplicate_clip(track, slot=0, target_slot=1, why="A copy to vary without losing the original")`. `set_scene(scene=0, name="A")`, `set_scene(scene=1, name="B")` (or `create_scene` if there is only one). `transpose_notes(track, slot=1, semitones=5, why="Make B obviously different from A")`. Say: "same clip, new slot, new pitch; scene B is now a different idea."
5. **Show me · launch quantization (2 min).** `fire_scene(0)`; ask them to count; `fire_scene(1)` on an off-beat: it waits for the next bar. Point to the Quantization menu in the Control Bar ("1 Bar" by default). One sentence on why: so everything stays on the grid when you jam.
6. **Let me try · tempo and loop (4 min).** Task: "Click the tempo field in the Control Bar, type 140, press Enter. Then in Clip View for 'Grid 2 bars', drag the right end of the loop brace so the loop is 1 bar long again." Verify: `get_transport().tempo == 140`, `get_clip(track, slot=0).loop_end == 4.0`. Feedback right / change / why ("at 140 the same 8 notes feel faster; the loop end decides what repeats, not the notes").
7. **Recap and journal (1 min).** Return tempo to 120 if the next lesson is synth-pop (`set_transport(tempo=120)`), and say so.

## Exercise (Let me try)

Make scene C: duplicate scene B's clip into slot 2 (select the clip, Cmd/Ctrl+D or drag with Option/Alt), then in Clip View move every note one 16th later by selecting all (Cmd/Ctrl+A) and dragging right by one grid step at 1/16 grid (one 8th would push the last offbeat note onto `loop_end`, where it is silent). Verify: `get_notes(track, slot=2)` starts are the originals + 0.25, all below `loop_end`.

## Verification

- `get_transport().tempo` is the intended value.
- `get_clip(...).loop_end − loop_start` is 4.0 or 8.0, `looping: true`.
- `get_notes(track, slot=0)`: 8 notes, starts at multiples of 0.5, none ≥ `clip_length`.
- Scenes 0–2 named.

## Recap

- 1 bar = 4.0 beats; a 16th = 0.25; the tool's `start` is what the ruler shows as bar.beat.sixteenth.
- The loop brace decides what repeats; `duplicate_clip_loop` doubles it; `duplicate_clip` copies a clip to another slot.
- Fired clips and scenes wait for the quantization boundary (1 bar by default).

## Go deeper

[02-drums-four-on-the-floor.md](02-drums-four-on-the-floor.md) (synth-pop) or [03-drums-half-time-140.md](03-drums-half-time-140.md) (riddim). Quantize and swing: `quantize_notes(grid=0.25, swing=0.15)` on a copy, A/B against the straight version.
