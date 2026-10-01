---
name: curriculum
description: A beginner's path from loops to finished tracks in Ableton Live 12, taught through the ableton-live MCP tools. Load when the user runs /ableton-live:lesson, asks what to learn next, wants a structured lesson on Live basics, drums, bass, chords, synth sound design, wobble or growl bass, sidechain, arrangement, transitions, automation, mixing or finishing, or asks for a song-structure template for synth-pop or riddim/dubstep. Holds the topic tree, a 15–20 minute plan per topic, genre conventions and bar-by-bar structure templates; teaching behaviour comes from production-mentor.
---

# Curriculum: loop to song

Spine: **Loop to song**. Every topic ends with something that plays, and the sequence ends with a finished ~3:30 track in one of the user's two genres. Teaching behaviour (modes, A/B, verification, journal) is defined in the `production-mentor` skill; load it alongside this one.

## Running `/ableton-live:lesson [topic]`

1. **Read the journal** at `~/.claude-live/journal.md` (create from `production-mentor/journal-template.md` if missing). Note confidence levels, Struggles, Next up.
2. **Check Live**: `ableton_status`. If not connected, walk through Preferences → Link, Tempo & MIDI → Control Surface: ClaudeLive (see `production-mentor/ui-vocabulary.md`) before anything else.
3. **Pick the topic**: the one requested, else the journal's Next up, else the first topic in the tree whose prerequisites are at confidence ≥ 2. If the user names something off-tree ("teach me arps"), map it to the nearest topic and say which.
4. **Read the topic file** under `topics/`. Read `get_session()` so the plan uses the user's real tracks and scenes rather than assuming an empty set.
5. **State the goal and the plan**: one sentence of goal, the 15–20 minute plan as 4–7 numbered steps, which steps are Show me and which are Let me try (offer Let me try for anything seen once). Ask one question only if the plan depends on it (genre, which track to use).
6. **Run it** step by step in the mentor's modes: say what/where/why, tool call with `why`, `select`/`show_view`, listen, A/B where the topic says so.
7. **Verify** with the topic's checks (and `production-mentor/feedback-checklists.md`). Feedback as right / change / why.
8. **Recap** in 3 lines and give the one thing to try alone.
9. **Append to the journal**: concepts with confidence, exercises with result, struggles, Next up (the "go deeper" pointer or the next topic).

Rules: one lesson = one topic file; if time runs out, stop at a clean step and write Next up. Work on new tracks/scenes rather than editing the user's existing material unless they ask. Name every track and clip you create. Ask before any `delete_*`, `replace_notes` or `clear_automation` on something the user made. Always `get_devices(..., include_params=true)` before `set_parameter` so parameter names are real, not guessed.

## Topic tree

| # | Topic | One line | File |
|---|---|---|---|
| 00 | Live orientation | Session vs Arrangement, tracks, slots, scenes, returns, master, Browser, Detail View; signal flow MIDI → instrument → audio effects → mixer → returns → master. | [topics/00-live-orientation.md](topics/00-live-orientation.md) |
| 01 | Tempo, grid and clips | BPM, bars as beats (1 bar = 4.0), grid, clip length and loop brace, duplicating clips and scenes, launch quantization. | [topics/01-tempo-grid-and-clips.md](topics/01-tempo-grid-and-clips.md) |
| 02 | Drums: four-on-the-floor | Kick every beat, clap on 2 and 4, offbeat hats, a bar-4 variation; 120 BPM synth-pop/disco feel. | [topics/02-drums-four-on-the-floor.md](topics/02-drums-four-on-the-floor.md) |
| 03 | Drums: half-time at 140 | Kick on 1, snare on 3, sparse kicks, triplet hats and rolls; riddim/dubstep feel. | [topics/03-drums-half-time-140.md](topics/03-drums-half-time-140.md) |
| 04 | Bass fundamentals | Sub vs mid bass, mono, register (MIDI 28–40 sub, 36–52 mid), locking to the kick, in key. | [topics/04-bass-fundamentals.md](topics/04-bass-fundamentals.md) |
| 05 | Chords and keys | `set_scale`; major pop progressions (I–V–vi–IV family) and minor dubstep keys (i–VI–III–VII, i–VI); voicings and harmonic rhythm. | [topics/05-chords-and-keys.md](topics/05-chords-and-keys.md) |
| 06 | Pads and leads | Sound design basics on Drift / Wavetable / Analog: oscillator, filter, envelope, LFO; a lush pad, a bright lead, an arpeggio. | [topics/06-pads-and-leads.md](topics/06-pads-and-leads.md) |
| 07 | Wobble and growl bass | LFO → filter (Auto Filter first, then Wavetable position / Operator FM), Saturator or Roar, OTT, a separate clean sub, the resampling idea. | [topics/07-wobble-and-growl-bass.md](topics/07-wobble-and-growl-bass.md) |
| 08 | Sidechain and space | Compressor sidechain pump, Reverb/Delay on returns, sends, dry/wet thinking. | [topics/08-sidechain-and-space.md](topics/08-sidechain-and-space.md) |
| 09 | Arrangement structure | Section maps for both genres; scenes first, then Arrangement with `add_clip_to_arrangement` and `set_locator`. | [topics/09-arrangement-structure.md](topics/09-arrangement-structure.md) |
| 10 | Transitions and automation | Risers, filter sweeps, drum fills, the silent beat before a drop; `set_automation`. | [topics/10-transitions-and-automation.md](topics/10-transitions-and-automation.md) |
| 11 | Mixing basics | Gain staging (0.85 ≈ 0 dB), EQ Eight high-pass and mud cuts, bus thinking, mono low end. | [topics/11-mixing-basics.md](topics/11-mixing-basics.md) |
| 12 | Finishing | When a track is done, a finishing pass, export checklist in Live's UI, loudness awareness. | [topics/12-finishing.md](topics/12-finishing.md) |

Suggested order for this user: 00 → 01 → 02 → 05 → 04 → 06 → 08 → 09 → 10 → 11 → 12 for a synth-pop track; then 03 → 07 → 09 (riddim template) → 10 → 12 for a riddim track. Interleave if they get bored: 02 and 03 back to back is a good contrast lesson.

## Templates and references

- [templates/synth-pop-structure.md](templates/synth-pop-structure.md): ~3:36 at 120 BPM, bar-by-bar table, scene names, locator times, tool sequence.
- [templates/riddim-dubstep-structure.md](templates/riddim-dubstep-structure.md): ~3:33 at 140 BPM, same format.
- [genre-notes.md](genre-notes.md): conventions for both genres (tempo, drums, bass, harmony, palette, arrangement, mixing habits).

Use the templates in topics 09–12 and whenever the user says "help me finish this". Use genre-notes whenever a step needs a stylistic default ("what tempo?", "what key?", "which hat pattern?").

## Lesson hygiene

- Fresh set or fresh tracks: `create_midi_track(name=...)` with a clear name per role (Drums, Sub, Bass, Chords, Lead, FX). Colour by role with `set_track(color_index=...)` so the Session grid reads at a glance.
- Tempo first: `set_transport(tempo=120)` or `140`. Then key: `set_scale(root_note=..., scale_name="Major"|"Minor")`; if Live rejects the name, use the `available` list in the error.
- Keep the user's ears in the loop: fire the scene after every musical change; at the end, `stop` and clear any `solo`.
- Drum pads: read `get_devices(track, device_path="0")` → `drum_pads` before writing drum notes; default to 36 kick, 38 snare, 39 clap, 42 closed hat, 46 open hat if the kit follows the usual map.
- Clip math: a 4-bar clip is `length=16.0`; a 16-bar section needs that clip placed at `time`, `time+16`, `time+32`, `time+48`, or a `duplicate_clip_loop` ×2 first.
- Record in `why` the musical reason on every mutating call; the user replays the lesson with `/ableton-live:history`.

## Related commands

`/ableton-live:lesson <topic>` runs this skill. `/ableton-live:explain` and `/ableton-live:review` use the mentor's read-back without a plan. `/ableton-live:quiz` draws from the journal. `/ableton-live:study "<song>" by <artist>` (the `song-study` skill) is the practical companion: after topics 05–09, studying a track in the user's genre consolidates everything here.
