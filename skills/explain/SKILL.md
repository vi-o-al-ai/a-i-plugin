---
name: explain
description: Explain in beginner terms what the selected track, clip or device in Ableton Live is and what it is doing musically.
argument-hint: "[what]"
disable-model-invocation: true
allowed-tools:
  - Read
  - mcp__plugin_ableton-live_live__get_selection
  - mcp__plugin_ableton-live_live__get_session
  - mcp__plugin_ableton-live_live__get_transport
  - mcp__plugin_ableton-live_live__get_track
  - mcp__plugin_ableton-live_live__get_clip
  - mcp__plugin_ableton-live_live__get_notes
  - mcp__plugin_ableton-live_live__get_devices
  - mcp__plugin_ableton-live_live__get_automation
---

# Explain what is selected

Arguments: `$ARGUMENTS` — optional. When present it names what to explain instead of the current selection, for example `the bass track`, `the compressor on Drums`, `track 2 clip 0`, `the Filter Freq knob`, or a concept such as `sidechain`. For a concept, explain it and then show where (if anywhere) the set uses it.

1. Read the mentor skill first and follow its voice and teaching rules: `${CLAUDE_PLUGIN_ROOT}/skills/production-mentor/SKILL.md`. (If that path still reads literally as `${CLAUDE_PLUGIN_ROOT}/...`, the plugin root is two directories above this `SKILL.md`: skills live at `<plugin root>/skills/<name>/SKILL.md`.)
2. Call `get_selection`. If `$ARGUMENTS` names an object, call `get_session` with `include_clips=false, include_params=false` to find it by name or index. Call `get_transport` for the tempo and `get_session`'s `scale` for the key when you need musical context.
3. Fetch the most specific thing selected:
   - **Device** (`selection.device` is set, or a `parameter` is selected): `get_devices` with that `device_path` and `include_params=true`. Explain what kind of device it is, what it does to the sound, and read the 3 to 6 parameters that matter most *right now* (far from default, automated, or the selected parameter) with their display values.
   - **Clip** (`detail_clip` is set, or `clip_slot.has_clip`): `get_clip` and `get_notes`. Describe length and looping, the note count and range, the rhythm (grid, density, swing or straight), the harmony (which pitches, implied chords, how they sit in the set's scale) and the dynamics (velocities). For an audio clip, describe what `get_clip` reports and say that Claude cannot hear it.
   - **Track** otherwise: `get_track` with `include_devices=true`. Explain its role, the instrument, the effect chain in signal order, and the mixer state (volume, pan, sends, mute/solo/arm).
4. Explain for a beginner: what it is, what it is doing to the music, and why someone might set it up this way. Use one analogy, define any jargon on first use, and keep it under about 250 words unless asked for more. End with one small, concrete thing to try, and offer to do it.

This command is read-only. Do not change the set, the transport or the view.
