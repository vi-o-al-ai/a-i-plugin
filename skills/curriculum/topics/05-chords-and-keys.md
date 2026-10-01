# 05 · Chords and keys

**Goal.** The user can set a key with `set_scale`, build triads from scale degrees, write a 4-bar major pop progression and a minor dubstep progression with sensible voicings, and name a progression by Roman numerals.

**Prerequisites.** 01. A pad-capable instrument (Drift is fine). Drums optional but help.

**Terms.** Key, scale degree, triad, voicing, inversion, harmonic rhythm, progression.

## Building chords from a scale

Semitone offsets from the root: Major = 0 2 4 5 7 9 11; Natural minor = 0 2 3 5 7 8 10. Degree d (1-based) triad = scale[d], scale[d+2], scale[d+4], wrapping with +12. Roman numerals: upper case for major chords, lower for minor.

| Key | Degrees → chords | Common loops |
|---|---|---|
| D major (root 62) | I D · ii Em · iii F#m · IV G · V A · vi Bm · vii° C#° | I–V–vi–IV, vi–IV–I–V, I–vi–IV–V, IV–I–V–vi |
| F minor (root 53) | i Fm · ii° G° · III Ab · iv Bbm · v Cm · VI Db · VII Eb | i–VI–III–VII, i–VII–VI–VII, i–iv–i–v, i–VI (2 bars each) |

Voicings that lead well (one chord per bar, starts 0, 4, 8, 12, durations 4.0):

| Progression | Chord 1 | Chord 2 | Chord 3 | Chord 4 |
|---|---|---|---|---|
| D major I–V–vi–IV | D: 62 66 69 | A: 61 64 69 | Bm: 62 66 71 | G: 62 67 71 |
| F minor i–VI–III–VII | Fm: 53 56 60 | Db: 53 56 61 | Ab: 56 60 63 | Eb: 55 58 63 |

Every voice moves ≤ 4 semitones between chords; the top note stays near 69–71 (major) or 60–63 (minor).

## Plan (15–20 min)

1. **Show me · the key (2 min).** `set_scale(root_note="D", scale_name="Major", why="Set the key so Live highlights in-scale notes")` (or F Minor). `get_session().scale` to read `scale_intervals` back. Point out that new clips show the Scale highlight in Clip View (Live 12).
2. **Show me · one chord (3 min).** `create_midi_track(name="Chords")`, `set_track(color_index=9)`, `load_device(name="Drift")`; `browse(query="Pad", categories=["sounds"])` and load a pad preset if the user prefers. `create_clip(track, slot=0, length=16.0, name="Prog A")`. `add_notes` the I chord for bar 1 only. `select(track, slot=0, show_clip_detail=true)`: "root, third, fifth: the third decides major or minor." Play.
3. **Show me · the progression (3 min).** Add chords 2–4 from the table, why="I–V–vi–IV: the pop loop; each voice moves a step or stays". Play 4 bars. Name the numerals aloud and say what each does (I home, V tension, vi sad cousin, IV lift).
4. **Show me · voicing A/B (3 min).** `duplicate_clip(track, slot=0, target_slot=1)`; in slot 1 `replace_notes` with root-position triads all starting from the root (D: 62 66 69, A: 69 73 76, B: 71 74 78, G: 67 71 74). Fire slot 1 then slot 0: "same chords; which one jumps around?" Keep slot 0; rename slot 1 "Root position (compare)".
5. **Show me · harmonic rhythm (2 min).** `duplicate_clip(slot=0 → slot=2)`, name "Prog A pre-chorus": `replace_notes` so each chord lasts 2.0 and the 4 chords fit in 2 bars, repeated twice (8 chords), why="Doubling the chord rate lifts into a chorus". A/B against slot 0.
6. **Let me try · colour (4 min).** Task: "In 'Prog A', add a 7th to the Bm chord in bar 3: draw an A (MIDI 69, the A3 row in Live) from 3.1 to the end of the bar. Then change the last chord's top note from B to A (drag the 71 note down two rows) so it becomes a Gsus2 colour." Verify `get_notes(from_time=8.0, time_span=8.0)`: pitches in key; the bar-3 chord has 4 voices; the bar-4 chord contains 69. Feedback: right / change / why ("7ths and sus/add colours are the shimmer in synth-pop pads").
7. **Recap and journal (1 min).** Minor version if time remains, or schedule it as Next up.

## Exercise (Let me try)

Write the minor loop i–VI–III–VII in F minor in a new clip (slot 3), one chord per bar, using the voicing table. Verify: all pitches in F natural minor, adjacent voices ≥ 3 semitones apart, durations 4.0, starts 0/4/8/12.

## Verification

- `(pitch − root) % 12 ∈ scale_intervals` for all notes.
- 3–4 notes per chord, same start; top voice moves ≤ 4 semitones between chords.
- Starts on 0, 4, 8, 12 (or every 2.0 for the pre-chorus version); durations fill the slot.
- Nothing below MIDI 48 on the Chords track.

## Recap

- Key = root + scale; chords are stacked every other scale note; the third makes it major or minor.
- I–V–vi–IV is the pop loop; i–VI–III–VII is the dubstep breakdown loop.
- Keep voices close and moving by step; change chords on bar lines; double the rate to lift.

## Go deeper

[06-pads-and-leads.md](06-pads-and-leads.md) to make these chords sound lush; [04-bass-fundamentals.md](04-bass-fundamentals.md) to put roots under them; `genre-notes.md` for more progressions. Live's Chord and Scale MIDI effects (`load_device(name="Scale")`) can pin everything to the key as a safety net.
