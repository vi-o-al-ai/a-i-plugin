# Analog (`UltraAnalog`)

Virtual-analog: two oscillators, two filters (each oscillator can be balanced between them),
two amps, two LFOs, noise, unison and vibrato. Classic bright leads, brass stabs and warm bass.

Load: `load_device(name="Analog", track=i, category="instruments")`.
LOM names use `OSC1`, `F1`, `AMP1`, `FEG1`, `AEG1`, `LFO1` (no spaces, as below).

## Oscillators

| LOM name | What it does | Start |
|---|---|---|
| `OSC1 Shape`, `OSC2 Shape` | Waveform (sine / saw / rectangle / noise-like; read `value_items`) | Saw lead/pad; rectangle for hollow bass |
| `OSC1 Octave`, `OSC2 Octave` | Octave offset | 0; bass −1 |
| `OSC1 Semi`, `OSC2 Semi` | Semitone offset | +7 on OSC2 for 5ths/brass |
| `OSC2 Detune` | Fine detune of OSC2 — width and warmth | 6–12 ct |
| `OSC1 Level`, `OSC2 Level` | Mix | both ≈ 70 % |
| `OSC1 Balance`, `OSC2 Balance` | Send each oscillator to F1 (left) or F2 (right) or both | 0 (both to F1) for simple patches |
| On/off switches and pulse width exist in the UI; if no parameter appears, set by hand (verify in Live) | | |

## Filters 1 and 2

`F1 On/Off`, `F1 Type` (2-/4-pole lowpass, bandpass, notch, highpass, formant variants — read
`value_items`), `F1 Freq`, `F1 Resonance`, `F1 Freq < Env` (filter envelope depth), `F1 Freq < LFO`,
`F1 Res < LFO`. Filter envelope `FEG1 Attack`, `FEG1 Decay`, `FEG1 Sustain`, `FEG1 Rel`.
Same with `F2 …`, `FEG2 …`.

## Amps

`AMP1 Level`, `AMP1 Pan`, envelope `AEG1 Attack`, `AEG1 Decay`, `AEG1 Sustain`, `AEG1 Rel`; same `AMP2 …`, `AEG2 …`.
Each filter feeds its own amp, so two complete signal paths can be layered inside one patch.

## LFOs, noise, global

`LFO1 Shape`, `LFO1 Sync` (`Hertz` or synced), `LFO1 Speed` (Hz), `LFO1 SncRate` (division); same `LFO2 …`.
`Noise On/Off`, `Noise Level`, `Noise Color`. `Unison On/Off`, `Unison Detune`. `Vib On/Off`, `Vib Amount`
(vibrato — great on leads). `Volume`. Glide, voices and legato are UI choosers unless they appear in the list (verify).

## Recipes

### Bright analog lead (synth-pop)
```
OSC1 Shape Saw, Octave 0; OSC2 Shape Saw, Octave 0, OSC2 Detune +9 ct, OSC2 Semi 0; both Levels 75 %
F1 Type 4-pole lowpass (24 dB); F1 Freq ≈ 3 kHz; F1 Resonance 12 %; F1 Freq < Env +25 %
FEG1 Attack 0, Decay 400 ms, Sustain 40 %, Rel 300 ms
AEG1 Attack 5 ms, Decay 300 ms, Sustain 80 %, Rel 250 ms
Unison On, Unison Detune 20 %; Vib On, Vib Amount 8 % (slow onset if available)
After: Saturator Soft Sine 4 dB, Echo dotted 1/8, Reverb send
```
Why: two detuned saws through a 24 dB filter with a short envelope bite is the 80s lead; vibrato sells the "played" feel.

### Brass stab (chorus chords)
```
OSC1 Saw; OSC2 Saw, OSC2 Detune +12 ct (no 5ths — they muddy chords)
F1 lowpass 24; F1 Freq ≈ 900 Hz; F1 Freq < Env +60 %; FEG1 Attack 60 ms, Decay 350 ms, Sustain 20 %
AEG1 Attack 20 ms, Decay 400 ms, Sustain 60 %, Rel 200 ms
Noise On, Noise Level 8 % (air)
```
Why: the slow filter attack (60 ms) is the brass "wah" onset.

### Warm analog bass (synth-pop octave bass)
```
OSC1 Shape Saw, Octave −1; OSC2 Shape Rectangle, Octave −1, OSC2 Detune 0, OSC2 Level 50 %
F1 lowpass 24; F1 Freq ≈ 350 Hz; F1 Resonance 18 %; F1 Freq < Env +40 %
FEG1 Attack 0, Decay 180 ms, Sustain 10 %; AEG1 Attack 0, Decay 200 ms, Sustain 90 %, Rel 100 ms
Unison Off; Vib Off; Voices mono + glide by hand if not a parameter
After: Saturator 4 dB, Compressor sidechain from kick
```
Why: short filter decay gives the pluck on every 8th; saw + rectangle = fundamental plus bite.

### Slow analog pad
```
OSC1 Saw, OSC2 Saw Detune +7 ct; both to F1
F1 lowpass 12; F1 Freq ≈ 1.2 kHz; F1 Freq < LFO +15 %; LFO1 Sync Hertz, LFO1 Speed 0.12 Hz, LFO1 Shape Triangle
AEG1 Attack 800 ms, Decay 1 s, Sustain 85 %, Rel 2.5 s
Unison On, Unison Detune 30 %
After: Chorus-Ensemble, Reverb send, sidechain Compressor
```

## Verify
Confirm `F1 Freq`, `F1 Resonance`, `OSC2 Detune`, `AEG1 Attack`, `FEG1 Decay`, `LFO1 Speed` in the
read list. `OSC1 Balance` controls routing to F1/F2 — leave at default unless you mean two paths.
