# Roar (`Roar`) — Live 12

Three gain stages (each: a **shaper** with twelve curve types and a **filter**), six routing modes
(Single, Serial, Parallel, Multi Band, Mid Side, Feedback), an input **Tone** section, a feedback
path with its own time/pitch, built-in compression, and a modulation section (two LFOs, envelope
follower, noise). The dubstep "bass distortion that moves" device.

Load: `load_device(name="Roar", track=i, category="audio_effects")`.
Parameter names below come from Live 12's Roar definitions; descriptions of shaper/routing modes
come from Ableton's Roar material. Shaper type strings: read `value_items` (known names include
Soft Sine, Diode Clipper, Tube Preamp, Polynomial, Fractal, Noise Injection, Shards).

## Input section

| LOM name | What it does | Start |
|---|---|---|
| `Drive` | Level into the gain stages — overall distortion amount | 6–12 dB bass |
| `Tone Amt`, `Tone Freq` | Pre-shaper tilt: positive values attenuate lows below `Tone Freq` so bass does not turn to mud | +20 % at 150 Hz |
| `Color On` | "Color compensation": attenuates the tone shift before the shaper and restores it after | On |
| `Routing` | Mode chooser — **not a plain parameter** (control-surface enum). Ask the user to pick it in the device | Single / Serial |
| `Blend` | Mix between stages in Serial/Parallel/Mid Side/Feedback | 50 % |
| `Low Mid X-Over`, `Mid High X-Over` | Band splits in Multi Band mode | 150 Hz / 2.5 kHz |

## Stages 1–3 (`Shaper N …`, `Flt N …`, N = 1, 2, 3)

| LOM name | What it does | Start (stage 1, bass) |
|---|---|---|
| `Stage N On`, `Shaper N On`, `Flt N On` | Enables | On / On / On |
| `Shaper N Type` | Curve (quantized) | Diode Clipper or Tube Preamp |
| `Shaper N Amt` | Distortion depth of this stage | 40–60 % |
| `Shaper N Bias` | DC offset into the curve — asymmetric, adds even harmonics / "snarl" | 5–15 % |
| `Shaper N Level` | Stage output | 0 dB |
| `Flt N Type` | Filter type (incl. `Morph`, `Peak`; read `value_items`) | Lowpass |
| `Flt N Freq`, `Flt N Res` | Cutoff / resonance | 2 kHz / 15 % |
| `Flt N Morph`, `Flt N Peak` | Extra control for Morph / Peak types | — |
| `Flt N Pre On` | Filter *before* the shaper (shapes what gets distorted) instead of after (tames fizz) | Off (post) for taming; On for "talking" |

## Feedback

`Fb Amt` (amount), `Fb Time Mode` (`Time` / `Synced` / `Triplet` / `Dotted` / note), `Fb Time`, `Fb Synced`,
`Fb Note` (pitch-based delay time), `Fb Freq`, `Fb Width` (band-pass on the feedback), `Fb Inv On`
(invert), `Fb Gate On` (gate the feedback). Only audible in Feedback routing — makes risers, drones and metallic tails.

## Modulation and dynamics

`LFO 1 Wave`, `LFO 1 Rate Mode` (`Free`/`Synced`/`Triplet`/`Dotted`/`Sixteenth`), `LFO 1 Rate`,
`LFO 1 Synced Rate`, `LFO 1 16th`, `LFO 1 Morph`, `LFO 1 Smooth`; same for `LFO 2 …`.
`Env Attack`, `Env Release`, `Env Thresh`, `Env Gain`, `Env Freq`, `Env Width` (envelope follower).
`Noise Type`, `Noise Rate Mode`, `Noise Rate`, `Noise Synced Rate`, `Noise 16th`, `Noise Smooth`.
`Global Mod Amt` scales all modulation. **Routing a modulator to a target is a matrix cell (by hand)**;
tell the user: "In Roar's Mod tab, set LFO 1 → Flt 1 Freq to 40 %".
`Comp Amt` (built-in compressor after the stages), `Comp Hp On` (its high-pass sidechain), `Output`, `Dry/Wet`.

## Recipes

### Bass distortion stage (riddim) — Single routing
```
Drive 10 dB; Tone Amt +25 %, Tone Freq ≈ 120 Hz; Color On
Shaper 1 Type Diode Clipper; Shaper 1 Amt 55 %; Shaper 1 Bias 10 %
Flt 1 Pre On Off; Flt 1 Type Lowpass; Flt 1 Freq ≈ 3 kHz; Flt 1 Res 10 %
Comp Amt 30 %; Output −6 dB; Dry/Wet 100 %
Chain: EQ Eight low cut 90 Hz → Roar → Multiband Dynamics (OTT 40 %) → Utility Bass Mono 120 Hz
```
Why: clipping the mids adds the harmonics that make the growl aggressive; the post-filter removes the fizz above 3 kHz; the compressor evens out the result.

### Multiband growl — ask the user to set Routing = Multi Band
```
Low Mid X-Over ≈ 150 Hz; Mid High X-Over ≈ 2 kHz
Stage 1 (low): Shaper 1 Type Soft Sine, Shaper 1 Amt 15 %  (keep the low end clean)
Stage 2 (mid): Shaper 2 Type Tube Preamp, Shaper 2 Amt 70 %, Shaper 2 Bias 15 %
Stage 3 (high): Shaper 3 Type Diode Clipper, Shaper 3 Amt 40 %, Flt 3 Lowpass ≈ 6 kHz
Drive 8 dB; Comp Amt 25 %; Output −6 dB
```
Why: distorting each band separately keeps the sub-ish lows solid while the mids snarl.

### "Talking" distortion — LFO on a pre-filter
```
Single routing; Shaper 1 Tube Preamp 60 %; Flt 1 Pre On On; Flt 1 Type Bandpass (or Morph); Flt 1 Freq ≈ 600 Hz; Flt 1 Res 35 %
LFO 1 Rate Mode Triplet; LFO 1 Synced Rate 1/8; LFO 1 Wave Triangle
(by hand) Mod matrix: LFO 1 → Flt 1 Freq +45 %
```
Why: moving the filter *before* the shaper changes which harmonics get generated — vowel-like movement in time with the riddim triplets.

### Riser / drone — Feedback routing (by hand)
```
Fb Amt 60 %; Fb Time Mode Synced; Fb Synced 1/8; Fb Freq ≈ 1 kHz; Fb Width 50 %; Fb Gate On Off
Shaper 1 Soft Sine 40 %; automate Fb Amt 30 → 85 % over the build with set_automation
```

## Verify
Check `Shaper 1 Type` `value_items` for exact names; check whether `Routing` appears in the
parameter list (if it does, set it with `display`; if not, it is by hand). Level-match with `Output`.
