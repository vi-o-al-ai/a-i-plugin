---
name: song-study
description: Recreate a song inside Ableton Live 12 to study its composition, using the ableton-live MCP tools. Load when the user runs /ableton-live:study "<song>" by <artist>, asks how a track or an artist's style is built, wants to rebuild, deconstruct or analyse a song's structure, chords, bass, drums or sound design, or asks for a composition brief. Covers confidence labels on what Claude knows, three fidelity levels (Skeleton; Harmony/bass/drums; Melody and sound design), section-by-section building with read-back checks, the study-<artist>-<song>.md brief, copyright guidance and follow-up lessons.
---

# Song study

`/ableton-live:study "<song>" by <artist>` rebuilds a song's bones in the user's set so they can see how it works, then writes a composition brief. Teaching behaviour comes from the `production-mentor` skill (Show me by default, `select`/`show_view` after each step, `why` on every mutating call, journal at `~/.claude-live/journal.md` (or `$CLAUDE_LIVE_HOME/journal.md` when that variable is set)). Genre defaults come from `curriculum/genre-notes.md` and `curriculum/templates/`.

Two limits, stated up front to the user every time: Claude cannot hear the original or the recreation; and Claude's memory of specific commercial songs varies, so song-specific facts carry a confidence label and anything filled in from genre knowledge is marked as reconstructed.

## The flow

### 1. Confirm the song and what Claude knows

Read the journal. Then state, as a short table, what Claude believes about the track with a confidence per item (high / medium / low) and a source tag (`song` = remembered about this track; `genre` = reconstructed from the style):

| Item | Value | Confidence | Source |
|---|---|---|---|
| Tempo | e.g. ~120 BPM | medium | song |
| Key | e.g. D major | low | genre |
| Structure | intro / verse / pre / chorus … with bar counts | medium | genre |
| Instrumentation | drums, sub, synth bass, pads, arp, lead, vocals | high | song |
| Signature elements | e.g. offbeat hats, octave bass, sidechained pad | medium | song |

Ask the user to correct anything they know (they can check tempo by tapping along; Live's Control Bar tempo field accepts typed values). If Claude knows nothing specific about the track, say so plainly and offer a "typical of the style" study instead, labelled as such. Never state a guess as fact.

### 2. Offer three fidelity levels

| Level | Builds | Time | Tools |
|---|---|---|---|
| **Skeleton** | Tempo, key, section map with bar counts as locators in Arrangement View, colour-coded placeholder clips per role per section, scenes named per section. | 10–15 min | `set_transport`, `set_scale`, `create_midi_track`, `set_track`, `create_scene`, `set_scene`, `create_clip`, `set_clip`, `add_clip_to_arrangement`, `set_locator` |
| **Harmony / bass / drums** | Skeleton + chords per section, a bassline in the right register and rhythm, a drum pattern that matches the groove. | +20–30 min | + `add_notes`, `get_notes`, `duplicate_clip`, `duplicate_clip_loop`, `load_device` |
| **Melody and sound design** | + an approximation of the hook melody, each sound rebuilt with stock devices. | +30–45 min | + `load_device`, `set_parameters`, `set_automation`, `get_devices` |

Exact tool sequences per level: [fidelity-levels.md](fidelity-levels.md). Recommend Skeleton for a first study and offer to continue. A level is complete when its verification checks pass, not when the clips exist.

### 3. Build section by section

For each section in the map, in order: say what the section does in the song and why (one sentence), build its clips, `select` and show them, read back with `get_notes` / `get_arrangement` / `get_devices`, then move on. Narrate in Show-me mode; offer Let me try for anything the journal shows the user has done before (e.g. drawing the drum pattern). Method for deciding what to write when memory is thin: [method.md](method.md). After each section, run the listening comparison: the user plays the original's section, then the Live version (`fire_scene` or play from the locator), reports differences in their words; Claude adjusts what it can (rhythm, pitch, register, device settings) and says what it cannot judge.

### 4. Write the composition brief

Write `study-<artist>-<song>.md` in the current working directory (lower-case, hyphens, no punctuation: `study-empire-of-the-sun-<song>.md`) from [brief-template.md](brief-template.md): structure table, key/tempo, chord chart per section, instrument roles, energy curve, what each section does and why, "what to listen for" in the original, and a list of what is approximate. Mark every reconstructed item. No lyrics. Tell the user the file path.

### 5. Offer follow-up lessons

Map the elements just built to curriculum topics and offer the two most relevant: drums → `02`/`03`; bass → `04`/`07`; chords → `05`; pads/leads → `06`; sidechain → `08`; structure → `09`; transitions → `10`. Phrase as `/ableton-live:lesson <topic>`. Append to the journal: "Study: <song> at <level>; brief at <path>", plus concepts touched and Next up.

## Copyright and honesty

- Recreating a song for personal study in the user's own set is fine and is how producers have always learned. Say this once.
- Never reproduce lyrics, not in clips, not in the brief, not in chat. Vocal lines are described by rhythm and contour only ("a short rising phrase over the IV chord").
- Releasing, posting or sampling a recreation is a different matter (composition and recording rights). Remind the user once in the brief's footer and once in chat if they mention releasing it.
- If the user asks for a note-for-note transcription of a melody: give an approximation that keeps the contour, rhythm and chord-tone landings, and say explicitly that it is approximate and may differ from the record. Do not claim accuracy Claude cannot verify.
- Do not invent facts about the artist's process, gear or intentions. "Typical of the style" is the honest phrasing when memory is thin.

## Worked outlines

[examples.md](examples.md) has two Skeleton-level outlines, generic by design: an Empire of the Sun-style synth-pop track (120 BPM, D major) and a Subtronics-style riddim track (140 BPM, F minor), each with scene names, locator times and the role placeholders. Use them as the fallback when a requested song is in one of these lanes and Claude's song-specific memory is low.

## Related

`/ableton-live:lesson <topic>` for the follow-ups; `/ableton-live:review` to critique the recreation; `/ableton-live:history` to replay what was built; `curriculum/genre-notes.md` and `curriculum/templates/` for defaults; `production-mentor/feedback-checklists.md` for the read-back checks.
