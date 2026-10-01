# Utility (`StereoGain`)

Gain, width, mono, phase and mute. Boring and essential: it is how you mono a sub, keep bass
centred, widen a pad or gain-stage before a distortion.

Load: `load_device(name="Utility", track=i, category="audio_effects")`.

## Parameters

| LOM name | What it does | Start |
|---|---|---|
| `Gain` (`Gain (Legacy)` on old presets) | ±35 dB trim | 0 dB; −6 dB before saturators |
| `Mute` | Hard mute (automatable — stutters) | Off |
| `Left Inv`, `Right Inv` | Polarity flip per channel | Off |
| `Channel Mode` | `Left` / `Right` / `Stereo` / `Swap` | Stereo |
| `Stereo Width` | 0 % mono … 100 % normal … 400 % hyper-wide (M/S scaling) | pad 120–150 %; sub 0 % |
| `Mid/Side Balance` | Shown instead of Width on some versions | — |
| `Mono` | Sum to mono switch | On for sub |
| `Bass Mono`, `Bass Freq` | Mono everything below `Bass Freq`, keep the rest stereo | On, 120 Hz on mid bass / master |
| `Balance` | Stereo balance | 0 |
| `DC Filter` | Removes DC offset (after heavy distortion/FM) | On after Roar/Operator FM |

## Recipes

### Sub: mono and nothing else
```
Mono On (or Stereo Width 0 %); Gain 0 dB; DC Filter On
```
Why: stereo information below 100 Hz cancels on club systems and wastes headroom.

### Mid bass: wide top, mono bottom
```
Bass Mono On; Bass Freq ≈ 120 Hz; Stereo Width 110 %
```
Why: the growl's harmonics can be wide; its weight must be centred.

### Pad width
```
Stereo Width 140 %; Bass Mono On, Bass Freq ≈ 200 Hz
```

### Gain staging before distortion
```
Utility (Gain −6 dB) → Saturator/Roar → Utility (Gain +4 dB)
```
Why: distortion amount depends on input level; the first Utility is a clean "drive" knob you can automate.

### Mute stutter (transition)
```
set_automation on `Mute` with mode "steps": alternate 1/0 every 0.25 beats for the last beat of a build
```

## Verify
`Stereo Width` vs `Mid/Side Balance` and `Gain` vs `Gain (Legacy)` depend on the preset's age — read first.
