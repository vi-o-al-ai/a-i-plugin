# Phaser-Flanger (`PhaserNew`)

Three modes: **Phaser** (notches sweeping — airy swirl), **Flanger** (short modulated delay —
jet/metallic), **Doubler** (short fixed delay with modulation — thickening). Two LFOs and an
envelope follower drive the sweep.

Load: `load_device(name="Phaser-Flanger", track=i, category="audio_effects")`.

## Parameters

| LOM name | What it does | Start |
|---|---|---|
| `Mode` | `Phaser` / `Flanger` / `Doubler` | Phaser for pads |
| `Mod Sync` | LFO 1 synced on/off | On for rhythmic, Off for slow |
| `Mod Rate` (synced) / `Mod Freq` (Hz) | LFO 1 speed | 4 bars · 0.1–0.2 Hz |
| `Mod Wave` | LFO shape | Sine / Triangle |
| `Mod Phase` | L/R LFO phase | 90–180° for width |
| `Spin Enabled`, `Spin` | L/R rate offset instead of phase | Off |
| `Duty Cycle` | Waveform skew | 50 % |
| `Amount` | Sweep depth | 40–60 % |
| `Feedback`, `FB Inv` | Resonance of notches/comb; inverted polarity for hollower tone | 20–35 %; flanger 60 % |
| `Notches` | Phaser: number of notches (more = denser swirl) | 4–8 |
| `Center Freq` | Phaser: centre of the sweep (newer builds) | ≈ 1 kHz |
| `Flange Time` (12.0) / `Flanger Time` (newer) | Flanger delay time — shorter = higher comb | 1–3 ms |
| `Doubler Time` | Doubler delay | 10–20 ms |
| `Lfo Blend`, `Mod Sync 2`, `Mod Rate 2` / `Mod Freq 2` | Second LFO and its mix | Blend 0 |
| `Env Enabled`, `Env Amount`, `Env Attack`, `Env Release` | Envelope follower → sweep | Off |
| `Safe Freq` | "Safe bass": keeps lows unmodulated | ≈ 150 Hz On |
| `Warmth` | Saturation on the wet path | 20 % |
| `Output Gain` | Trim | 0 dB |
| `Dry/Wet` | Mix | 35–50 % |

## Recipes

### Slow phaser on a pad (synth-pop)
```
Mode Phaser; Mod Sync Off; Mod Freq 0.12 Hz; Amount 50 %; Feedback 30 %; Notches 6; Mod Phase 120°; Safe Freq ≈ 150 Hz; Warmth 20 %; Dry/Wet 40 %
```
Why: a sweep slower than the chord changes keeps a static pad alive without drawing attention.

### Jet flange on a riser or hat loop (build)
```
Mode Flanger; Mod Sync On; Mod Rate 4 bars (or 2 bars); Amount 80 %; Feedback 65 %; Flange Time 1.5 ms; Dry/Wet 50 %
```
Why: feedback + short time = the metallic "jet"; synced to the build length it peaks at the drop.

### Doubler thickening for a lead
```
Mode Doubler; Doubler Time 14 ms; Mod Freq 0.4 Hz; Amount 20 %; Dry/Wet 40 %
```

### Envelope-driven phaser on a pluck
```
Mode Phaser; Env Enabled On; Env Amount 60 %; Env Attack 5 ms; Env Release 250 ms; Amount 20 %; Dry/Wet 45 %
```

## Verify
Check whether your build exposes `Flange Time` or `Flanger Time`, and `Center Freq`. Keep
`Safe Freq` on for anything with low end.
