# Drum grids

All patterns are 1 bar of 4/4 (`create_clip(length=4.0)`), pitches per the GM table in
[SKILL.md](SKILL.md) — **confirm against the rack's `drum_pads` first**. Durations on drums are
cosmetic for one-shots except open hats (longer = rings longer when the rack chokes it).

Grid cheat: beat 1 = 0.0, "e" = 0.25, "and" = 0.5, "a" = 0.75; beat 2 = 1.0 … beat 4 = 3.0.

## Four-on-the-floor — house / synth-pop, 118–125 BPM

Kick on every beat is the engine; clap on 2 and 4 is the backbeat; closed hats on 8ths with the
on-beat louder; one open hat on the "and" of 4 lifts into the next bar.

```json
[
 {"pitch":36,"start":0.0,"duration":0.25,"velocity":120},
 {"pitch":36,"start":1.0,"duration":0.25,"velocity":112},
 {"pitch":36,"start":2.0,"duration":0.25,"velocity":118},
 {"pitch":36,"start":3.0,"duration":0.25,"velocity":112},
 {"pitch":39,"start":1.0,"duration":0.25,"velocity":105},
 {"pitch":39,"start":3.0,"duration":0.25,"velocity":108},
 {"pitch":42,"start":0.0,"duration":0.125,"velocity":92},
 {"pitch":42,"start":0.5,"duration":0.125,"velocity":70},
 {"pitch":42,"start":1.0,"duration":0.125,"velocity":88},
 {"pitch":42,"start":1.5,"duration":0.125,"velocity":70},
 {"pitch":42,"start":2.0,"duration":0.125,"velocity":92},
 {"pitch":42,"start":2.5,"duration":0.125,"velocity":70},
 {"pitch":42,"start":3.0,"duration":0.125,"velocity":88},
 {"pitch":46,"start":3.5,"duration":0.4,"velocity":84}
]
```
14 notes. Synth-pop variant: add 16th closed hats (`start` 0.25, 0.75, 1.25 … 3.25, velocity 55–62)
for drive; layer a snare (38, velocity 96) under the clap on 1.0 and 3.0 for weight.

## Disco — open hats on every offbeat, 115–122 BPM

The "pea soup" hat: closed hat on the beat and the 16ths around it, open hat on every "and",
choked by the next closed hat. Snare + clap together on 2 and 4.

```json
[
 {"pitch":36,"start":0.0,"duration":0.25,"velocity":118},
 {"pitch":36,"start":1.0,"duration":0.25,"velocity":110},
 {"pitch":36,"start":2.0,"duration":0.25,"velocity":116},
 {"pitch":36,"start":3.0,"duration":0.25,"velocity":110},
 {"pitch":38,"start":1.0,"duration":0.25,"velocity":108},
 {"pitch":38,"start":3.0,"duration":0.25,"velocity":110},
 {"pitch":39,"start":1.0,"duration":0.25,"velocity":96},
 {"pitch":39,"start":3.0,"duration":0.25,"velocity":98},
 {"pitch":42,"start":0.0,"duration":0.125,"velocity":95},
 {"pitch":42,"start":0.25,"duration":0.125,"velocity":60},
 {"pitch":42,"start":0.75,"duration":0.125,"velocity":65},
 {"pitch":42,"start":1.0,"duration":0.125,"velocity":92},
 {"pitch":42,"start":1.25,"duration":0.125,"velocity":60},
 {"pitch":42,"start":1.75,"duration":0.125,"velocity":65},
 {"pitch":42,"start":2.0,"duration":0.125,"velocity":95},
 {"pitch":42,"start":2.25,"duration":0.125,"velocity":60},
 {"pitch":42,"start":2.75,"duration":0.125,"velocity":65},
 {"pitch":42,"start":3.0,"duration":0.125,"velocity":92},
 {"pitch":42,"start":3.25,"duration":0.125,"velocity":60},
 {"pitch":42,"start":3.75,"duration":0.125,"velocity":65},
 {"pitch":46,"start":0.5,"duration":0.45,"velocity":90},
 {"pitch":46,"start":1.5,"duration":0.45,"velocity":86},
 {"pitch":46,"start":2.5,"duration":0.45,"velocity":90},
 {"pitch":46,"start":3.5,"duration":0.45,"velocity":88}
]
```
24 notes. If open and closed hats are not in the same choke group the open hats ring over the
closed ones; shorten open-hat `duration` to 0.3 or ask the user to set the choke group on the pads.

## Half-time — dubstep / riddim, 140 BPM

Snare on beat 3 only. That single choice halves the felt tempo (70 BPM) and makes room for the
bass. Kick on 1; hats on 2 and 4 are the *offbeats* of the felt pulse. Sparse on purpose.

```json
[
 {"pitch":36,"start":0.0,"duration":0.25,"velocity":127},
 {"pitch":38,"start":2.0,"duration":0.25,"velocity":127},
 {"pitch":39,"start":2.0,"duration":0.25,"velocity":100},
 {"pitch":42,"start":1.0,"duration":0.125,"velocity":82},
 {"pitch":42,"start":3.0,"duration":0.125,"velocity":78}
]
```
5 notes. Two-bar variation (write in an 8-beat clip): bar 2 adds a kick on the "and" of 2
(`start: 5.5`, velocity 112) so the bar bounces into the snare, and an extra hat 16th before the
snare (`start: 5.75`, velocity 60). Never move the snare off 2.0/6.0.

## Riddim triplet hats, 140 BPM

The triplet bounce is the riddim signature: 8th triplets on beat 2, a 16th-triplet roll on beat 4
rising into the next bar. Kick and snare unchanged.

```json
[
 {"pitch":36,"start":0.0,"duration":0.25,"velocity":127},
 {"pitch":38,"start":2.0,"duration":0.25,"velocity":127},
 {"pitch":42,"start":1.0,"duration":0.1,"velocity":84},
 {"pitch":42,"start":1.3333,"duration":0.1,"velocity":60},
 {"pitch":42,"start":1.6667,"duration":0.1,"velocity":68},
 {"pitch":42,"start":3.0,"duration":0.1,"velocity":64},
 {"pitch":42,"start":3.1667,"duration":0.1,"velocity":70},
 {"pitch":42,"start":3.3333,"duration":0.1,"velocity":78},
 {"pitch":42,"start":3.5,"duration":0.1,"velocity":86},
 {"pitch":42,"start":3.6667,"duration":0.1,"velocity":94},
 {"pitch":42,"start":3.8333,"duration":0.1,"velocity":102}
]
```
11 notes. Alternative bounce: 8th triplets across beats 3–4 after the snare
(`start` 2.3333, 2.6667, 3.0, 3.3333, 3.6667) with an open hat (46) on 3.6667. Match the bass:
when the bass plays triplets, give the hats the same subdivision in the same beat ([bass.md](bass.md)).

## Fills (last beat of a 4- or 8-bar phrase)

Write these at `12.0 + offset` in a 16-beat clip (bar 4), or `28.0 + offset` for bar 8.

Snare 16th build (any genre):
```json
[
 {"pitch":38,"start":3.0,"duration":0.2,"velocity":72},
 {"pitch":38,"start":3.25,"duration":0.2,"velocity":84},
 {"pitch":38,"start":3.5,"duration":0.2,"velocity":98},
 {"pitch":38,"start":3.75,"duration":0.2,"velocity":112}
]
```

Tom run, high to low (synth-pop / disco):
```json
[
 {"pitch":50,"start":3.0,"duration":0.25,"velocity":104},
 {"pitch":48,"start":3.25,"duration":0.25,"velocity":100},
 {"pitch":47,"start":3.5,"duration":0.25,"velocity":106},
 {"pitch":45,"start":3.75,"duration":0.25,"velocity":112}
]
```

Dubstep build roll (1 bar before the drop; 16ths, then 32nds in the final two beats):
```json
[
 {"pitch":38,"start":0.0,"duration":0.2,"velocity":80},{"pitch":38,"start":0.25,"duration":0.2,"velocity":82},
 {"pitch":38,"start":0.5,"duration":0.2,"velocity":84},{"pitch":38,"start":0.75,"duration":0.2,"velocity":86},
 {"pitch":38,"start":1.0,"duration":0.2,"velocity":88},{"pitch":38,"start":1.25,"duration":0.2,"velocity":90},
 {"pitch":38,"start":1.5,"duration":0.2,"velocity":92},{"pitch":38,"start":1.75,"duration":0.2,"velocity":94},
 {"pitch":38,"start":2.0,"duration":0.1,"velocity":96},{"pitch":38,"start":2.125,"duration":0.1,"velocity":98},
 {"pitch":38,"start":2.25,"duration":0.1,"velocity":100},{"pitch":38,"start":2.375,"duration":0.1,"velocity":102},
 {"pitch":38,"start":2.5,"duration":0.1,"velocity":104},{"pitch":38,"start":2.625,"duration":0.1,"velocity":106},
 {"pitch":38,"start":2.75,"duration":0.1,"velocity":108},{"pitch":38,"start":2.875,"duration":0.1,"velocity":110},
 {"pitch":38,"start":3.0,"duration":0.1,"velocity":112},{"pitch":38,"start":3.125,"duration":0.1,"velocity":114},
 {"pitch":38,"start":3.25,"duration":0.1,"velocity":116},{"pitch":38,"start":3.375,"duration":0.1,"velocity":118},
 {"pitch":38,"start":3.5,"duration":0.1,"velocity":120},{"pitch":38,"start":3.625,"duration":0.1,"velocity":122},
 {"pitch":38,"start":3.75,"duration":0.1,"velocity":124},{"pitch":38,"start":3.875,"duration":0.1,"velocity":127}
]
```
24 notes. Remove the kick in the build bar; the drop's first kick (next clip, `start: 0.0`,
velocity 127) with a crash (49, velocity 110, duration 1.0) is the payoff.

Crash: put 49 at `0.0` of the bar *after* the fill (the first beat of the next 4-bar loop), not at the end of the fill.

## Extending 1 bar to 4 bars with variation

1. `duplicate_clip_loop(track, slot)` twice: 4.0 → 8.0 → 16.0 beats, notes copied. Verify `loop_end: 16.0` in the result.
2. Bar 2 (4.0–8.0): leave identical — repetition is the groove.
3. Bar 3 (8.0–12.0): small change. House: add a kick pickup at `11.75` (velocity 90). Dubstep: add the "and of 2" kick at `9.5`.
4. Bar 4 (12.0–16.0): the fill. `remove_notes(from_time=15.0, time_span=1.0, from_pitch=42, pitch_span=5)`
   to clear hats under the fill, then `add_notes` one of the fills above with `start + 12.0`.
   House: swap the bar-4 open hat for an 8th-note open-hat pair at `15.0` and `15.5`.
5. `get_notes` → count should be `4 × (bar count) − removed + added`. `fire_clip` and listen to the turnaround.
6. For 8 bars: `duplicate_clip_loop` once more and put the bigger fill at bar 8 (28.0–32.0); keep bar 4's fill smaller (2 notes).

## Teaching lines

- "Four-on-the-floor" = kick on every beat; it is why people can dance without thinking.
- Half-time = snare on 3 instead of 2 and 4; same BPM, half the felt speed, twice the weight.
- Hats carry the subdivision (8ths feel relaxed, 16ths drive, triplets bounce); kick and snare carry the pulse.
