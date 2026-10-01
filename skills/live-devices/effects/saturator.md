# Saturator (`Saturator`)

Waveshaping distortion from warm to brutal. Adds harmonics, so a bass becomes audible on small
speakers and a pad gets "glue". Drive in, Output out, pick the curve.

Load: `load_device(name="Saturator", track=i, category="audio_effects")`.

## Parameters

| LOM name | What it does | Start |
|---|---|---|
| `Drive` | Input gain into the curve (dB) — the amount of distortion | 3–6 warm · 12–20 bass grit · 24+ destroy |
| `Type` | Curve, quantized: Analog Clip, Soft Sine, Medium Curve, Hard Curve, Sinoid Fold, Digital Clip, Waveshaper (read `value_items`) | Soft Sine (warm) · Analog Clip (bass) · Hard Curve (drums) |
| `Color` | Enables the pre-shaper tone section | On for bass |
| `Base`, `Frequency`, `Width`, `Depth` | Live 12.0 names: low-shelf amount (Base) and a peak filter (Frequency/Width/Depth) before the shaper | Base +3 dB for bass weight |
| `Color Amt Low`, `Color Freq`, `Color Width`, `Color Amt Hi` | Newer-build names for the same section — use whichever the read list shows | — |
| `Output` | Make-up after the curve (dB) | ≈ −Drive/2 |
| `Dry/Wet` | Parallel | 100 % bass · 40 % pads |
| `Soft Clip` | Final soft limiter | On |
| `WS Drive`, `WS Curve`, `WS Depth`, `WS Lin`, `WS Damp`, `WS Period` | Waveshaper mode only — custom curve | — |

## Recipes

### Bass distortion stage (riddim mid bass)
```
Type Analog Clip (or Soft Sine for rounder); Drive 14 dB; Color On, Base +4 dB (12.0) / Color Amt Low +4 dB (newer)
Soft Clip On; Output −8 dB; Dry/Wet 100 %
Before it: EQ Eight low cut 90 Hz (the sub is on its own track). After it: Multiband Dynamics OTT, Utility Bass Mono.
```
Why: distortion generates harmonics of the fundamental, so the bass line reads on a phone speaker;
cutting the lows first stops the sub from modulating the distortion ("farting").

### Warm pad glue
```
Type Soft Sine; Drive 4 dB; Color Off; Output −2 dB; Dry/Wet 40 %; Soft Clip On
```

### Drum bus crunch (dubstep)
```
Type Hard Curve; Drive 8 dB; Output −6 dB; Soft Clip On; Dry/Wet 60 %
```

### Lead presence (synth-pop)
```
Type Medium Curve; Drive 6 dB; Color On, Frequency ≈ 2 kHz, Depth +3 dB; Output −4 dB; Dry/Wet 50 %
```

## Verify
Check which Color names exist (`Base`/`Frequency`/`Width`/`Depth` vs `Color Amt Low`/`Color Freq`/
`Color Width`/`Color Amt Hi`). Confirm `Type` via `display`. Level-match with `Output`: distortion
that is louder always "sounds better" — A/B at equal loudness.
