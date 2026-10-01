# Melody: arpeggios, hooks, call and response

Registers: synth-pop lead 67–84 (bright, above the chords); dubstep lead/top line 60–79.
Pitch tables and voicings in [chords.md](chords.md).

## Using the set's scale

1. `get_session()` → `scale` = `{root_note, root_name, scale_name, scale_intervals}`. If null or
   wrong, `set_scale(root_note="C", scale_name="Major")` (or `"F"`, `"Minor"`). Live 12 then
   highlights in-key notes in the piano roll, which helps the user see what you wrote.
2. Allowed pitches = `root_note + i + 12k` for `i` in `scale_intervals`. Check every melody note.
3. Chord tones of the bar's chord are the safe landing notes; other scale tones are passing tones (use them between beats).
4. The Scale MIDI effect is a safety net for live playing, not a substitute for correct notes
   (`live-devices/midi-effects/scale.md`).

## Arpeggios (synth-pop)

Write them as notes when the pattern must change per chord; use the Arpeggiator MIDI effect on
held chords when the user wants to tweak rate/style by ear (`live-devices/midi-effects/arpeggiator.md`).

Chord tones to cycle (voice-led inversions from chords.md, plus the octave):
C `60 64 67 72` · G `62 67 71 74` · Am `60 64 69 72` · F `60 65 69 72` ·
Fm `60 65 68 72` · Db `61 65 68 73` · Ab `60 63 68 72` · Eb `58 63 67 70`.

1/16 **up**, 1 bar over C (duration 0.2 leaves a gap so each note plucks; accent pattern 110/85/95/85):
```json
[
 {"pitch":60,"start":0.0,"duration":0.2,"velocity":110},{"pitch":64,"start":0.25,"duration":0.2,"velocity":85},
 {"pitch":67,"start":0.5,"duration":0.2,"velocity":95},{"pitch":72,"start":0.75,"duration":0.2,"velocity":85},
 {"pitch":60,"start":1.0,"duration":0.2,"velocity":110},{"pitch":64,"start":1.25,"duration":0.2,"velocity":85},
 {"pitch":67,"start":1.5,"duration":0.2,"velocity":95},{"pitch":72,"start":1.75,"duration":0.2,"velocity":85},
 {"pitch":60,"start":2.0,"duration":0.2,"velocity":110},{"pitch":64,"start":2.25,"duration":0.2,"velocity":85},
 {"pitch":67,"start":2.5,"duration":0.2,"velocity":95},{"pitch":72,"start":2.75,"duration":0.2,"velocity":85},
 {"pitch":60,"start":3.0,"duration":0.2,"velocity":110},{"pitch":64,"start":3.25,"duration":0.2,"velocity":85},
 {"pitch":67,"start":3.5,"duration":0.2,"velocity":95},{"pitch":72,"start":3.75,"duration":0.2,"velocity":85}
]
```
16 notes. Bars 2–4: same starts `+4.0`, `+8.0`, `+12.0` with the G, Am, F tone sets.

Other patterns (same 16 slots): **down** `72 67 64 60`; **up-down** `60 64 67 72 67 64` (6-note cycle,
so the accent drifts — that drift is the charm); **octave pulse** `60 72 60 72` on 8ths for a
simpler Italo feel; **1/8 up over two octaves** `60 64 67 72 76 79 84 79` at 0.5 spacing.
Put an arp an octave higher (`+12`) than the pad so they do not fight.

## Building a hook (2–4 bars)

1. **Motif**: 3–5 pitches, one rhythmic idea, ≤ 2 beats. Start on a chord tone or step into one.
2. **Repeat** it in bar 2 adjusted to the new chord (same rhythm, pitches moved to chord tones).
3. **Vary** in bar 3: go higher or stretch the rhythm — the peak of the phrase.
4. **Resolve** in bar 4: fewer notes, longer last note on the root or 3rd of the final chord.
5. Leave rests. A hook you can hum has air in it. Keep the range within an octave plus a step.

Worked 4-bar hook, C major over I–V–vi–IV (16-beat clip):
```json
[
 {"pitch":72,"start":0.0,"duration":0.5,"velocity":100},
 {"pitch":74,"start":0.5,"duration":0.5,"velocity":92},
 {"pitch":76,"start":1.0,"duration":1.0,"velocity":104},
 {"pitch":79,"start":2.0,"duration":0.5,"velocity":108},
 {"pitch":76,"start":2.5,"duration":1.5,"velocity":96},
 {"pitch":74,"start":4.0,"duration":0.5,"velocity":100},
 {"pitch":76,"start":4.5,"duration":0.5,"velocity":92},
 {"pitch":74,"start":5.0,"duration":1.0,"velocity":104},
 {"pitch":71,"start":6.0,"duration":0.5,"velocity":100},
 {"pitch":74,"start":6.5,"duration":1.5,"velocity":96},
 {"pitch":72,"start":8.0,"duration":0.5,"velocity":100},
 {"pitch":74,"start":8.5,"duration":0.5,"velocity":92},
 {"pitch":76,"start":9.0,"duration":1.0,"velocity":104},
 {"pitch":79,"start":10.0,"duration":0.5,"velocity":110},
 {"pitch":81,"start":10.5,"duration":1.5,"velocity":112},
 {"pitch":77,"start":12.0,"duration":0.5,"velocity":100},
 {"pitch":76,"start":12.5,"duration":0.5,"velocity":94},
 {"pitch":74,"start":13.0,"duration":1.0,"velocity":98},
 {"pitch":72,"start":14.0,"duration":2.0,"velocity":90}
]
```
19 notes. Check: every pitch in C major (C D E F G A B); each bar ends on a chord tone of its
chord (E on C, D on G, A on Am, C on F); bar 3 is the peak (A5 = 81); bar 4 has the fewest notes
and the longest last note. The second half of each bar is a rest-free echo, so add rests by
shortening `duration` if the lead patch has a long release.

## Call and response

- **Call** (2 bars): ends on a non-root chord tone or the 7th — a question mark.
- **Response** (2 bars): same rhythm or its mirror, ends on the root — a full stop.
- Between two instruments (riddim): lead calls in bars 1–2, bass answers in bars 3–4
  ([bass.md](bass.md) response pattern), drums stay constant.

Lead call in F minor, 2 bars (8-beat clip), ends open on Eb:
```json
[
 {"pitch":65,"start":0.0,"duration":0.5,"velocity":104},
 {"pitch":68,"start":0.5,"duration":0.5,"velocity":96},
 {"pitch":72,"start":1.0,"duration":1.0,"velocity":108},
 {"pitch":70,"start":2.0,"duration":0.5,"velocity":100},
 {"pitch":68,"start":2.5,"duration":1.0,"velocity":96},
 {"pitch":67,"start":4.0,"duration":0.5,"velocity":100},
 {"pitch":68,"start":4.5,"duration":0.5,"velocity":96},
 {"pitch":72,"start":5.0,"duration":1.5,"velocity":108},
 {"pitch":75,"start":6.5,"duration":1.5,"velocity":104}
]
```
9 notes, all in F natural minor (F 65, G 67, Ab 68, Bb 70, C 72, Eb 75). Response: the riddim
bass bar 2 from bass.md, or a lead answer that reuses this rhythm and ends on 65 (F) at 14.0 with duration 2.0.

## Synth-pop vs dubstep melody habits

| | Synth-pop (Empire of the Sun) | Riddim / dubstep (Subtronics) |
|---|---|---|
| Role | Hook carries the chorus; arp carries the verse | Lead lives in intro/break; the drop's "melody" is the bass rhythm |
| Rhythm | Straight 8ths/16ths, syncopated pickups | Sparse, triplet-leaning, long notes with pitch glide (mono + `Glide` on the synth) |
| Range | 67–84, bright | 60–79, often doubled an octave down |
| Harmony | Major, chord-tone endings | Minor, ends on root or b7; chromatic slides are fine |
| Length | 4-bar hooks, repeated | 2-bar calls, answered by bass |

## Teaching lines

- A melody is rhythm first: clap it; if it is boring clapped, new pitches will not save it.
- Chord tones on the beat, passing tones between the beats.
- The best note of a hook is the rest after it.
