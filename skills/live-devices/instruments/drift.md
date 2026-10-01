# Drift (`Drift`)

A compact analog-style synth: two oscillators with shape morphing, noise, one low-pass + high-pass
filter, two envelopes (Env 2 can cycle), one LFO, a small mod matrix and a `Drift` control that
adds per-voice analog imperfection. Fast route to warm pads, leads and simple basses.

Load: `load_device(name="Drift", track=i, category="instruments")`.
Names verified from Live 12.0 and 12.4 definitions; note the resonance spelling changed:
`LP Reso` (12.0) vs `LP Res` (later) — use whichever the read list shows.

## Oscillators and noise

| LOM name | What it does | Start |
|---|---|---|
| `Osc 1 Wave` | Waveform set (quantized; read `value_items`) | Saw for pads/leads |
| `Osc 1 Shape` | Morphs the waveform (pulse width / shape) | 0.2–0.5 |
| `Osc 1 Shape Mod Amt`, `Shape Mod Src` | Modulate shape (PWM-style movement) | LFO, +20 % |
| `Osc 1 Oct` | Octave | 0; bass −1 |
| `Osc 1 Gain`, `Osc 2 Gain`, `Noise Gain` | Mix | Osc 1 0 dB, Osc 2 −3 dB, Noise −inf |
| `Osc 2 Wave`, `Osc 2 Oct`, `Osc 2 Shape` | Second oscillator | same wave, same octave |
| `Osc 2 Detune` | Cents against Osc 1 — the warmth | 6–12 ct |
| `Osc 1 Flt On`, `Osc 2 Flt On`, `Noise On` | Route each source through the filter | all On |
| `Osc Retrig On` | Phase reset per note (consistent bass) | On for bass, Off for pads |
| `Pitch Mod Src 1`, `Pitch Mod Amt 1`, `Pitch Mod Src 2`, `Pitch Mod Amt 2` | Pitch modulation slots | Env 2 → +12 st short decay for "zap" |

## Filter

`LP Type` (`I` / `II`; read `value_items` — II is more aggressive), `LP Freq`, `LP Reso`/`LP Res`,
`HP Freq` (clean up pad lows), `Key > LPF` (key tracking), `LP Mod Src 1`, `LP Mod Amt 1`,
`LP Mod Src 2`, `LP Mod Amt 2` (two filter modulation slots; default sources are Env 2 and LFO).
`LP Mod Src 1/2` may be chooser-only (not settable) in some builds — set the *amount* and tell the
user which source to pick if the source parameter is absent.

## Envelopes and LFO

`Env 1 Attack/Decay/Sustain/Release` (amp). `Env 2 Attack/Decay/Sustain/Release` (mod) or, when
`Env 2 Cyc On` = Cyc, the cycling envelope: `Cyc Env Tilt`, `Cyc Env Hold`, `Cyc Env Time Mode`
(`Freq`/`Ratio`/`Time`/synced), `Cyc Env Rate`/`Cyc Env Ratio`/`Cyc Env Time`/`Cyc Env Synced`.
LFO: `LFO Wave`, `LFO Time Mode` (`Freq`/`Ratio`/`Time`/synced), `LFO Rate`/`LFO Ratio`/`LFO Time`/`LFO Synced`,
`LFO Amt`, `LFO Retrig On`, `LFO Mod Src`, `LFO Mod Amt`.

## Mod matrix and global

`Mod Source 1/2/3`, `Mod Dest 1/2/3`, `Mod Matrix Amt 1/2/3` (three free slots), `Vel > Vol`.
`Voice Mode` (`Poly`/`Mono`/`Stereo`/`Unison`) and `Voice Count` are choosers added by Live's control
surface layer and may not be plain parameters — ask the user to set them if absent. Per-mode
knobs: `Thickness` (Mono), `Spread` (Stereo), `Strength` (Unison). `Legato On`, `Glide Time`,
`Drift` (analog instability, 0–100 %), `Transpose`, `Volume`.

## Recipes

### Warm synth-pop pad (fastest good pad in Live)
```
Osc 1 Wave Saw, Shape 0.3; Osc 2 Wave Saw, Osc 2 Detune +9 ct, Osc 2 Gain −2 dB; Noise Gain −inf
Voice Mode Stereo (by hand if needed), Spread 60 %; Drift 35 %
LP Type I; LP Freq ≈ 1.5 kHz; LP Reso 10 %; HP Freq ≈ 150 Hz; Key > LPF 30 %
Env 1 Attack 700 ms, Decay 1 s, Sustain 85 %, Release 2.5 s
LFO Wave Triangle, LFO Time Mode Freq, LFO Rate 0.2 Hz, LFO Amt 100 %; LP Mod Amt 2 (LFO) +12 %
Osc 1 Shape Mod Amt +15 % from LFO
After: Chorus-Ensemble (optional — Stereo mode already widens), Compressor sidechain, Reverb send
```
Why: `Drift` gives the slow pitch/filter wander a real poly has; HP keeps the pad out of the bass.

### Drifting lead
```
Osc 1 Saw, Osc 2 Square Oct 0 Detune +5 ct; Voice Mode Mono, Thickness 40 %; Legato On; Glide Time 50 ms
LP Freq ≈ 2.5 kHz; LP Reso 15 %; LP Mod Amt 1 (Env 2) +35 %; Env 2 Attack 0, Decay 300 ms, Sustain 20 %
Env 1 Attack 3 ms, Decay 200 ms, Sustain 80 %, Release 300 ms; Drift 25 %
Mod Source 1 LFO → Mod Dest 1 Pitch, Mod Matrix Amt 1 +4 % (vibrato), LFO Rate 5.5 Hz
```

### Simple analog bass
```
Osc 1 Saw Oct −1; Osc 2 Square Oct −1 Detune 0 Gain −6 dB; Osc Retrig On On
Voice Mode Mono; Legato On; Glide Time 40 ms; Drift 10 %
LP Type II; LP Freq ≈ 400 Hz; LP Reso 20 %; LP Mod Amt 1 (Env 2) +45 %; Env 2 Decay 180 ms, Sustain 0
Env 1 Attack 0, Decay 250 ms, Sustain 90 %, Release 100 ms
After: Saturator 5 dB, Compressor sidechain
```

### Cycling-envelope rhythmic pad (builds)
```
Pad recipe + Env 2 Cyc On = Cyc; Cyc Env Time Mode synced; Cyc Env Synced 1/8; Cyc Env Tilt 50 %; Cyc Env Hold 20 %
LP Mod Amt 1 (Env 2) +40 %
```
Why: a tempo-synced cycling envelope on the filter is a built-in rhythmic gate — no sidechain needed.

## Verify
Read `LP Reso` vs `LP Res`, `Voice Mode` presence, and `LP Mod Src 1/2` presence before writing.
`Drift`, `Osc 2 Detune`, `Env 1 Attack`, `LFO Rate` are stable across versions.
