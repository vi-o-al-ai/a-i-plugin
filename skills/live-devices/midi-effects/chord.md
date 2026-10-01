# Chord (`MidiChord`)

Adds up to six fixed intervals to every incoming note. Great for octaves and 5ths; dangerous for
3rds (a fixed interval gives the wrong chord quality on other scale degrees — add a Scale device
after it, or write the chords as notes instead; see `midi-writing/chords.md`).

Load: `load_device(name="Chord", track=i, category="midi_effects")`.

## Parameters

| LOM name | What it does | Range |
|---|---|---|
| `Shift1` … `Shift6` | Interval in semitones added to each note (0 or disabled = no extra note; read `min`/`max`, typically −36…+36) | +12 octave, +7 fifth, +4 major 3rd, +3 minor 3rd, −12 octave down |
| `Velocity1` … `Velocity6` | Velocity of each added note as % of the original | 50–100 % |

## Recipes

### Octave stack for a lead
```
Shift1 +12, Velocity1 70 %
```
Why: the octave doubles brightness without changing harmony — safe on every note.

### Power chord / 5ths (minor-key riffs, dubstep lead)
```
Shift1 +7, Velocity1 90 %; Shift2 +12, Velocity2 60 %
```
Why: root + 5th + octave has no 3rd, so it fits major and minor equally.

### Triad from one finger (then correct it)
```
Minor: Shift1 +3, Shift2 +7   ·   Major: Shift1 +4, Shift2 +7
Follow with Scale set to the song key so the 3rds snap to the right quality on each degree
```

### Octave-down thickening (audition only)
```
Shift1 −12, Velocity1 100 %
```
Why: quick way to hear a bass line an octave lower. For the real track give the sub its own
instrument and its own notes (`midi-writing/bass.md`) so it can be mixed and sidechained separately.

## Verify
Read `Shift1`'s `min`/`max`/`display`; set with `value` in semitones once the unit is confirmed.
