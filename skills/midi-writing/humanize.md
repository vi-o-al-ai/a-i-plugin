# Humanize

Machines are the sound of both genres; humanize to add *life*, not sloppiness. Default: tight
drums, slightly loose hats, expressive leads.

## Rules

| Element | Timing offset (beats) | Velocity | Notes |
|---|---|---|---|
| Kick | 0 — on the grid | ±4 | The anchor. Never move it. |
| Snare / clap | 0 to +0.015 (late = laid back) | ±6 | Dubstep snare on 3: exactly 2.0, velocity 127, always. |
| Closed hats | ±0.01–0.03 | ±8–15 | Keep the accent pattern (on-beat louder). Use `probability` 0.7–0.85 on 16th ghosts. |
| Open hats | ±0.01 | ±8 | Vary `duration` (0.35–0.5) more than velocity. |
| Percussion / shakers | ±0.02–0.03 | ±12 | The loosest layer. |
| Chord stabs | ±0.01 on the whole chord (move all notes of a hit together) | ±8 | Strum: offset the chord's notes by 0.005–0.01 each from bottom to top for a "played" feel. |
| Pads | 0 | ±5 | Let the envelope and LFO move. |
| Synth bass | 0 to +0.01 | ±8 | Off-beat notes a touch softer. |
| Sub bass | 0 | 0 | Dead straight, constant. |
| Lead | ±0.02, pickups early (−0.02) | ±10–15, phrase peaks louder | Vary `duration` ±10 %. |

What 0.01 beats is in milliseconds: 5 ms at 120 BPM, 4.3 ms at 140. 0.03 beats = 15 ms / 12.9 ms.
Below ~5 ms nobody hears timing; above ~30 ms it reads as a mistake on drums.

## Prefer Live's note properties for randomness

`add_notes` items accept `velocity_deviation` and `probability`. They re-roll every loop pass,
so the groove never repeats exactly — better than baking fixed offsets.

- `"velocity_deviation": 12` → Live plays the note anywhere from `velocity` to `velocity + 12`
  (set `velocity` to the bottom of the range you want).
- `"probability": 0.75` → the note plays 75 % of the time. Use on ghost hats and extra percussion, never on kick/snare/sub.

Example ghost-hat 16ths between the main 8ths (velocity 55 ± 12, 75 %):
```json
[
 {"pitch":42,"start":0.25,"duration":0.1,"velocity":55,"velocity_deviation":12,"probability":0.75},
 {"pitch":42,"start":0.75,"duration":0.1,"velocity":55,"velocity_deviation":12,"probability":0.75},
 {"pitch":42,"start":1.25,"duration":0.1,"velocity":55,"velocity_deviation":12,"probability":0.75},
 {"pitch":42,"start":1.75,"duration":0.1,"velocity":55,"velocity_deviation":12,"probability":0.75},
 {"pitch":42,"start":2.25,"duration":0.1,"velocity":55,"velocity_deviation":12,"probability":0.75},
 {"pitch":42,"start":2.75,"duration":0.1,"velocity":55,"velocity_deviation":12,"probability":0.75},
 {"pitch":42,"start":3.25,"duration":0.1,"velocity":55,"velocity_deviation":12,"probability":0.75},
 {"pitch":42,"start":3.75,"duration":0.1,"velocity":55,"velocity_deviation":12,"probability":0.75}
]
```

## Swing: use the tool, not hand offsets

`quantize_notes(track, slot, grid=0.25, amount=1.0, swing=s)` delays every second 16th by `s × 0.125` beats.

| `swing` | Feel | ≈ MPC swing % |
|---|---|---|
| 0.0 | straight | 50 |
| 0.2 | subtle push | 55 |
| 0.4 | house shuffle | 60 |
| 0.67 | full triplet | 66.7 |

Swing acts on the whole clip, so put hats/percussion on their own clip or track if the kick must
stay straight (it must). For a partially humanized clip, `quantize_notes(grid=0.25, amount=0.8)`
pulls hand-placed notes 80 % of the way back to the grid — a quick way to tidy without killing feel.

## Worked example: straight vs humanized hats (1 bar, 8ths)

Straight:
```json
[
 {"pitch":42,"start":0.0,"duration":0.125,"velocity":90},{"pitch":42,"start":0.5,"duration":0.125,"velocity":70},
 {"pitch":42,"start":1.0,"duration":0.125,"velocity":90},{"pitch":42,"start":1.5,"duration":0.125,"velocity":70},
 {"pitch":42,"start":2.0,"duration":0.125,"velocity":90},{"pitch":42,"start":2.5,"duration":0.125,"velocity":70},
 {"pitch":42,"start":3.0,"duration":0.125,"velocity":90},{"pitch":42,"start":3.5,"duration":0.125,"velocity":70}
]
```
Humanized (offsets within ±0.02, velocities within ±10, accents preserved, first hit on the grid):
```json
[
 {"pitch":42,"start":0.0,"duration":0.125,"velocity":92},{"pitch":42,"start":0.515,"duration":0.125,"velocity":66},
 {"pitch":42,"start":0.99,"duration":0.125,"velocity":88},{"pitch":42,"start":1.52,"duration":0.125,"velocity":74},
 {"pitch":42,"start":2.005,"duration":0.125,"velocity":94},{"pitch":42,"start":2.49,"duration":0.125,"velocity":63},
 {"pitch":42,"start":3.01,"duration":0.125,"velocity":86},{"pitch":42,"start":3.485,"duration":0.125,"velocity":72}
]
```
Pattern: the off-beats drift late more often than early (that is "lazy", which dance music likes);
no two consecutive hits share a velocity.

## Applying humanization to existing notes

1. `get_notes` → each note has an `id`.
2. Build `changes` for `modify_notes`: `{"id": ..., "start": start + offset, "velocity": clamp(v + dv, 1, 127)}`.
3. Keep offsets > 0 for the first note in the clip (a negative start is invalid); keep `start + duration ≤ loop_end`.
4. `modify_notes` returns `missing_ids` — non-empty means the clip changed under you; re-read.

## Do not humanize

- Kick, sub bass, dubstep snare, sidechain-trigger notes.
- Anything the user called "tight", "robotic", "quantized" or "machine".
- A loop you have not listened to with the user first: fix the notes, then the feel.
