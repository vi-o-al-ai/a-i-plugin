---
name: quiz
description: Ask five short questions on recently learned production topics, check answers against the open Live set where possible, and record the results in the learning journal.
argument-hint: "[topic]"
disable-model-invocation: true
allowed-tools:
  - Read
  - Write(~/.claude-live/**)
  - Edit(~/.claude-live/**)
  - mcp__plugin_ableton-live_live__ableton_status
  - mcp__plugin_ableton-live_live__get_session
  - mcp__plugin_ableton-live_live__get_transport
  - mcp__plugin_ableton-live_live__get_track
  - mcp__plugin_ableton-live_live__get_clip
  - mcp__plugin_ableton-live_live__get_notes
  - mcp__plugin_ableton-live_live__get_devices
  - mcp__plugin_ableton-live_live__get_selection
---

# Quiz

Arguments: `$ARGUMENTS` — optional topic to quiz on. Empty means the most recent lesson topics from the journal.

1. Read the mentor skill and follow its voice: `${CLAUDE_PLUGIN_ROOT}/skills/production-mentor/SKILL.md`. (If that path still reads literally as `${CLAUDE_PLUGIN_ROOT}/...`, the plugin root is two directories above this `SKILL.md`: skills live at `<plugin root>/skills/<name>/SKILL.md`.)
2. Read the learning journal at `~/.claude-live/journal.md` (or `$CLAUDE_LIVE_HOME/journal.md` when that variable is set; expand `~`). Reads and writes under the default `~/.claude-live/` are pre-approved; a custom `CLAUDE_LIVE_HOME` prompts once. Pick the topics: `$ARGUMENTS` if given, otherwise the last one or two lessons, weighted toward things the journal marks as difficult. If there is no journal, say so, ask what they have been working on, and quiz on that.
3. Call `ableton_status`. If Live is connected, call `get_session` with `include_clips=true, include_params=false` so that some questions can be about the user's own set ("What key is this set in?", "Which device on Bass shapes the low end?", "How many bars is the clip in Drums slot 0?"). Check such answers with the matching read tool (`get_transport`, `get_notes`, `get_devices`, `get_clip`). If Live is not connected, ask conceptual questions only.
4. Ask **five short questions, one at a time**. Wait for each answer before asking the next. After each answer say whether it is right, give the correct answer in one or two sentences when it is not, and move on. Mix recall ("what does a compressor's ratio do?") with application ("which parameter would you move to make this kick punch through the bass, and which way?").
5. Finish with the score (n/5), one sentence on what to revisit, and update the journal (create it from `${CLAUDE_PLUGIN_ROOT}/skills/production-mentor/journal-template.md` if needed) in that template's format: raise a concept's confidence in Concepts covered per its rules (a correct answer moves 1 → 2), add a dated Struggles line per missed question with the score (n/5), and replace Next up with the suggested revisit. Suggest `/ableton-live:lesson <weak topic>` when the score is 3/5 or below.

This command is read-only with respect to the Live set.
