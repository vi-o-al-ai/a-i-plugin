---
name: review
description: Give a structured, beginner-friendly critique of the open Live set — what works, what to change and why, plus one exercise.
disable-model-invocation: true
allowed-tools:
  - Read
  - mcp__plugin_ableton-live_live__ableton_status
  - mcp__plugin_ableton-live_live__get_session
  - mcp__plugin_ableton-live_live__get_transport
  - mcp__plugin_ableton-live_live__get_arrangement
  - mcp__plugin_ableton-live_live__get_track
  - mcp__plugin_ableton-live_live__get_clip
  - mcp__plugin_ableton-live_live__get_notes
  - mcp__plugin_ableton-live_live__get_devices
  - mcp__plugin_ableton-live_live__get_automation
  - mcp__plugin_ableton-live_live__get_selection
---

# Review the set

Arguments: `$ARGUMENTS` — optional focus, for example `the drums`, `arrangement`, `mix`, `harmony`. Empty means review the whole set.

1. Read the mentor skill first and follow its voice and rules: `${CLAUDE_PLUGIN_ROOT}/skills/production-mentor/SKILL.md`. (If that path still reads literally as `${CLAUDE_PLUGIN_ROOT}/...`, the plugin root is two directories above this `SKILL.md`: skills live at `<plugin root>/skills/<name>/SKILL.md`.)
2. Gather the picture:
   - `get_session` with `include_clips=true, include_devices=true, include_params=false` — tracks, instruments, effect chains, mixer state, scenes, scale.
   - `get_arrangement` with `include_clips=true` — song length, locators, how the clips sit over time (or whether the set is Session-only).
   - `get_notes` on a few key clips: the main drum clip, the bass, the chords or lead, and anything the focus names. Look at rhythm, range, harmony against the set's scale, velocities and length. Keep it to a handful of clips; do not read everything.
   - `get_devices` with `include_params=true` on one or two chains where the mix question lives (for example the bass or master) when relevant.
3. Write the critique in this structure, for a beginner:
   - **What works** — two or three specific strengths, each tied to something concrete in the set (a track, clip or device by name).
   - **What to change** — the three most valuable changes, in priority order. For each: what, where (track/clip/device), and **why** in plain language (what the listener will hear differently). Prefer changes the user can do themselves in a few minutes.
   - **One exercise** — a single focused task that teaches the main idea behind the top change, with the steps in Live and what to listen for.
   Keep the whole review under about 400 words. Remember that Claude cannot hear the audio: say so when a judgement depends on the sound rather than on the notes and settings.
4. Do not change anything unless the user asks. If they want a change made, do it one step at a time, with `why` filled in, and tell them how to undo it (Cmd+Z in Live, or ask Claude to `undo`).
