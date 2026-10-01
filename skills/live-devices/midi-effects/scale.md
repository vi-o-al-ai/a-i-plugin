# Scale (`MidiScale`)

Maps incoming pitches onto allowed pitches: a safety net that forces notes into key. The 12×12
mapping grid itself is **not a parameter** — load a preset for the mode (Major, Minor, Dorian…)
and set the root with `Base`.

Load a preset: `browse(query="Minor", categories=["midi_effects"])` → pick the Scale preset →
`load_device(uri=..., track=i)`. Or `load_device(name="Scale", track=i, category="midi_effects")`
for the default (chromatic-ish) grid and ask the user to click the grid.

## Parameters

| LOM name | What it does | Start |
|---|---|---|
| `Base` | Root note of the grid (C … B) | song key root |
| `Transpose` | Shift output in semitones after mapping | 0 |
| `Range` | Width of the input range that gets mapped (semitones) | 12 |
| `Lowest` | Bottom note of that range | C-2 (all) |
| `Fold` | Folds notes outside the range back inside | Off |

## Recipes

### Lock a lead to F minor
```
Load the "Minor" Scale preset (browse → load_device by uri); Base F; Transpose 0
```
Why: the Scale device converts wrong notes into right ones in real time — good for a beginner
jamming on a keyboard. Written MIDI should already be in key (`midi-writing/melody.md`).

### Make Chord-device triads correct
Chord (+3/+4, +7) → Scale (song key). The 3rds snap to major/minor per degree.

### Pentatonic "can't miss" lead
Load a Pentatonic preset (minor pentatonic for dubstep leads), Base = key.

## Caveats
- A Scale device after a sub bass can shift the root; never put it on the sub track.
- Live 12's clip-level scale highlighting (`set_scale`) is only visual; this device actually changes notes.

## Verify
Read `Base` `value_items` (note names) and set via `display`.
