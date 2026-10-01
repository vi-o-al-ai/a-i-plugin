---
name: lesson
description: Run an interactive, hands-on music production lesson inside the open Live set, following the plugin curriculum and the user's learning journal.
argument-hint: "[topic]"
disable-model-invocation: true
allowed-tools:
  - Read
  - Write
  - Edit
  - mcp__plugin_ableton-live_live__ableton_status
  - mcp__plugin_ableton-live_live__get_session
  - mcp__plugin_ableton-live_live__get_transport
  - mcp__plugin_ableton-live_live__get_track
  - mcp__plugin_ableton-live_live__get_clip
  - mcp__plugin_ableton-live_live__get_notes
  - mcp__plugin_ableton-live_live__get_devices
  - mcp__plugin_ableton-live_live__get_selection
  - mcp__plugin_ableton-live_live__get_arrangement
  - mcp__plugin_ableton-live_live__get_automation
  - mcp__plugin_ableton-live_live__browse
  - mcp__plugin_ableton-live_live__play
  - mcp__plugin_ableton-live_live__stop
  - mcp__plugin_ableton-live_live__continue_playing
  - mcp__plugin_ableton-live_live__set_transport
  - mcp__plugin_ableton-live_live__set_scale
  - mcp__plugin_ableton-live_live__undo
  - mcp__plugin_ableton-live_live__redo
  - mcp__plugin_ableton-live_live__create_midi_track
  - mcp__plugin_ableton-live_live__create_audio_track
  - mcp__plugin_ableton-live_live__create_return_track
  - mcp__plugin_ableton-live_live__set_track
  - mcp__plugin_ableton-live_live__create_scene
  - mcp__plugin_ableton-live_live__set_scene
  - mcp__plugin_ableton-live_live__fire_scene
  - mcp__plugin_ableton-live_live__duplicate_scene
  - mcp__plugin_ableton-live_live__create_clip
  - mcp__plugin_ableton-live_live__set_clip
  - mcp__plugin_ableton-live_live__fire_clip
  - mcp__plugin_ableton-live_live__stop_clip
  - mcp__plugin_ableton-live_live__duplicate_clip
  - mcp__plugin_ableton-live_live__duplicate_clip_loop
  - mcp__plugin_ableton-live_live__add_notes
  - mcp__plugin_ableton-live_live__replace_notes
  - mcp__plugin_ableton-live_live__remove_notes
  - mcp__plugin_ableton-live_live__modify_notes
  - mcp__plugin_ableton-live_live__quantize_notes
  - mcp__plugin_ableton-live_live__transpose_notes
  - mcp__plugin_ableton-live_live__set_parameter
  - mcp__plugin_ableton-live_live__set_parameters
  - mcp__plugin_ableton-live_live__set_device_enabled
  - mcp__plugin_ableton-live_live__load_device
  - mcp__plugin_ableton-live_live__add_clip_to_arrangement
  - mcp__plugin_ableton-live_live__set_locator
  - mcp__plugin_ableton-live_live__set_automation
  - mcp__plugin_ableton-live_live__select
  - mcp__plugin_ableton-live_live__show_view
---

# Lesson

Arguments: `$ARGUMENTS` — optional topic, for example `drum programming`, `sidechain compression`, `chord voicings`, `arrangement`. Empty means "propose the next topic".

## Prepare

1. Read, in this order, and follow both:
   - `${CLAUDE_PLUGIN_ROOT}/skills/production-mentor/SKILL.md` — how to teach (voice, pacing, the mentor modes).
   - `${CLAUDE_PLUGIN_ROOT}/skills/curriculum/SKILL.md` — what to teach, in which order, how a lesson is structured, and how the journal is formatted.
   (If those paths still read literally as `${CLAUDE_PLUGIN_ROOT}/...`, the plugin root is two directories above this `SKILL.md`: skills live at `<plugin root>/skills/<name>/SKILL.md`.)
2. Read the learning journal at `~/.claude-live/journal.md` if it exists (expand `~` to the user's home directory; if `CLAUDE_LIVE_HOME` is set, the journal is `$CLAUDE_LIVE_HOME/journal.md`). It records past lessons, quiz results and what the user found hard. If it does not exist this is the first lesson: ask two or three quick questions about their experience and what they want to make, and create the journal with that as its first entry.
3. Call `ableton_status`. If Live is not connected, say so, suggest `/ableton-live:setup`, and offer a talk-only lesson instead of stopping.
4. Call `get_session` with `include_clips=true, include_params=false` so the lesson builds on what is already in the set.

## Pick the topic

- If `$ARGUMENTS` names a topic, use it, placed where it falls in the curriculum.
- Otherwise propose the next topic from the curriculum given the journal (not yet covered, prerequisites done, weakest recent quiz area first) in one sentence with one alternative, and let the user confirm or choose.

## Run the lesson

Follow the lesson structure from the curriculum skill. In general: one idea at a time; explain → demonstrate in the set → have the user do a step themselves → listen together → reflect. Build in the user's set wherever possible, on a new track or clip rather than inside their material unless they ask. Fill in `why` on every mutating tool call so the action history reads as a lesson log. After each change, tell the user exactly what to look at or listen to in Live, and use `play`/`stop` so they can hear it. Never delete anything; use `undo` to revert your own demonstrations when asked.

Keep messages short, ask one question at a time, and check understanding with a question before moving on.

## Wrap up

When the lesson ends (or the user wants to stop), append an entry to the journal, creating the file if needed: date, topic, what was covered, what the user did themselves, what was difficult, and one suggested next topic. Use the journal format defined by the curriculum skill; if it defines none, use a `## YYYY-MM-DD — Lesson: <topic>` heading followed by short bullets. Tell the user it was recorded and how to continue (`/ableton-live:quiz` to check retention, `/ableton-live:lesson` for the next one).
