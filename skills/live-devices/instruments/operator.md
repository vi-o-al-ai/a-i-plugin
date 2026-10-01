# Operator (`Operator`)

Four-oscillator FM synth. One oscillator you hear (the carrier, usually A); the others modulate
it to add harmonics. Modulator **level** = how much distortion of the carrier's sine; modulator
**ratio** (`Coarse`) = which harmonics appear. The cleanest sub in Live and the fastest growl.

Load: `load_device(name="Operator", track=i, category="instruments")`.

## Oscillators A–D

Prefixes: `Osc-A …`, `A …`, `Ae …` (A's envelope); same for B, C, D.

| LOM name | What it does | Start |
|---|---|---|
| `Osc-A On` | Enable | A on; B/C/D as needed |
| `Osc-A Wave` | Waveform (Sine, Saw, Square, Triangle, noise variants; read `value_items`) | Sine |
| `A Coarse` | Frequency ratio vs. the note (1 = fundamental, 2 = octave, 3 = 12th…) | Carrier 1; modulator 1 (gritty) or 2 (hollow) |
| `A Fine` | Fine ratio (0–1000) — tiny values add beating | 0 |
| `A Fix On` | Fixed frequency instead of key-tracked (some builds spell this LOM name with a trailing space — match the read list exactly; verify by read-back) | Off |
| `A Fix Freq`, `A Fix Freq Mul` | Fixed frequency and multiplier | — |
| `Osc-A Level` | Output (carrier) or modulation depth (modulator) | Carrier 0 dB; modulator −20 to −6 dB |
| `Osc-A Lev < Vel`, `Osc-A Lev < Key` | Velocity/key scaling of level | modulator Lev<Vel +30 % for expressive growl |
| `Osc-A Phase`, `Osc-A Retrig` | Start phase, retrigger per note | Retrig On for consistent bass |
| `A Quantize`, `A Freq<Vel` | Pitch quantize, velocity → pitch | 0 |
| `Ae Attack`, `Ae Decay`, `Ae Sustain`, `Ae Release` | Per-oscillator envelope. On a modulator this is *timbre over time* | see recipes |
| `Ae Init`, `Ae Peak`, `Ae End` | Envelope levels (Level view) | — |
| `Ae Mode`, `Ae Loop`, `Ae Retrig`, `Ae R < Vel` | Loop/beat-sync modes, velocity → release | — |
| `Algorithm` | How A–D connect (quantized, 11 shapes). First item = D→C→B→A serial stack | Serial for growl; "all parallel" for additive |

## Filter

`Filter On`, `Filter Type` (`Lowpass`/`Highpass`/`Bandpass`/`Notch`/`Morph`), `Filter Freq`, `Filter Res`,
`Filter Circuit - LP/HP`, `Filter Circuit - BP/NO/Morph`, `Filter Morph`, `Filter Slope`, `Filt < Vel`,
`Filt < Key`, `Filt < LFO`. Filter envelope `Fe Attack/Decay/Sustain/Release`, `Fe Amount` (depth, ±),
`Fe R < Vel`, `Fe Mode`, `Fe Loop`/`Fe Retrig`, level-view `Fe Init/Peak/End`.
Waveshaper after the filter: `Shaper Type`, `Shaper Drive`, `Shaper Mix` — Operator's built-in distortion.

## LFO

`LFO On`, `LFO Type` (shape), `LFO Range` (`Low`/`High`/`Sync`), `LFO Rate` (Hz) or `LFO Sync` (division
when Range = Sync), `LFO Amt`, `LFO Retrigger`, `LFO R < K`, `LFO < Vel`. Destinations are switches per
oscillator: `Osc-A < LFO` … `Osc-D < LFO`, `Filt < LFO`, plus `LFO Amt A`, `LFO Dst B`, `LFO Amt B`.
LFO envelope: `Le Attack/Decay/Sustain/Release`, `Le Mode`, `Le Loop`/`Le Retrig`.
Routing the LFO to a **modulator's level/pitch** is the growl.

## Pitch envelope and glide

`Pe On`, `Pe Attack/Decay/Sustain/Release`, `Pe Init/Peak/End`, `Pe Amount`, `Pe R < Vel`, destinations
`Osc-A < Pe` … `Osc-D < Pe`, `LFO < Pe`, `Pe Amt A`, `Pe Dst B`, `Pe Amt B`. `Glide On`, `Glide Time`
(portamento — bass slides), `Spread` (stereo detune of voices; 0 for bass).

## Global

`Transpose`, `Tone` (global high-frequency rolloff), `Time` (scales all envelopes), `Panorama`,
`Pan < Rnd`, `Pan < Key`, `Time < Key`, `Volume`. Polyphony/voices is a UI chooser; if no `Voices`
parameter appears, ask the user to set Voices = 1 for mono bass (verify in Live).

## Recipes

### Clean sub (the dubstep sub track)
```
Algorithm: any; Osc-A On, Osc-A Wave Sine, A Coarse 1, Osc-A Level 0 dB; Osc-B/C/D Off
Ae Attack 2 ms, Ae Decay 0, Ae Sustain 100 %, Ae Release 150 ms
Filter On Off; Glide On On, Glide Time 40 ms; Spread 0; Voices 1 (by hand if not a parameter)
Notes: root only, 24–40, typically 28–40 (see `midi-writing/bass.md`)
```
Why: one sine at the root is the whole job; glide ties repeated notes without clicks.

### FM growl bass (riddim)
```
Algorithm: serial stack (B → A)
Osc-A: Sine, A Coarse 1, Level 0 dB
Osc-B On: Sine or Saw, B Coarse 1 (gritty) or 2 (hollower), Osc-B Level −14 dB  ← this is the "growl amount"
Be Attack 0, Be Decay 500 ms, Be Sustain 40 %, Be Release 100 ms   ← timbre opens then settles
LFO On; LFO Type Triangle; LFO Range Sync; LFO Sync 1/8T; LFO Amt 45 %; Osc-B < LFO On; LFO Retrigger On
Filter On; Lowpass 24; Filter Freq ≈ 500 Hz; Filter Res 20 %; Fe Amount +30 %; Fe Decay 400 ms
Shaper Type Soft; Shaper Drive 30 %; Shaper Mix 100 %
Glide On, Glide Time 60 ms; Spread 0; Tone 70 %
After: Roar/Saturator → OTT → Utility Bass Mono; keep the sub on its own Operator track
```
Why: the LFO moves the modulator's level, which changes how many harmonics the carrier gets —
that is the vowel-like "growl". Triplet sync matches riddim hats.

### FM bell / pluck (synth-pop top layer)
```
Algorithm: B → A
Osc-A Sine, A Coarse 1; Osc-B Sine, B Coarse 3 + B Fine 500 (a 3.5 ratio; or B Coarse 7 for glassier), Osc-B Level −10 dB
Be Attack 0, Be Decay 1.2 s, Be Sustain 0            ← harmonics fade before the note does
Ae Attack 0, Ae Decay 2 s, Ae Sustain 0, Ae Release 600 ms
Spread 30 %; Tone 60 %
After: Echo dotted 1/8, Reverb send
```
Why: non-integer ratios give inharmonic bell partials; a fast-decaying modulator = bright attack, pure tail.

### DX-style electric piano (80s keys)
```
Algorithm: two stacks (B → A and D → C) if available, else B → A
A Coarse 1, Osc-A Level 0 dB; B Coarse 1, Osc-B Level −18 dB, Be Decay 800 ms, Be Sustain 20 %
C Coarse 1, Osc-C Level −6 dB; D Coarse 14, Osc-D Level −30 dB, De Decay 300 ms, De Sustain 0 (the "tine")
Ae/Ce Attack 0, Decay 3 s, Sustain 30 %, Release 400 ms
Osc-B Lev < Vel +50 % (harder = brighter)
After: Chorus-Ensemble, light Compressor
```

## Verify
Confirm `A Fix On` (with or without a trailing space), `Osc-B Level`, `Be Decay`, `LFO Sync`, `Shaper Drive` in the read
list; if `Algorithm` display names look different, pick by `value_items` index and describe the
shape to the user.
