# Composition brief template

Write to `./study-<artist>-<song>.md` (lower-case, hyphens). Fill every section; where memory is thin write "reconstructed from the style" rather than guessing. Mark confidence on facts about the specific song. No lyrics anywhere.

```markdown
# Study: <Song> by <Artist>

Built in Ableton Live 12 on <date> at fidelity level: <Skeleton | Harmony/bass/drums | Melody and sound design>.
Purpose: personal study of how the track is put together. Claude could not hear the original or this recreation; the user compared by ear. Facts about the specific song are labelled with confidence; anything else is typical of the style.

## Key and tempo

| Item | Value | Confidence | Source |
|---|---|---|---|
| Tempo | <BPM> | <high/medium/low> | <song/genre/user> |
| Time signature | 4/4 | | |
| Key | <e.g. D major> | | |
| Felt pulse | <straight / half-time> | | |

## Structure

| # | Section | Bars | Beats | Time | What plays | Energy (1–10) |
|---|---|---|---|---|---|---|
| 0 | Intro | 1–8 | 0–32 | 0:00 | ... | 3 |
| ... | | | | | | |

Total: <bars> bars ≈ <m:ss>. Locators in the set match the Beats column.

## Chord chart

| Section | Progression (Roman) | Chords | Harmonic rhythm | Notes |
|---|---|---|---|---|
| Verse | I–V–vi–IV | D – A – Bm – G | 1 per bar | reconstructed |
| ... | | | | |

## Instrument roles

| Track in the set | Role | Register | Rhythm cell | Device used | Approximation note |
|---|---|---|---|---|---|
| Drums | groove | — | kick every beat, clap 2 and 4, offbeat hats | Drum Rack <kit> | kit sounds differ |
| Sub | fundamental | MIDI 36–43 | on kicks | Operator sine | |
| ... | | | | | |

## Energy curve

<One line per section: what enters, what leaves, why it rises or falls. Or a simple text graph:>
Intro 3 → Verse 5 → Pre 6 → Chorus 9 → Verse 6 → Pre 7 → Chorus 9 → Bridge 4 → Final 10 → Outro 2

## What each section does and why

- **Intro**: establishes <key/groove/hook fragment>; withholds <kick/bass> so the verse has something to add.
- **Verse**: ...
- **Chorus**: ...
(Keep to two sentences per section: function, then the device that achieves it.)

## What to listen for in the original

- <Section/time>: <one concrete thing: "how the hats switch to offbeats when the kick enters">
- ...
(5–8 items. These are the user's homework; each should be checkable by ear.)

## What is approximate

- Melody: contour and rhythm only; pitches may differ from the record.
- <Chords>: <which ones were reconstructed>.
- <Sounds>: stock-device stand-ins for <...>.
- <Anything the compare exercise left unresolved>.

## Follow-up lessons

- `/ableton-live:lesson <topic>` — <why it follows from this study>
- `/ableton-live:lesson <topic>` — ...

---
Personal study only. Releasing, posting or sampling a recreation involves composition and recording rights that this study does not address.
```

## Writing rules

- Tables over prose; one idea per cell.
- Beats column = (bar − 1) × 4 start, end exclusive; Time column from beats × 60 / BPM.
- Roman numerals: upper case major, lower case minor; name the chords in the chosen key.
- "Reconstructed" is a complete and acceptable entry.
- Keep the file under ~150 lines.
