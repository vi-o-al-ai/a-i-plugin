# Chords, voicings and pads

## Pitch tables (Live convention: C3 = 60)

| Note | pc | oct 0 | oct 1 | oct 2 | oct 3 | oct 4 |
|---|---|---|---|---|---|---|
| C | 0 | 24 | 36 | 48 | 60 | 72 |
| C#/Db | 1 | 25 | 37 | 49 | 61 | 73 |
| D | 2 | 26 | 38 | 50 | 62 | 74 |
| D#/Eb | 3 | 27 | 39 | 51 | 63 | 75 |
| E | 4 | 28 | 40 | 52 | 64 | 76 |
| F | 5 | 29 | 41 | 53 | 65 | 77 |
| F#/Gb | 6 | 30 | 42 | 54 | 66 | 78 |
| G | 7 | 31 | 43 | 55 | 67 | 79 |
| G#/Ab | 8 | 32 | 44 | 56 | 68 | 80 |
| A | 9 | 33 | 45 | 57 | 69 | 81 |
| A#/Bb | 10 | 34 | 46 | 58 | 70 | 82 |
| B | 11 | 35 | 47 | 59 | 71 | 83 |

Registers: sub bass 24–36 · bass 36–55 · chords/pads 55–76 · leads 67–91. Keep chords above
~55 (G2); triads lower than that turn to mud.

Scale intervals: major `[0,2,4,5,7,9,11]`, natural minor `[0,2,3,5,7,8,10]`.
Chord intervals from the root: major `[0,4,7]`, minor `[0,3,7]`, dim `[0,3,6]`, add9 `+14`,
maj7 `+11`, min7 `+10`, sus2 `[0,2,7]`, sus4 `[0,5,7]`, power/5th `[0,7,12]`.

Diatonic chords — major key: I ii iii IV V vi vii° · natural minor: i ii° III iv v VI VII.

## Progressions

| Name | Degrees | C major | F minor | Feel |
|---|---|---|---|---|
| The pop loop | I–V–vi–IV | C G Am F | — | Bright, anthemic chorus; the Empire-of-the-Sun lane. |
| Pre-chorus lift | vi–IV–I–V | Am F C G | — | Starts shadowed, lands bright; same chords, new start point. |
| Doo-wop | I–vi–IV–V | C Am F G | — | Nostalgic, 50s; V at the end pulls hard back to I. |
| Minor epic | i–VI–III–VII | — | Fm Db Ab Eb | Cinematic minor; dubstep intros/breaks, synth-pop verses in minor. |
| Minor oscillator | i–VII–VI–VII | — | Fm Eb Db Eb | Never resolves; tension for builds and drops. |

Transpose any progression by adding the same offset to every pitch (`transpose_notes` does this
in Live). C major → G major = +7; F minor → G minor = +2; F minor → E minor = −1.

## Voicing

- **Close**: triad inside one octave (`60 64 67`). Clear, punchy; use for stabs.
- **Spread / open**: drop the middle note an octave or put the root low and the 3rd on top
  (`48 55 64` or `48 64 67 74`). Wide, lush; use for pads. Never put the 3rd below ~50.
- **Inversions for smooth movement**: between chords, keep common tones and move the others by
  1–2 semitones. Pads then "breathe" instead of jumping. Rule of thumb: pick the inversion whose
  lowest note is nearest the previous chord's lowest note.
- **Lush extensions**: add the 9th (root + 14) on top of pads; add a maj7 (root + 11) on IV and I;
  min7 (root + 10) on vi and ii. Avoid 9ths on the diminished chord.
- **Low end belongs to the bass track**: do not double the root below 48 inside the pad; let the
  bass/sub own it ([bass.md](bass.md)).

### Worked voice-leading, C major I–V–vi–IV (pads around 60–72)

| Chord | Pitches | Note names | Movement from previous |
|---|---|---|---|
| C | 64 67 72 | E G C | — |
| G | 62 67 71 | D G B | E→D, G stays, C→B |
| Am | 60 64 69 | C E A | D→C, G→E, B→A |
| F | 60 65 69 | C F A | C stays, E→F, A stays |

### Worked voice-leading, F minor i–VI–III–VII

| Chord | Pitches | Note names | Movement |
|---|---|---|---|
| Fm | 60 65 68 | C F Ab | — |
| Db | 61 65 68 | Db F Ab | C→Db only |
| Ab | 60 63 68 | C Eb Ab | Db→C, F→Eb, Ab stays |
| Eb | 58 63 67 | Bb Eb G | C→Bb, Eb stays, Ab→G |

All pitches are in F natural minor (F G Ab Bb C Db Eb).

## Sustained pads: 4-beat chords, 16-beat clip

`create_clip(length=16.0)`, then one chord per bar. Duration 4.0 butts each chord against the
next (legato); use 3.9 if the synth clicks on retrigger. Velocity ~90, even.

C major I–V–vi–IV:
```json
[
 {"pitch":64,"start":0.0,"duration":4.0,"velocity":90},
 {"pitch":67,"start":0.0,"duration":4.0,"velocity":90},
 {"pitch":72,"start":0.0,"duration":4.0,"velocity":90},
 {"pitch":62,"start":4.0,"duration":4.0,"velocity":90},
 {"pitch":67,"start":4.0,"duration":4.0,"velocity":90},
 {"pitch":71,"start":4.0,"duration":4.0,"velocity":90},
 {"pitch":60,"start":8.0,"duration":4.0,"velocity":90},
 {"pitch":64,"start":8.0,"duration":4.0,"velocity":90},
 {"pitch":69,"start":8.0,"duration":4.0,"velocity":90},
 {"pitch":60,"start":12.0,"duration":4.0,"velocity":90},
 {"pitch":65,"start":12.0,"duration":4.0,"velocity":90},
 {"pitch":69,"start":12.0,"duration":4.0,"velocity":90}
]
```
12 notes. Lush version: add a 9th on top of each chord — 74 (D) on C, 69 (A) on G, 71 (B) on Am,
67 (G) on F — at velocity 80.

F minor i–VI–III–VII:
```json
[
 {"pitch":60,"start":0.0,"duration":4.0,"velocity":90},
 {"pitch":65,"start":0.0,"duration":4.0,"velocity":90},
 {"pitch":68,"start":0.0,"duration":4.0,"velocity":90},
 {"pitch":61,"start":4.0,"duration":4.0,"velocity":90},
 {"pitch":65,"start":4.0,"duration":4.0,"velocity":90},
 {"pitch":68,"start":4.0,"duration":4.0,"velocity":90},
 {"pitch":60,"start":8.0,"duration":4.0,"velocity":90},
 {"pitch":63,"start":8.0,"duration":4.0,"velocity":90},
 {"pitch":68,"start":8.0,"duration":4.0,"velocity":90},
 {"pitch":58,"start":12.0,"duration":4.0,"velocity":90},
 {"pitch":63,"start":12.0,"duration":4.0,"velocity":90},
 {"pitch":67,"start":12.0,"duration":4.0,"velocity":90}
]
```
12 notes. For the dubstep "minor oscillator" (Fm Eb Db Eb) reuse these voicings:
Fm `60 65 68`, Eb `58 63 67`, Db `61 65 68`, Eb `58 63 67`.

Two chords per bar (faster harmonic rhythm, more energetic chorus): duration 2.0, starts at
0.0, 2.0, 4.0 … — same voicings, 8 beats per 4 chords.

## Rhythmic chord stabs (synth-pop)

Stabs are the same voicing played short. Two classic patterns, 1 bar each, over the C chord
(`64 67 72`); repeat per bar with the next chord's voicing.

Offbeat 8ths (the "pumping" pop/dance stab; sits between the kicks):
```json
[
 {"pitch":64,"start":0.5,"duration":0.25,"velocity":104},{"pitch":67,"start":0.5,"duration":0.25,"velocity":104},{"pitch":72,"start":0.5,"duration":0.25,"velocity":104},
 {"pitch":64,"start":1.5,"duration":0.25,"velocity":100},{"pitch":67,"start":1.5,"duration":0.25,"velocity":100},{"pitch":72,"start":1.5,"duration":0.25,"velocity":100},
 {"pitch":64,"start":2.5,"duration":0.25,"velocity":104},{"pitch":67,"start":2.5,"duration":0.25,"velocity":104},{"pitch":72,"start":2.5,"duration":0.25,"velocity":104},
 {"pitch":64,"start":3.5,"duration":0.25,"velocity":100},{"pitch":67,"start":3.5,"duration":0.25,"velocity":100},{"pitch":72,"start":3.5,"duration":0.25,"velocity":100}
]
```

Tresillo 3-3-2 (hits on 1, the "a" of 1, the "and" of 2, then the same in the second half):
```json
[
 {"pitch":64,"start":0.0,"duration":0.3,"velocity":112},{"pitch":67,"start":0.0,"duration":0.3,"velocity":112},{"pitch":72,"start":0.0,"duration":0.3,"velocity":112},
 {"pitch":64,"start":0.75,"duration":0.3,"velocity":100},{"pitch":67,"start":0.75,"duration":0.3,"velocity":100},{"pitch":72,"start":0.75,"duration":0.3,"velocity":100},
 {"pitch":64,"start":1.5,"duration":0.3,"velocity":104},{"pitch":67,"start":1.5,"duration":0.3,"velocity":104},{"pitch":72,"start":1.5,"duration":0.3,"velocity":104},
 {"pitch":64,"start":2.0,"duration":0.3,"velocity":110},{"pitch":67,"start":2.0,"duration":0.3,"velocity":110},{"pitch":72,"start":2.0,"duration":0.3,"velocity":110},
 {"pitch":64,"start":2.75,"duration":0.3,"velocity":100},{"pitch":67,"start":2.75,"duration":0.3,"velocity":100},{"pitch":72,"start":2.75,"duration":0.3,"velocity":100},
 {"pitch":64,"start":3.5,"duration":0.3,"velocity":104},{"pitch":67,"start":3.5,"duration":0.3,"velocity":104},{"pitch":72,"start":3.5,"duration":0.3,"velocity":104}
]
```
18 notes. Layer stabs (short amp envelope, brighter patch) over the sustained pad (slow attack,
sidechained) on separate tracks: the pad gives width, the stabs give rhythm.

## Building a 4-bar stab clip from the 1-bar pattern

1. `create_clip(length=16.0)`; `add_notes` the bar-1 pattern.
2. For bars 2–4 add the same rhythm with the next voicings (G `62 67 71`, Am `60 64 69`, F `60 65 69`), each `start + 4.0 × bar`.
   Or `duplicate_clip_loop` ×2 and then `transpose_notes` is **not** enough (inversions change) — write the voicings explicitly.
3. `get_notes`: 72 notes for the tresillo version (18 × 4). Check that no note starts ≥ 16.0.

## Teaching lines

- Chords define the mood; the bass defines which chord you hear. Change the bass root and the same pad changes meaning.
- Smooth voice leading is why professional pads feel like one evolving sound instead of block chords.
- In dubstep the "chords" are often a single pad in the intro and break; the drop is monophonic bass plus drums.
