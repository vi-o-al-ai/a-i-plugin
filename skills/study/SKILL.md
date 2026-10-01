---
name: study
description: Study a reference song — its structure, harmony, rhythm and sound design — and rebuild its ideas as a learning sketch in the open Live set.
argument-hint: "\"<song>\" by <artist>"
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

# Song study

Arguments: `$ARGUMENTS` — the song to study, as `"<song>" by <artist>`. If it is empty or ambiguous, ask for the song and artist before doing anything else.

1. Read the song-study skill and follow it exactly, with `$ARGUMENTS` as the song reference: `${CLAUDE_PLUGIN_ROOT}/skills/song-study/SKILL.md`. It defines how to analyse the reference (structure, tempo and key, harmony, rhythm, sound design, arrangement) and how to rebuild its ideas as a learning sketch in Live. Also read `${CLAUDE_PLUGIN_ROOT}/skills/production-mentor/SKILL.md` for the teaching voice if the song-study skill does not already say to. (If those paths still read literally as `${CLAUDE_PLUGIN_ROOT}/...`, the plugin root is two directories above this `SKILL.md`: skills live at `<plugin root>/skills/<name>/SKILL.md`.)
2. Call `ableton_status` before building anything. If Live is not connected, do the analysis part only and say that the Live sketch can be built after `/ableton-live:setup`.
3. Build only on new tracks and clips (never inside the user's existing material unless asked), fill in `why` on every mutating tool call, and never delete anything; use `undo` to revert your own steps when asked. Original ideas and techniques are the point: write your own material in the song's style rather than copying its recorded melody or lyrics.
4. If the song-study skill asks for it, record the study in the learning journal at `~/.claude-live/journal.md` (expand `~`; `$CLAUDE_LIVE_HOME/journal.md` if that variable is set), creating the file if needed.
