---
name: midi-writing
description: "Recipes for writing musically correct MIDI into Ableton Live clips with add_notes: drum grids (four-on-the-floor, disco, half-time 140 dubstep/riddim, triplet hats, fills), chord progressions and pad voicings, synth-pop and riddim bass, arpeggios and hooks, section-by-section arrangement patterns and humanization. Load when the user asks Claude to write, generate, program or improve drums, beats, chords, pads, bass, sub, leads, melodies, arps or a song skeleton, or asks what notes/rhythm to use for an Empire of the Sun-style synth-pop or Subtronics-style riddim/dubstep track."
---

# MIDI writing

Tool mechanics (addressing, verify loop, errors) live in the `ableton-live` skill; sound design in
`live-devices`. This skill is about *what notes to write*. All times are beats (1 bar of 4/4 = 4.0,
16th = 0.25, 8th triplet = 0.3333, 16th triplet = 0.1667). Note objects are ready for `add_notes`:
`{"pitch", "start", "duration", "velocity"}`.

Files: [drums.md](drums.md) · [chords.md](chords.md) · [bass.md](bass.md) · [melody.md](melody.md) ·
[arrangement-patterns.md](arrangement-patterns.md) · [humanize.md](humanize.md)

## Method

1. **Decide key, tempo, feel first.** Ask or infer from the reference:
   synth-pop (Empire of the Sun): 115–125 BPM, major key (C, G, D, A, F are friendly), straight 8ths/16ths, four-on-the-floor.
   riddim/dubstep (Subtronics): 140 BPM felt as 70 (half-time), minor key (F, F#, G, E minor are typical), snare on beat 3, triplet bass rhythms.
   Set them: `set_transport(tempo=...)`, `set_scale(root_note="F", scale_name="Minor")` so Live's
   piano roll highlights the key. Read `scale` back from `get_session` and derive allowed pitches.
2. **Drums → bass → chords → lead.** Drums fix the grid; bass locks to the kick; chords sit above
   the bass; the lead fills the space that is left. Each on its own MIDI track.
3. **Write 1–2 bars, verify, then extend.** `create_clip(length=4.0 or 8.0)`, `add_notes`,
   `get_notes` (check `count`, min/max start, pitches in key), `fire_clip`, ask the user to listen.
   Then `duplicate_clip_loop` (4→8→16 beats, copies notes) and *vary* the copy: `remove_notes` in a
   range, `add_notes` a fill, `transpose_notes` a bar. Or `duplicate_clip` into the next scene and vary there.
4. **Check before writing.** Every pitch in the stated key or a chord tone; every `start + duration ≤ loop_end`;
   no overlaps on monophonic parts (sub bass); velocities 1–127.
5. **Say why.** One musical clause per `why`, and one sentence to the user ("snare on 3 is what makes it feel half-time").

## Drum mapping (General MIDI, as Live's stock Drum Racks lay it out)

Live names middle C (60) **C3**, so 36 = **C1**.

| Pitch | Name | Sound | Pitch | Name | Sound |
|---|---|---|---|---|---|
| 36 | C1 | Kick | 44 | G#1 | Pedal hat |
| 37 | C#1 | Rim / sidestick | 45 | A1 | Low tom |
| 38 | D1 | Snare | 46 | A#1 | Open hat |
| 39 | D#1 | Clap | 47 | B1 | Low-mid tom |
| 40 | E1 | Snare 2 (electric) | 48 | C2 | Hi-mid tom |
| 41 | F1 | Low floor tom | 49 | C#2 | Crash |
| 42 | F#1 | Closed hat | 50 | D2 | High tom |
| 43 | G1 | High floor tom | 51 | D#2 | Ride |

**Caveat:** any Drum Rack pad can hold anything. Before writing, call
`get_devices(track, device_path="<rack path>")` and read `drum_pads` (`note`, `name`, `has_chain`).
Use the pad whose name says Kick/Snare/Clap/Hat; fall back to the GM table only when the rack is
empty or the names are unhelpful. Pads with `has_chain: false` are silent — never write to them.
Many 808/dubstep kits put the kick on 36 and the snare on 38 anyway, but 909/dance kits often use
37 for a second kick or 40 for a clap.

## Velocity guidance

| Part | Range | Note |
|---|---|---|
| Kick | 110–127 | Beat 1 strongest; constant in dance music. |
| Snare / clap backbeat | 100–125 | Dubstep snare on 3: 127, it *is* the drop. |
| Closed hats | 50–95 | Accent on the beat (90), lighter on 16ths (55–70). |
| Open hat | 75–95 | Duration matters more than velocity (0.4–0.5 beats). |
| Ghost notes | 30–55 | Snare ghosts on 16ths before the backbeat. |
| Pads | 70–95 | Even; let the envelope do the dynamics. |
| Chord stabs | 95–115 | Accent the syncopated hits. |
| Bass (synth) | 95–115 | On-beats stronger than off-beats. |
| Sub bass | 100–110 | Constant — the sub must not breathe. |
| Lead | 85–115 | Phrase peaks louder; the last note of a phrase softer. |

Many Live instruments map velocity to filter or amplitude; if a part sounds dull, check velocity
before touching the device.

## Humanization rules (details in [humanize.md](humanize.md))

- Timing: offset hats, snares, chords and leads by ±0.01–0.03 beats. **Keep the kick on the grid**, and the sub bass too.
- Velocity: vary by ±8–15 per hit; keep the accent pattern (on-beats louder) so the groove reads.
- Prefer Live's note properties for randomness that renews every loop: `velocity_deviation` (e.g. 12) and `probability` (0.6–0.8 on ghost hats).
- Swing comes from `quantize_notes(grid=0.25, swing=0.2–0.4)`, not from hand offsets.
- Dance genres want tight: humanize hats and percussion, not kick/snare/sub. Dubstep snares stay dead on 3.

## Quick picks by genre

**Synth-pop (120 BPM, C major, I–V–vi–IV)**
1. Drums: [drums.md § Four-on-the-floor](drums.md), 1 bar → 4 bars with an open hat lift in bar 4.
2. Bass: octave bass, 8ths, root per bar ([bass.md](bass.md)).
3. Chords: close-voiced triads around 60–72 as 4-beat pads, plus an offbeat/tresillo stab layer ([chords.md](chords.md)).
4. Lead: 1/16 arp over chord tones, then a 4-bar hook ([melody.md](melody.md)).
5. Sidechain pads and bass to the kick (`live-devices/effects/compressor.md`).

**Riddim / dubstep (140 BPM, F minor)**
1. Drums: half-time, kick 0.0, snare 2.0, hats on 1.0 and 3.0; triplet hat bounce in bar 2 ([drums.md § Half-time](drums.md)).
2. Bass: call-and-response, 8th-triplet rhythms with rests, mid bass 41–53 ([bass.md](bass.md)).
3. Sub: same rhythm one or two octaves down (24–40, typically 28–40), one note at a time, no overlaps.
4. Chords/pad only in intro/break; drop is drums + bass + sub + one-shot FX.
5. Arrangement: intro 16 → build 16 → drop 32 → break 16 → build 8 → drop 32 ([arrangement-patterns.md](arrangement-patterns.md)).

## Pitch arithmetic

`pitch = 12 × (octave + 2) + pitch_class` with C=0 C#=1 D=2 D#=3 E=4 F=5 F#=6 G=7 G#=8 A=9 A#=10 B=11
(Live convention: C3 = 60, C1 = 36, C0 = 24). Allowed pitches in a key: `root + interval + 12k` for each
`interval` in `scale_intervals` (from `get_session().scale`). Major = [0,2,4,5,7,9,11];
natural minor = [0,2,3,5,7,8,10]. Full tables in [chords.md](chords.md).

## Verification checklist (run mentally before `add_notes`)

- [ ] Clip exists and `loop_end` ≥ last `start + duration` (else extend with `set_clip`).
- [ ] Pitches: in key, or deliberate chromatic passing tones you can name.
- [ ] Monophonic parts (sub, 303-style bass): no two notes overlap; leave ≥ 0.02 gap or use legato on purpose.
- [ ] Drum pitches match the rack's `drum_pads`.
- [ ] Velocities within the table above; nothing at 0.
- [ ] ≤ 500 notes per call.
- After: `get_notes` and compare `count` with `len(notes)`.
