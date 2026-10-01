# Simpler (`OriginalSimpler`)

One sample, played three ways: **Classic** (pitched, looping, polyphonic — pads, keys), **One-Shot**
(drum hits, vocal shots), **Slicing** (chop a loop across the keyboard). Inside Drum Racks every
pad is usually a Simpler. Sample loading is by hand (drag into the device) in v1.

Load: `load_device(name="Simpler", track=i, category="instruments")`, or pick a Simpler preset
(`browse(query="...", categories=["instruments","sounds"])`).

## Playback (names depend on `Mode`)

| LOM name | Mode | What it does | Start |
|---|---|---|---|
| `Mode` | all | `Classic` / `One-Shot` / `Slicing` (quantized) | — |
| `Start`, `End` | all | Sample start/end (0–1 of the file) | trim silence |
| `S Start`, `S Length`, `S Loop Length`, `S Loop Fade` | Classic | Playback start, length, loop length and crossfade | loop on for pads |
| `Fade In`, `Fade Out` | One-Shot | Envelope on the shot | 0 / 5 ms |
| `Trigger Mode` | One-Shot | Trigger vs Gate | Trigger for drums |
| `Slice by`, `Sensitivity`, `Division`, `Regions`, `Playback`, `Nudge` | Slicing | Transient/Beat/Region/Manual slicing, mono/poly | Beat 1/16 for breaks |
| `Transpose`, `Detune` | all | Semitones / cents | tune drum hits to key |
| `Gain`, `Volume`, `Pan`, `Spread`, `Pan < Rnd` | all | Level, pan, stereo spread, random pan | — |
| `Voices`, `Retrigger`, `Glide Mode`, `Glide Time`, `Vol < Vel` | Classic/Slicing | Polyphony, mono glide, velocity → volume | Vol < Vel 60 % on drums |
| `Warp`, `Warp Mode`, `Preserve`, `Loop Mode`, `Envelope`, `Grain Size Tones`, `Grain Size Texture`, `Flux` | all | Tempo-sync the sample; Beats/Tones/Texture/Re-Pitch/Complex modes | Warp On for loops |
| `PB Range`, `Note PB` | all | Pitch-bend range | — |

## Envelopes

Amp: `Ve Attack`, `Ve Decay`, `Ve Sustain`, `Ve Release`, `Ve Mode`, `Ve Retrig`.
Filter: `Fe On`, `Fe Attack/Decay/Sustain/Release`, `Fe < Env` (depth).
Pitch: `Pe On`, `Pe Attack/Decay/Sustain/Release`, `Pe < Env` (depth; pitch drop on kicks).

## Filter and LFO

`F On`, `Filter Type` (`Lowpass`/`Highpass`/`Bandpass`/`Notch`/`Morph`), `Filter Freq`, `Filter Res`,
`Filter Circuit - LP/HP`, `Filter Circuit - BP/NO/Morph`, `Filter Morph`, `Filter Slope`, `Filt < Vel`, `Filt < LFO`.
LFO: `L On`, `L Wave`, `L Sync` (`Free`/synced), `L Rate` / `L Sync Rate`, `L Attack`, `L R < Key`,
`L Retrig`, `L Offset`, `Vol < LFO`, `Pitch < LFO`, `Pan < LFO`.

## Recipes

### Drum hit inside a rack (kick/snare/hat)
```
Mode One-Shot; Trigger Mode Trigger; Fade Out 5 ms
Kick: Transpose to key (±2 st), Ve/Fade so the tail is 150–300 ms (dubstep) or 300–500 ms (house)
Snare: Filter Lowpass ≈ 8 kHz if harsh; Vol < Vel 40 %
Closed hat: Fade Out so decay ≈ 80 ms; Spread 10 %
```
Why: short, in-key kicks leave room for the sub; velocity-to-volume makes hat patterns breathe.

### Vocal chop / sample pad (synth-pop)
```
Mode Classic; Warp On, Warp Mode Complex or Tones; S Loop Length to a clean phrase; S Loop Fade 20 %
Ve Attack 10 ms, Ve Release 300 ms; Filter Lowpass ≈ 6 kHz; Spread 40 %
Voices 4; play chords from midi-writing/chords.md an octave up
After: Echo dotted 1/8, Reverb send
```

### Slice a drum break
```
Mode Slicing; Slice by Beat; Division 1/16; Playback Mono
Write a 16th-note MIDI pattern across the slice notes (read which pitches hold slices: Live maps slices from C1 = 36 upward)
```
Why: re-sequencing slices keeps the break's sound but gives you the half-time grid you want.

### 808 kick with pitch drop
```
Mode One-Shot or Classic; Pe On On; Pe < Env +24 st; Pe Decay 60 ms; Pe Sustain 0
Ve Decay 400 ms, Ve Sustain 0; Transpose to key
```

## Verify
Parameter names switch with `Mode` (One-Shot shows `Fade In`/`Fade Out`; Classic shows `Ve …`).
Set `Mode` first, re-read, then set the rest.
