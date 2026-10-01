# Arrangement patterns

Bar *N* in Live's ruler starts at song time `(N-1) × 4.0` beats (4/4). Seconds per bar =
`240 / tempo`: 2.0 s at 120 BPM, 1.714 s at 140 BPM.

| Bar | Beats | 120 BPM | 140 BPM |
|---|---|---|---|
| 1 | 0.0 | 0:00 | 0:00 |
| 9 | 32.0 | 0:16 | 0:14 |
| 17 | 64.0 | 0:32 | 0:27 |
| 33 | 128.0 | 1:04 | 0:55 |
| 49 | 192.0 | 1:36 | 1:22 |
| 65 | 256.0 | 2:08 | 1:50 |
| 97 | 384.0 | 3:12 | 2:45 |
| 129 | 512.0 | 4:16 | 3:39 |

## Synth-pop (Empire of the Sun lane), 118–124 BPM

| Section | Bars | What is playing (MIDI terms) |
|---|---|---|
| Intro | 8 | Pad (4-beat chords) + 1/16 arp. No kick, or hats only from bar 5. |
| Verse 1 | 16 | Four-on-the-floor, octave bass, pad quieter or absent, sparse stabs (offbeat 8ths every other bar), lead motif or vocal space. |
| Pre-chorus | 8 | Chords change twice per bar (duration 2.0), hats go to 16ths, snare 16th build in the last bar, bass stays on 8ths. |
| Chorus | 16 | Everything: disco open-hat offbeats, pad + tresillo stabs, hook lead 67–84, bass full, crash on bar 1. |
| Verse 2 | 16 | Verse 1 minus the pad; keep the arp; add a counter-line in bars 9–16. |
| Pre-chorus 2 | 8 | As before; bigger fill (snare 16ths + toms). |
| Chorus 2 | 16 | As chorus; add a top layer of the hook an octave up (`+12`) from bar 9. |
| Bridge / break | 8 | Drums out or kick only; pad + arp; filter sweep automation over the 8 bars; snare build in the last 2. |
| Final chorus | 16–24 | Chorus 2 plus every layer; the last 8 bars drop the bass octave jumps to straight 8ths for weight. |
| Outro | 8 | Pad + arp fade; remove kick first, then bass. |

Total ≈ 120–128 bars ≈ 4:00–4:16 at 120 (bars × 4 beats × 0.5 s). Radio edit: cut Verse 2 to 8 and the final chorus to 16.

## Riddim / dubstep (Subtronics lane), 140 BPM

| Section | Bars | What is playing |
|---|---|---|
| Intro | 16–32 | Minor pad (i–VI–III–VII or i–VII–VI–VII, 4-beat chords), filtered hats, FX, lead call phrase. No sub. |
| Build | 16 | Kick on every beat (or none), snare roll stepping 8ths → 16ths → 32nds in the last 4 bars, hats to 16ths then 16th triplets, pad rising via filter automation, bass out. Last beat (or last bar) silent except a vocal/FX. |
| Drop A | 16 | Half-time kit (kick 0.0, snare 2.0), riddim call/response bass + sub skeleton, hats on 2 and 4, no pad. |
| Drop B | 16 | Same kit; bass variation (triplet groups moved, one held wobble note), triplet hat bounce, one-beat silence at bar 8. |
| Break | 16 | Pad returns, drums half (kick + snare only or none), lead answers. |
| Build 2 | 8–16 | Shorter than build 1; same roll logic. |
| Drop C / D | 32 | New bass pattern or the drop transposed (+2 or +5 semitones via `transpose_notes` on bass and sub together), ride/triplet hats, extra percussion. |
| Outro | 16 | Pad + hats; kick last to leave. |

Total ≈ 136–160 bars ≈ 3:53–4:34 at 140 (bars × 4 beats × 0.4286 s).

## What changes between sections, in MIDI terms

| Lever | Low energy | High energy |
|---|---|---|
| Density | 4–8 notes/bar | 16–32 notes/bar |
| Hat subdivision | none / 8ths | 16ths → 16th triplets → 32nd rolls (builds) |
| Register | chords 55–67, lead 67–72 | add octave-up doubles (`+12`), bass octave jumps |
| Kick | out, or on 1 only | four-on-the-floor (pop) / 1 + "and of 2" (dubstep) |
| Snare | out or ghosted | backbeat 2+4 (pop) / 3 (dubstep), rolls into transitions |
| Chord rhythm | 1 chord per bar, sustained | 2 per bar, plus stabs |
| Velocity ceiling | 70–95 | 100–127 |
| Note length | long pads | short stabs, staccato bass |
| Bass | sub only, or none | mid bass + sub |

Energy *drops* are as important as rises: remove the kick for the last bar before a chorus; cut
everything for 1 beat before a dubstep drop.

## Doing it with the tools

**Session view skeleton (fastest to iterate):**
1. `create_scene(name=...)` for each section in order (Intro, Verse, Pre, Chorus, …).
2. Write each part's core clip in its first scene; `duplicate_clip(track, slot, target_slot)` into later scenes; vary copies
   (`remove_notes` by time range, `add_notes` fills, `transpose_notes` for a key lift).
3. `set_scene(scene, color_index=...)` per section type; `fire_scene` to audition transitions.

**Arrangement (when the user wants a timeline):**
1. For each section compute `time = (start_bar - 1) × 4.0`.
2. `add_clip_to_arrangement(track, slot, time)` for each clip in that section; a 4-bar clip must be added at
   `time`, `time + 16.0`, … to fill a 16-bar section (or extend the clip's loop first with `duplicate_clip_loop`).
3. `set_locator(time, name="Chorus")` at each section start. `show_view("Arranger")` and `select` the first clip.
4. Automation for sweeps lives in the session clip (`set_automation`) before you copy it in.

**Transitions checklist:** crash on the first beat of the new section; fill in the last bar of the old
one; one-beat silence before a drop; `why="Silence before the drop makes the first kick land"`.
