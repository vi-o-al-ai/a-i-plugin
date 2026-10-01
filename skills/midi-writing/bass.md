# Bass

Bass locks to the kick and names the chord. Keep it mono (one note at a time) unless you mean a
pad-bass. Registers: sub 24–36 (C0–C1, ~33–65 Hz), synth/mid bass 36–55. Pitch tables in [chords.md](chords.md).

## Synth-pop octave bass (120 BPM, 8ths)

Root on the beat, octave up on the "and". The octave jump is the 80s/Italo/synth-pop engine; the
staccato duration (0.4 of a 0.5 slot) leaves air for the kick. Change root per chord.

C major I–V–vi–IV, 16-beat clip (`create_clip(length=16.0)`):
```json
[
 {"pitch":36,"start":0.0,"duration":0.4,"velocity":110},{"pitch":48,"start":0.5,"duration":0.4,"velocity":95},
 {"pitch":36,"start":1.0,"duration":0.4,"velocity":105},{"pitch":48,"start":1.5,"duration":0.4,"velocity":95},
 {"pitch":36,"start":2.0,"duration":0.4,"velocity":110},{"pitch":48,"start":2.5,"duration":0.4,"velocity":95},
 {"pitch":36,"start":3.0,"duration":0.4,"velocity":105},{"pitch":48,"start":3.5,"duration":0.4,"velocity":95},
 {"pitch":43,"start":4.0,"duration":0.4,"velocity":110},{"pitch":55,"start":4.5,"duration":0.4,"velocity":95},
 {"pitch":43,"start":5.0,"duration":0.4,"velocity":105},{"pitch":55,"start":5.5,"duration":0.4,"velocity":95},
 {"pitch":43,"start":6.0,"duration":0.4,"velocity":110},{"pitch":55,"start":6.5,"duration":0.4,"velocity":95},
 {"pitch":43,"start":7.0,"duration":0.4,"velocity":105},{"pitch":55,"start":7.5,"duration":0.4,"velocity":95},
 {"pitch":45,"start":8.0,"duration":0.4,"velocity":110},{"pitch":57,"start":8.5,"duration":0.4,"velocity":95},
 {"pitch":45,"start":9.0,"duration":0.4,"velocity":105},{"pitch":57,"start":9.5,"duration":0.4,"velocity":95},
 {"pitch":45,"start":10.0,"duration":0.4,"velocity":110},{"pitch":57,"start":10.5,"duration":0.4,"velocity":95},
 {"pitch":45,"start":11.0,"duration":0.4,"velocity":105},{"pitch":57,"start":11.5,"duration":0.4,"velocity":95},
 {"pitch":41,"start":12.0,"duration":0.4,"velocity":110},{"pitch":53,"start":12.5,"duration":0.4,"velocity":95},
 {"pitch":41,"start":13.0,"duration":0.4,"velocity":105},{"pitch":53,"start":13.5,"duration":0.4,"velocity":95},
 {"pitch":41,"start":14.0,"duration":0.4,"velocity":110},{"pitch":53,"start":14.5,"duration":0.4,"velocity":95},
 {"pitch":41,"start":15.0,"duration":0.4,"velocity":105},{"pitch":53,"start":15.5,"duration":0.4,"velocity":95}
]
```
32 notes: C (36/48) → G (43/55) → A (45/57) → F (41/53). For a 16th-note version halve every
slot (duration 0.2) and keep the octave on the "e" and "a" only when you want more drive.

## Disco walking octaves (118 BPM)

Same octave engine, but the last 8th of the bar walks to the next root. Diatonic approach from
below (F → G) is safe; a chromatic approach (F# = 42 → G) is idiomatic disco/funk — use it on
purpose and say so.

Bar on C heading to G:
```json
[
 {"pitch":36,"start":0.0,"duration":0.45,"velocity":112},{"pitch":48,"start":0.5,"duration":0.45,"velocity":96},
 {"pitch":36,"start":1.0,"duration":0.45,"velocity":106},{"pitch":48,"start":1.5,"duration":0.45,"velocity":96},
 {"pitch":36,"start":2.0,"duration":0.45,"velocity":112},{"pitch":48,"start":2.5,"duration":0.45,"velocity":96},
 {"pitch":36,"start":3.0,"duration":0.45,"velocity":106},{"pitch":41,"start":3.5,"duration":0.45,"velocity":100}
]
```
8 notes. Walk-ups for the other changes: G → Am use A's lower neighbour G (43) or the 5th E (40);
Am → F use G (43) or E (40); F → C use B (47, leading tone) or G (43). Accent the walk note slightly.

## Riddim call-and-response (140 BPM, F minor)

Two bars: the **call** asks, the **response** answers and lands on the root. Rhythm is the point:
8th-triplet bounces (0.3333) against rests; the bass sits out under the snare at 2.0 / 6.0 so the
snare hits harder. Mid bass (wobble/growl patch) in 36–53.

8-beat clip (`create_clip(length=8.0)`):
```json
[
 {"pitch":41,"start":0.0,"duration":0.5,"velocity":112},
 {"pitch":41,"start":0.6667,"duration":0.3333,"velocity":100},
 {"pitch":41,"start":1.0,"duration":0.3333,"velocity":106},
 {"pitch":44,"start":1.3333,"duration":0.3333,"velocity":100},
 {"pitch":41,"start":1.6667,"duration":0.3333,"velocity":104},
 {"pitch":39,"start":2.5,"duration":0.5,"velocity":104},
 {"pitch":41,"start":3.0,"duration":0.3333,"velocity":106},
 {"pitch":41,"start":3.3333,"duration":0.3333,"velocity":100},
 {"pitch":44,"start":3.6667,"duration":0.3333,"velocity":108},
 {"pitch":41,"start":4.0,"duration":0.5,"velocity":112},
 {"pitch":36,"start":4.6667,"duration":0.3333,"velocity":100},
 {"pitch":36,"start":5.0,"duration":0.3333,"velocity":106},
 {"pitch":39,"start":5.3333,"duration":0.3333,"velocity":100},
 {"pitch":36,"start":5.6667,"duration":0.3333,"velocity":104},
 {"pitch":46,"start":6.5,"duration":0.5,"velocity":104},
 {"pitch":44,"start":7.0,"duration":0.5,"velocity":106},
 {"pitch":41,"start":7.5,"duration":0.5,"velocity":110}
]
```
17 notes, all in F natural minor (F 41, Ab 44, Eb 39, C 36, Bb 46). Bar 1 ends on Ab (open),
bar 2 ends on F (closed). Variation ideas for drop part B: move the beat-2 triplet to beat 4;
replace one triplet group with a single held note (duration 1.0) so the wobble LFO is heard; drop
every note in the last beat of bar 2 for a one-beat silence before the loop restarts.

Match the wobble to the rhythm: a held note wants an LFO rate of 1/8 or 1/8T; triplet 8ths want
the LFO retriggered per note or a shorter rate (see `live-devices/instruments/wavetable.md`,
`live-devices/effects/auto-filter.md`).

## Sub bass rules

1. **One note at a time.** No overlaps: each `start + duration ≤ next start`. Leave ≥ 0.05 gap or use a mono/legato instrument.
2. **Root only** (the chord's root, occasionally the 5th). The sub tells the ear which chord it is; a 3rd down there is mud.
3. **One octave band.** Choose, per pitch class, the octave that lands in ~29–40 (F0–E1 ≈ 44–82 Hz) so the sub stays even.
   F minor: F0 29 · Ab0 32 · Bb0 34 · C1 36 · Eb0 27 (38.9 Hz — use Eb1 39 if the system cannot reproduce it).
4. **No faster than 8ths.** A 16th at 140 BPM is 107 ms — the sub barely completes four cycles. Let the mid bass do the triplets; the sub plays the skeleton.
5. **Constant velocity** 100–110. No humanization, dead on the grid.
6. **Sine or triangle, no filter sweep.** Operator sine (`live-devices/instruments/operator.md`) or Wavetable sub (`Sub Gain`).
7. **Separate track** from the mid bass, so the mid bass can be distorted and sidechained without touching the sub.

Sub skeleton for the riddim pattern above (8 beats):
```json
[
 {"pitch":29,"start":0.0,"duration":0.95,"velocity":106},
 {"pitch":29,"start":1.0,"duration":0.95,"velocity":106},
 {"pitch":27,"start":2.5,"duration":0.45,"velocity":106},
 {"pitch":29,"start":3.0,"duration":0.95,"velocity":106},
 {"pitch":29,"start":4.0,"duration":0.6,"velocity":106},
 {"pitch":36,"start":4.6667,"duration":1.3,"velocity":106},
 {"pitch":34,"start":6.5,"duration":0.45,"velocity":106},
 {"pitch":32,"start":7.0,"duration":0.45,"velocity":106},
 {"pitch":29,"start":7.5,"duration":0.5,"velocity":106}
]
```
9 notes, no overlaps, every note the root of what the mid bass is playing at that moment.

## Sidechain interplay with the kick

- Kick and bass want the same 50–100 Hz. Either the bass ducks (sidechain compressor keyed from
  the kick, see `live-devices/effects/compressor.md`) or it moves out of the way in the MIDI.
- **MIDI-side ducking:** start bass notes a 16th after the kick (`start` 0.25 instead of 0.0) or
  end them a 16th before the next kick (`duration` 0.75 on a 1-beat slot). Octave-bass patterns
  already do this: the 0.4 durations leave the kick a clean transient.
- **Compressor-side ducking** (house/synth-pop): fast attack, release ~150–250 ms at 120 BPM so
  the bass is back before the next kick (500 ms apart). The audible "pump" is the release.
- **Dubstep:** sub and kick both hit on 0.0; short sidechain (release ~80–120 ms) or a 1–2 dB
  dip, not a pump. Half-time has 1.7 s between kicks, so there is no groove to gain from pumping.
- Never sidechain the kick to itself; never sidechain the sub to the snare.

## Teaching lines

- The bass tells you the chord; the chords tell you the colour.
- Octave bass = movement without changing harmony. Walk-ups = the bass announcing the next chord.
- Riddim bass is rhythm first: the pitches barely move, the gaps do the work.
