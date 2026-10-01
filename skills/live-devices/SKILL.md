---
name: live-devices
description: "Reference for Ableton Live 12 devices and what their parameters do: instruments (Wavetable, Operator, Analog, Drift, Drum Rack, Simpler), audio effects (EQ Eight, Compressor, Multiband Dynamics, Saturator, Roar, Auto Filter, Reverb, Echo, Delay, Chorus-Ensemble, Phaser-Flanger, Utility), MIDI effects (Arpeggiator, Chord, Scale, Velocity); LOM parameter names, starting ranges and recipes (pads, plucks, wobble/growl bass, sidechain pump, OTT). Load when choosing, loading or tweaking a device, when the user wants a sound brighter, wider, fatter, distorted or pumping, or before set_parameter."
---

# Live 12 devices

Tool mechanics are in the `ableton-live` skill. This skill answers "which device, which
parameter, what value, and why does it sound like that".

## Method (every time)

1. **Load by name**: `load_device(name="Wavetable", track=i, category="instruments")`
   (`"audio_effects"` / `"midi_effects"` / `"drums"` for kits). Check `matched.name`; the result's
   `devices` list gives the new `device_path`. Insert position: `after_device_path`.
2. **Read before writing**: `get_devices(track=i, device_path=p, include_params=true)`. Each
   parameter has `name`, `min`, `max`, `value`, `display`, `is_quantized`, `value_items`.
   Device identity is `class_name` (e.g. `InstrumentVector` = Wavetable, `Compressor2` = Compressor).
3. **Set by name**: `set_parameters(track, device_path, values=[{"parameter": "<name>", ...}])`.
   - Quantized (`is_quantized: true`): pass `display` with one of `value_items` (`"Lowpass"`, `"1/8T"`, `"On"`).
   - Continuous: pass `normalized` 0–1 for "about this much", or `value` when the read-back shows
     natural units (ms, dB, semitones). Confirm the resulting `display`, adjust once if needed.
4. **Name-not-found rule**: if a name below is missing (`NOT_FOUND` with `available`), search the
   returned parameter list for the closest name (same words, different abbreviation) and use that.
   Names here come from Live's own device definitions (Live 12.0–12.4), but a few changed between
   point releases; the per-device files mark them. The LOM `name` is what counts, not the UI label.
5. **Explain in one line** what the change does musically, and set `why` on the call.

Values the files quote as "≈ −20 dB", "≈ 1/8" are *display* targets. Reach them with `display`
(quantized) or `normalized` + read-back (continuous); do not assume `value` is in dB or Hz unless `min`/`max` say so.

## What the API cannot set (v1) — tell the user which control to click

- Sidechain **input routing** (Compressor, Glue, Auto Filter, Multiband): the "Audio From" chooser. Threshold/ratio/etc. are settable.
- **Modulation-matrix routings** in Wavetable, Drift and Roar (which source modulates which target). Per-source *amounts* exposed as parameters are listed per device.
- **Rack macro mappings**, Drum Rack **pad assignments** and **choke groups**, Scale's 12×12 grid, Simpler sample loading, Operator/Wavetable **wavetable choice by file**.
- Device **presets** load through `browse(query=..., categories=[...])` + `load_device(uri=...)` — this is often the fastest route to a sound.

## Device index

| Device | Class | Reach for it when | File |
|---|---|---|---|
| Wavetable | `InstrumentVector` | Modern pads, plucks, wobble/growl bass; two oscillators scanning wavetables + sub | [instruments/wavetable.md](instruments/wavetable.md) |
| Operator | `Operator` | FM: clean sub, growl bass, bells, 80s DX-style keys | [instruments/operator.md](instruments/operator.md) |
| Analog | `UltraAnalog` | Virtual-analog leads, brass, warm basses, classic pads | [instruments/analog.md](instruments/analog.md) |
| Drift | `Drift` | Fast, warm analog-style pads/leads with built-in "drift"; the easiest good pad | [instruments/drift.md](instruments/drift.md) |
| Drum Rack | `DrumGroupDevice` | Any drum kit; pads → `drum_pads`, chains hold Simplers | [instruments/drum-rack.md](instruments/drum-rack.md) |
| Simpler | `OriginalSimpler` | One sample as instrument/drum hit/slices; vocal chops | [instruments/simpler.md](instruments/simpler.md) |
| EQ Eight | `Eq8` | Carve space: high-pass pads, tame mud, brighten | [effects/eq-eight.md](effects/eq-eight.md) |
| Compressor | `Compressor2` | Sidechain pump, control dynamics, punch | [effects/compressor.md](effects/compressor.md) |
| Glue Compressor | `GlueCompressor` | Bus glue, drum-bus smash, smooth sidechain | [effects/glue-compressor.md](effects/glue-compressor.md) |
| Multiband Dynamics | `MultibandDynamics` | OTT-style squash, per-band control, de-harsh | [effects/multiband-dynamics.md](effects/multiband-dynamics.md) |
| Saturator | `Saturator` | Warmth to heavy distortion, bass harmonics | [effects/saturator.md](effects/saturator.md) |
| Roar | `Roar` | Live 12 multi-stage coloration/distortion with filters, feedback and modulation | [effects/roar.md](effects/roar.md) |
| Auto Filter | `AutoFilter` | LFO wobble, envelope wah, build-up sweeps | [effects/auto-filter.md](effects/auto-filter.md) |
| Reverb | `Reverb` | Space; pads and snares; on return tracks | [effects/reverb.md](effects/reverb.md) |
| Echo | `Echo` | Characterful synced delay with filter, ducking, wobble, reverb tail | [effects/echo.md](effects/echo.md) |
| Delay | `Delay` | Plain synced/ping-pong delay | [effects/delay.md](effects/delay.md) |
| Chorus-Ensemble | `Chorus2` | Width and 80s shimmer on pads, leads | [effects/chorus-ensemble.md](effects/chorus-ensemble.md) |
| Phaser-Flanger | `PhaserNew` | Sweeping movement, jet flanges, doubling | [effects/phaser-flanger.md](effects/phaser-flanger.md) |
| Utility | `StereoGain` | Gain, mono/width, bass mono, mute | [effects/utility.md](effects/utility.md) |
| Arpeggiator | `MidiArpeggiator` | Synth-pop 1/16 arps from held chords | [midi-effects/arpeggiator.md](midi-effects/arpeggiator.md) |
| Chord | `MidiChord` | Stack intervals on single notes | [midi-effects/chord.md](midi-effects/chord.md) |
| Scale | `MidiScale` | Force notes into key | [midi-effects/scale.md](midi-effects/scale.md) |
| Velocity | `MidiVelocity` | Shape/limit/randomize velocity | [midi-effects/velocity.md](midi-effects/velocity.md) |

Live 12 additions in this set: **Roar** (new in 12.0) and **Drift** (added in 11.3, standard in 12).
Live 12 Suite also ships **Meld** (`InstrumentMeld`), a macro-oscillator synth; not covered here.

## Chains that work (signal order)

- **Pad (synth-pop)**: Drift or Wavetable → EQ Eight (low cut 180 Hz) → Chorus-Ensemble → Compressor (sidechain from kick) → send to Reverb return.
- **Lead**: Analog or Wavetable → Saturator (light) → Echo (dotted 1/8, ducked) → send Reverb.
- **Mid bass (riddim)**: Wavetable or Operator (mono) → EQ Eight (low cut 90 Hz) → Roar or Saturator → Auto Filter (LFO wobble, if the synth has none) → Multiband Dynamics (OTT, Amount 40 %) → Utility (Bass Mono 120 Hz).
- **Sub**: Operator sine → Utility (Mono) → Compressor (light, 2:1). Nothing else.
- **Drum bus**: Glue Compressor (2:1, slow attack) → Saturator (soft) → EQ Eight.
- **Master**: leave it alone unless asked; never add a limiter without saying so.

## Quick translations of what users say

| They say | Do |
|---|---|
| brighter / dull | Filter freq up; EQ high shelf +2–3 dB at 6–10 kHz; shorter filter decay |
| warmer | Saturator Soft Sine 3–6 dB; EQ low shelf +1–2 dB at 150 Hz; Drift `Drift` up |
| wider | Chorus-Ensemble; Utility `Stereo Width` 120–150 %; Wavetable `Unison Amount` |
| fatter bass | Sub osc/gain up; Saturator; Unison off below 150 Hz; Bass Mono |
| pumping | Compressor sidechain, release 150–250 ms (see compressor.md) |
| wobble | Synth LFO → filter/position (matrix by hand) or Auto Filter LFO synced 1/8 |
| growl | Operator FM with LFO on modulator level; Wavetable FM mode + Roar |
| punchier drums | Compressor attack 10–30 ms, Glue on the bus, Saturator Hard Curve |
| more space | Reverb send up, predelay 20 ms, longer Echo feedback |
| tighter / cleaner | Shorter releases, low cut everything but kick/sub, less reverb |
