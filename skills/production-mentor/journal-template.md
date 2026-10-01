# Learning journal: template and rules

Path: `~/.claude-live/journal.md` (or `$CLAUDE_LIVE_HOME/journal.md` when that variable is set). If it does not exist, create the directory and write the template below with the Write tool (not an MCP tool). Read it at the start of every lesson, explain, review, quiz or study; append at the end.

## Template

```markdown
# Learning journal

## Profile
- Live edition: 12 (Intro / Standard / Suite: ask once; some stock devices are Suite-only)
- Goals: finish a full short track; synth-pop (Empire of the Sun-style) and riddim (Subtronics-style)
- Preferred mode: Show me; offer Let me try after first exposure
- Setup notes: (control surface selected, audio device, anything that broke)

## Concepts covered
| Date | Concept | Confidence (1–3) | Notes |
|---|---|---|---|

## Exercises completed
| Date | Exercise | Result |
|---|---|---|

## Struggles
- (date: what was hard, in one line)

## Next up
- (the single next topic, and why)
```

## Rules

- Confidence: 1 = watched it in Show me; 2 = did it in Let me try with corrections; 3 = did it alone and it verified clean on first read-back. A quiz answer can raise 1 → 2; a clean do-it quiz item can raise 2 → 3.
- One row per concept per lesson. If a concept recurs, add a new row rather than editing the old one, so progress is visible.
- Exercises: name the exercise as the topic file names it (e.g. "02 offbeat hats", "08 sidechain routing") and the result in a few words ("clean", "fixed velocity", "needed help with grid").
- Struggles: one line, dated, concrete ("confused scene index with slot index"). Remove a struggle when a later exercise on it comes back clean, and say so in the lesson.
- Next up: replace, do not append. One item. Reference the topic file (`curriculum/topics/NN-...md`) or the study follow-up.
- Keep the whole file under ~200 lines. When it grows past that, collapse the oldest Concepts rows into one summary row per topic ("00–03 covered Sept 2026, all at 3").
- Terse. No lyrics, no song recreation notes beyond the brief file name, no personal data beyond Profile.
- Dates in ISO form (2026-10-01).

## Example entries

```markdown
| 2026-10-01 | Four-on-the-floor kick + backbeat clap | 2 | Did claps in Let me try; velocity fix |
| 2026-10-01 | Offbeat hats vs straight 8ths (A/B) | 1 | Preferred offbeats |

| 2026-10-01 | 02 open hat on bar 4 | clean |

- 2026-10-01: grid was 1/8 when drawing 16ths; needed to right-click → Fixed Grid 1/16

## Next up
- 03-drums-half-time-140: snare on 3; contrast with today's four-on-the-floor
```
