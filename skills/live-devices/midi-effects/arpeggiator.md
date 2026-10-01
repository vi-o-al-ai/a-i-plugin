# Arpeggiator (`MidiArpeggiator`)

Turns held chords into note sequences. Put it **before** the instrument on a MIDI track; write
sustained chords in the clip (see `midi-writing/chords.md`) and let the device make the 1/16s.
Use MIDI notes instead when the pattern must differ per chord or needs exact velocities.

Load: `load_device(name="Arpeggiator", track=i, category="midi_effects")`.
Two LOM names carry Ableton's own typo: `Tranpose Mode` and `Tranpose Key` (no "s"). Use them as spelled.

## Parameters

| LOM name | UI | What it does | Start |
|---|---|---|---|
| `Style` | Style | Order: Up, Down, UpDown, DownUp, Up & Down, Down & Up, Converge, Diverge, Con & Diverge, Pinky Up/UpDown, Thumb Up/UpDown, Play Order, Chord Trigger, Random, Random Other, Random Once (read `value_items`) | Up |
| `Sync On` | Sync | Tempo-synced rate | On |
| `Synced Rate` | Rate | Division (`1/16`, `1/8`, `1/8T` …) | 1/16 synth-pop; 1/8 slower |
| `Free Rate` | Rate (ms) | When unsynced | — |
| `Gate` | Gate | Note length as % of the step | 50–70 % pluck; 100 % legato |
| `Offset` | Offset | Rotates the start step of the pattern | 0 |
| `Groove` | Groove | Swing amount | 0; 20 % for lilt |
| `Hold On` | Hold | Keeps arpeggiating after keys release | Off (On for live jamming) |
| `Repeats` | Repeats | How many cycles before stopping (inf default) | inf |
| `Retrigger Mode` | Retrigger | `Off` / `Note` / `Beat` — restart the pattern | Beat for tight loops |
| `Ret. Interval` | Interval | Beat interval for Beat retrigger | 1 bar |
| `Tranpose Mode` | Transpose | `Shift` / `Major` / `Minor` (how steps are transposed) | Shift (octaves) |
| `Tranpose Key` | Key | Root for Major/Minor transposition | set to song key |
| `Transp. Steps` | Steps | How many transposed repeats are added | 1 (2 octaves total) |
| `Transp. Dist.` | Distance | Transposition per step (semitones or scale steps) | +12 |
| `Velocity On` | Velocity | Enable velocity shaping | On |
| `Velocity Decay` | Decay | Fade velocity over time (ms) | 0; 2000 ms for echo-like fade |
| `Velocity Target` | Target | Velocity the decay heads to | 40 |
| `Vel. Retrigger` | Retrigger | Restart the decay on new notes | On |

## Recipes

### Synth-pop 1/16 arp over held chords
```
Style Up; Sync On; Synced Rate 1/16; Gate 60 %; Retrigger Mode Beat; Ret. Interval 1 bar
Tranpose Mode Shift; Transp. Steps 1; Transp. Dist. +12 (adds the octave above)
Clip: 4-beat chord voicings from chords.md; velocity 100
Instrument: pluck patch (Wavetable "Plucky arp lead"); Echo dotted 1/8 after
```
Why: Beat retrigger means every bar starts on the chord's lowest note, so the arp lines up with the kick.

### Up-down octave shimmer (intro)
```
Style UpDown; Synced Rate 1/8; Gate 90 %; Transp. Steps 2; Transp. Dist. +12; Groove 0
```

### Riddim stutter from a single bass note
```
Style Up (single note = repeats); Synced Rate 1/16 or 1/8T; Gate 40 %; Velocity On; Velocity Decay 600 ms; Velocity Target 30; Vel. Retrigger On
```
Why: a repeating single note with fading velocity is a quick machine-gun fill before the drop.

### Chord Trigger (rhythmic chord stabs without writing stabs)
```
Style Chord Trigger; Synced Rate 1/8; Gate 50 %; Offset 1 (puts hits on the off-beats)
```

## Verify
`Style`/`Synced Rate`/`Retrigger Mode` via `display`; confirm the typo'd names exist. Rate and
Gate are what the user will want to tweak by ear — A/B them.
