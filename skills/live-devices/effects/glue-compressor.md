# Glue Compressor (`GlueCompressor`)

SSL-bus-style compressor with stepped attack/release. Sounds like "one thing" on groups: drum bus,
synth bus, master. Also a smoother sidechain pump than Compressor.

Load: `load_device(name="Glue Compressor", track=i, category="audio_effects")`.

## Parameters

| LOM name | What it does | Values / start |
|---|---|---|
| `Threshold` | Where compression starts (dB) | −15 dB bus; −25 dB sidechain |
| `Ratio` | Quantized `2`, `4`, `10` | 2 glue · 4 drums · 10 smash/sidechain |
| `Attack` | Quantized ms (0.01 … 30) | 10 or 30 ms for glue (keeps punch); 0.3 ms for sidechain |
| `Release` | Quantized s (0.1 … 1.2) plus `Auto` | Auto for glue; 0.2 for pump @120 |
| `Makeup` | Make-up gain (dB) | match bypass loudness |
| `Range` | Maximum gain reduction (dB) — limits how hard it can clamp | −70 (off) … −6 for gentle sidechain |
| `Peak Clip In` | Soft clipper on the output | On for dubstep drum bus |
| `Dry/Wet` | Parallel | 100 % glue; 50 % drums |
| `S/C On`, `S/C Gain`, `S/C Mix`, `S/C EQ On`, `S/C EQ Type`, `S/C EQ Freq`, `S/C EQ Gain` / `S/C EQ Q` | Sidechain | Source routing is by hand (see compressor.md) |

Quantized parameters (`Ratio`, `Attack`, `Release`) take `display` strings from `value_items`
(e.g. `"4"`, `"0.3"`, `"Auto"`) — read them first; the exact strings vary.

## Recipes

### Mix-bus / synth-bus glue
```
Ratio 2; Attack 30 ms; Release Auto; Threshold so the meter shows 1–2 dB reduction; Makeup +1 dB
```
Why: slow attack, gentle ratio — the parts move together without anyone hearing a compressor.

### Drum bus (synth-pop)
```
Ratio 4; Attack 10 ms; Release 0.2; Threshold ≈ −20 dB (3–5 dB GR); Makeup +3 dB; Dry/Wet 60 %
```

### Drum bus (dubstep drop)
```
Ratio 4; Attack 0.3 ms; Release 0.1; Threshold ≈ −24 dB (5–8 dB GR); Peak Clip In On; Makeup +5 dB
```
Why: fast attack + clipper flattens the kit into one aggressive slab, which is the sound.

### Smooth sidechain for pads
```
S/C On On (Audio From kick by hand); Ratio 10; Attack 0.3 ms; Release 0.2 (120 BPM) ; Threshold ≈ −30 dB; Range −12 dB
```
Why: `Range` caps the duck at 12 dB so the pad never disappears; the stepped release gives a rounder pump than Compressor.

## Verify
Read `Ratio`/`Attack`/`Release` `display` after setting; if a `display` string is rejected
(`-32602`), copy the exact item from `value_items`.
