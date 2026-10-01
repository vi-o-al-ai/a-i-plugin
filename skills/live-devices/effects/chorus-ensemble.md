# Chorus-Ensemble (`Chorus2`)

Three modes: **Classic** (two-voice chorus), **Ensemble** (three-voice, the 80s string-machine
shimmer), **Vibrato** (pitch wobble only). The quickest way to make a pad or lead wide and vintage.

Load: `load_device(name="Chorus-Ensemble", track=i, category="audio_effects")`.

## Parameters

| LOM name | What it does | Start |
|---|---|---|
| `Mode` | `Classic` / `Ensemble` / `Vibrato` (quantized) | Ensemble for pads |
| `Rate` | LFO speed (Hz) | 0.3–0.6 Hz pads; 1–2 Hz leads |
| `Amount` | Modulation depth — how "seasick" | 25–50 % |
| `Feedback` | Resonant, metallic colour | 0–15 % |
| `Width` | Stereo spread (Classic/Ensemble) | 100 % |
| `Offset` | Vibrato mode: phase offset L/R | — |
| `Shape` | Vibrato mode (newer builds): LFO shape | — |
| `HP Freq` | Newer builds: high-pass on the wet signal — keeps lows mono | ≈ 200 Hz |
| `Gain` | Output trim | 0 dB |
| `Warmth` | Saturation/darkening of the wet path | 20–40 % |
| `Dry/Wet` | Mix | 40–50 % pads; 25–35 % leads |

## Recipes

### 80s poly pad width (synth-pop)
```
Mode Ensemble; Rate 0.4 Hz; Amount 40 %; Feedback 5 %; Width 100 %; Warmth 30 %; HP Freq ≈ 200 Hz (if present); Dry/Wet 45 %
```
Why: three slightly detuned copies swimming against each other is the Juno/string-machine
sound; warmth takes the digital edge off.

### Lead doubling (subtle)
```
Mode Classic; Rate 1.2 Hz; Amount 15 %; Feedback 0; Width 80 %; Dry/Wet 30 %
```

### Wobbly keys / tape vibrato
```
Mode Vibrato; Rate 5.5 Hz; Amount 8 %; Dry/Wet 100 %
```

### Bass? No.
Keep chorus off anything below 150 Hz; if a mid bass needs width, use it with `HP Freq` ≈ 300 Hz
or Utility `Bass Mono` after it. The sub stays dry and mono.

## Verify
`Mode` via `display`; check whether `HP Freq` and `Shape` exist in your build.
