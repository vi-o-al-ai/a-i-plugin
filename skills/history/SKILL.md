---
name: history
description: List what Claude has changed in the Live set during this session, grouped by track, with the paths of the history files.
argument-hint: "[count]"
disable-model-invocation: true
allowed-tools:
  - Read(~/.claude-live/**)
  - mcp__plugin_ableton-live_live__get_history
---

# Action history

Arguments: `$ARGUMENTS` — optional number of most recent actions to show. Default 30. If it is not a positive integer, use 30 and say so in one line.

1. Call `get_history` with `limit=<count>` and `include_reads=false`.
2. Render the actions grouped by track, oldest first within each group. Group by `resolved.track_name`; actions without a track (transport, tempo, scale, scenes, locators, undo/redo) go under **Song**. For each action show the time from `ts` converted to local time (HH:MM:SS; `ts` is UTC ISO with a `Z`), the tool name, the target (the remaining `resolved` names joined with ` › `), the change from `result_summary` (for example `800 Hz → 1.20 kHz` or `+16 notes`), and the `why` after an em dash when present. Mark failed actions (`ok: false`) with `✗` and the error message.

```
Bass (track 1)
  14:03:22  set_parameter   Wavetable › Filter Freq   800 Hz → 1.20 kHz   — open the filter so the bass cuts through
  14:05:10  add_notes       Bass 1 (slot 0)           +16 notes           — root–fifth pattern for the verse
Song
  14:01:02  set_transport   tempo   120 → 124
```

3. End with the history file paths from the result (the `.jsonl` and the `.md` file) and one line explaining that the `.md` file is the human-readable log of this session and that earlier sessions are the sibling files in the same directory (`~/.claude-live/history/`, or `$CLAUDE_LIVE_HOME/history/` when that variable is set). If the user asks about an earlier session, read that `.md` file (reads under the default `~/.claude-live/` are pre-approved; a custom `CLAUDE_LIVE_HOME` prompts once).

If the history is empty, say that nothing has been changed in this session yet. Never mutate anything from this command.
