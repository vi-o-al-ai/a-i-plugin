# Velocity (`MidiVelocity`)

Reshapes incoming velocities: compress, expand, randomize, fix, or gate notes by velocity. Use it
to humanize hats, flatten a sub, or tame an over-expressive lead — without editing notes.

Load: `load_device(name="Velocity", track=i, category="midi_effects")`.

## Parameters

| LOM name | What it does | Start |
|---|---|---|
| `Mode` | `Clip` (limit to Out range) / `Gate` (notes outside the input range are dropped) / `Fixed` (every note = Out Hi) | Clip |
| `Drive` | Curve bend: positive lifts quiet notes, negative pushes them down | 0 |
| `Compand` | Negative = compress (less dynamic), positive = expand | −0.3 to tame |
| `Random` | Random velocity added (0–64) | 10–15 hats |
| `Out Hi`, `Out Low` | Output velocity ceiling/floor | 127 / 1 |
| `Range` | Input range width (for Gate) | 127 |
| `Lowest` | Bottom of the input range | 1 |

## Recipes

### Humanize hats without editing notes
```
Mode Clip; Random 12; Compand 0; Out Hi 110; Out Low 40
```
Why: random velocity re-rolls every pass, so the hat loop never repeats exactly (same idea as `velocity_deviation` on notes, `midi-writing/humanize.md`).

### Sub bass: constant level
```
Mode Fixed; Out Hi 110
```
Why: the sub must not breathe; fixed velocity removes any accidental dynamics.

### Tame a lead
```
Mode Clip; Compand −0.4; Out Low 70; Out Hi 118
```

### Drop ghost notes (keep only accents)
```
Mode Gate; Lowest 70; Range 57
```
Why: notes under velocity 70 are removed — instant "simplify this part".

## Verify
`Mode` via `display`; `Random` and `Compand` by `value` after reading `min`/`max`.
