# 03 · Drums: half-time at 140

**Goal.** A 4-bar riddim/dubstep drum loop at 140 BPM: kick on 1, snare on 3, sparse extra kicks, hats that leave space, a triplet snare roll in bar 4. The user can explain why 140 feels like 70.

**Prerequisites.** 01 at confidence ≥ 1; 02 helps as a contrast but is not required.

**Terms.** Half-time, snare on 3, triplet, layering, roll.

## Reference pattern (per bar)

| Element | Pad | Starts | Velocity |
|---|---|---|---|
| Kick | 36 | 0.0; plus 1.5 or 3.5 in bars 2 and 4 only | 127 / 110 |
| Snare | 38 | 2.0 | 127 |
| Clap layer | 39 | 2.0 | 100 |
| Closed hat | 42 | 1.0, 3.0 (beats 2 and 4: the offbeats of the felt half-time pulse), or 8ths 0.0–3.5 at low velocity | 70–85 |
| Triplet hats (bars 2, 4) | 42 | 3.0, 3.333, 3.667 | 70, 80, 90 |
| Roll, bar 4 | 38 | 14.0, 14.333, 14.667, 15.0, 15.25, 15.5, 15.75 | 70 → 120 |

Nothing on beat 2 (1.0) or beat 4 (3.0) for the kick; no snare on 1.0 or 3.0. Space is the style.

## Plan (15–20 min)

1. **Show me · tempo and kit (3 min).** `set_transport(tempo=140, why="Dubstep tempo; the drums will make it feel like 70")`. Reuse the Drums track or `create_midi_track(name="Drums 140")`; `browse(query="Kit", categories=["drums"])` for a hard electronic kit; `load_device(uri=...)`. Read `drum_pads`.
2. **Show me · kick on 1, snare on 3 (3 min).** `create_clip(track, slot=0, length=4.0, name="Riddim A")`. `add_notes` kick at 0.0 (127) and snare at 2.0 (127), layered clap at 2.0 (100), why="Snare on 3 is the half-time backbeat". Fire it. Ask them to tap along: "you tap twice a bar, 70 taps a minute, while Live says 140."
3. **Show me · the A/B that explains everything (3 min).** `duplicate_clip(track, slot=0, target_slot=1)`; in slot 1 `remove_notes(from_pitch=38, pitch_span=2)` and `add_notes` snare at 1.0 and 3.0, why="A/B: same tempo with snare on 2 and 4 to hear double-time". `fire_clip(track, slot=1)` then `fire_clip(track, slot=0)`: "same 140 BPM; the snare position alone halves the feel." Delete nothing; rename slot 1 "Double-time (compare)".
4. **Show me · hats and space (3 min).** In slot 0 add hats at 1.0 and 3.0 at 80, why="Hats on 2 and 4 are the offbeats of the felt 70 BPM pulse". Play. Then `duplicate_clip_loop` twice → 16 beats; in bars 2 and 4 replace the hat at 3.0 with a triplet group 3.0/3.333/3.667 (`remove_notes` then `add_notes`), why="Triplets are the riddim swing". Point to the grid: right-click → Fixed Grid 1/8T shows triplets.
5. **Show me · sparse kicks (2 min).** Add one kick at 1.5 in bar 2 (beat 5.5) and one at 3.5 in bar 4 (15.5), velocity 110, why="One extra kick per two bars; more would crowd the bass". A/B with and without; keep what they like.
6. **Let me try · snare roll (4 min).** Task: "In bar 4, D1 row: set the grid to 1/8T (right-click → Fixed Grid → 1/8T), draw snares at 4.3, then the two triplet positions after it; switch the grid to 1/16 and draw four more from 4.4 to the end. Then in the velocity lane drag them so they rise from quiet to loud." Verify `get_notes(from_time=14.0, time_span=2.0, from_pitch=38, pitch_span=1)`: 7 notes, starts within ±0.02 of 14, 14.333, 14.667, 15, 15.25, 15.5, 15.75, velocities ascending. Feedback right / change / why ("a roll that gets louder pulls the ear into the next bar; a flat roll is just noise").
7. **Recap and journal (1 min).** Note in the journal that 02 vs 03 was heard side by side if it was.

## Exercise (Let me try)

Build "Riddim B" in slot 2 by duplicating A and moving the extra kicks: bar 2's kick from 5.5 to 7.5 and bar 4's from 15.5 to 13.5 (select note, drag). Verify with `get_notes(from_pitch=36, pitch_span=1)`.

## Verification

- Kick at 0, 4, 8, 12 (127); at most two extra kicks in 16 beats, none at x.0 of beat 3 (2.0, 6.0, 10.0, 14.0).
- Snare + clap at 2, 6, 10, 14 only (plus the roll in 14–16).
- Hats never louder than 90; triplet starts within ±0.02 of thirds.
- Roll velocities strictly ascending; last note ≤ 15.75.
- `get_transport().tempo == 140`.

## Recap

- Half-time: kick on 1, snare on 3; same 140 BPM, half the felt pulse.
- Fewer hits, not more: one extra kick per two bars, quiet hats, space for the bass.
- Triplets (0.333 steps) are the riddim bounce; rising-velocity rolls end phrases.

## Go deeper

[04-bass-fundamentals.md](04-bass-fundamentals.md) for the clean sub that lives in the gaps; [07-wobble-and-growl-bass.md](07-wobble-and-growl-bass.md) for the bass this beat exists for; [10-transitions-and-automation.md](10-transitions-and-automation.md) for builds and the silent beat before a drop.
