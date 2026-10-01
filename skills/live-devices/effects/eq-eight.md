# EQ Eight (`Eq8`)

Eight parametric bands. Its job in these genres is *space*: high-pass everything that is not
kick or sub, cut mud, add a little air. Boosts are small; cuts can be big.

Load: `load_device(name="EQ Eight", track=i, category="audio_effects")`.

## Parameters

Band `n` = 1…8; the `A` suffix is the main (or left/mid) channel, `B` the second channel when
`Eq Mode` is Left/Right or Mid/Side.

| LOM name | What it does | Notes |
|---|---|---|
| `n Filter On A` | Band enable | Only enabled bands cost CPU / affect sound |
| `n Filter Type A` | Quantized: low cut (12/48 dB), low shelf, bell, notch, high shelf, high cut (12/48 dB) — read `value_items` for exact strings | Low cut 48 for surgical pad cleanup |
| `n Frequency A` | Centre/corner frequency | Set with `normalized`, read `display` (Hz); adjust once |
| `n Gain A` | Boost/cut in dB (bell/shelf only) | `min`/`max` typically −15…+15 dB |
| `n Resonance A` | Q / slope sharpness | 0.7 broad … 3+ surgical |
| `Scale` | Scales all band gains (0–200 %) | Automate for "EQ fade-in" effects |
| `Output Gain` | Make-up | Compensate boosts |
| `Adaptive Q` | Narrower Q at higher gain | Leave default |
| `Eq Mode` | `Stereo` / `Left/Right` / `Mid/Side` | Mid/Side to widen pads: cut lows on Side |
| `Edit Mode` | UI: which channel the knobs edit | Not needed when you address `A`/`B` names directly |

Read all parameters first; the default set has some bands on and some off, with preset types per band.

## Recipes

### Pad / chords: get out of the bass's way
```
Band 1: On, type low cut 48 dB, Frequency ≈ 180 Hz (synth-pop) or ≈ 250 Hz (dubstep break pad)
Band 2: On, bell, Frequency ≈ 350 Hz, Gain −2.5 dB, Resonance 1.0   (mud)
Band 8: On, high shelf, Frequency ≈ 9 kHz, Gain +1.5 dB                (air)
```
Why: the pad's lows blur the kick and sub; nobody misses them once the bass is in.

### Mid bass vs sub (riddim)
```
Mid-bass track: Band 1 low cut 48 dB ≈ 90 Hz   → the sub track owns everything below
Sub track:      Band 1 low cut 12 dB ≈ 28 Hz; Band 8 high cut 48 dB ≈ 150 Hz → pure sine region
```

### Kick vs sub
```
Sub track: bell, Frequency = kick's fundamental (usually 50–60 Hz), Gain −3 dB, Resonance 2.5
or Kick: bell at the sub's note frequency (F0 ≈ 44 Hz), Gain −3 dB
```
Why: two sources on the same 50 Hz = flabby low end; give each its own slot.

### Brighter lead without harshness
```
Bell, Frequency ≈ 2.8 kHz, Gain −1.5 dB, Resonance 1.2 (harshness)
High shelf, Frequency ≈ 7 kHz, Gain +2 dB
```

### Clean up a reverb return
```
Low cut 48 dB ≈ 300 Hz; high cut 12 dB ≈ 8 kHz
```
Why: reverb below 300 Hz is mud; above 8 kHz it is hiss on a dense mix.

## Verify
`display` for frequency after each set; if the band type display is unexpected (e.g. a shelf when
you wanted a bell), set `n Filter Type A` via `display` from `value_items` and re-check `n Gain A`.
