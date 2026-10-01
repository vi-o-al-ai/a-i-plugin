# Errors and what to do

Tool errors arrive as `"<CODE>: <message>. <hint>"`. The message is a sentence you can act on
("Track 9 does not exist (set has 4 tracks)"). Codes come from PROTOCOL.md §3.

## Application errors

| Code | Name | Meaning | Action |
|---|---|---|---|
| -32000 | `NOT_FOUND` | Track, scene, slot, clip, device, chain, parameter, locator or browser item does not exist. `data` has `kind`, `index`, `count`, or for parameters `name` + `available`. | Re-read (`get_session` / `get_track` / `get_devices`) and re-map names → indices. For a parameter, choose the closest name from `available` (UI label ≠ LOM name) and retry. Do not loop more than twice. |
| -32001 | `INVALID_STATE` | Object exists but the operation does not apply: slot occupied (`create_clip`, `duplicate_clip`), slot empty, clip is audio not MIDI, track cannot be armed, device has no chains. `data.reason` says which. | Explain in plain words; pick another slot/track or ask. Never delete something to make room unless the user asks. |
| -32002 | `CONFIRM_REQUIRED` | A destructive method was called without `confirm: true`. `data.target` names what would be deleted. | Ask the user, naming the target. Retry with `confirm=true` only after a yes. |
| -32003 | `UNSUPPORTED` | Installed Live lacks the API (`data.needs` / `data.have`), e.g. `set_scale` below Live 12. | Tell the user the feature needs the newer version; offer a manual alternative. |
| -32004 | `LIVE_ERROR` | The Live Object Model raised (`data.exception`, `data.detail`). | Report the detail. Retry a smaller or simpler operation (one parameter, fewer notes, a plain `value` instead of `display`). If it repeats, suggest Cmd+Z and check Live's Log.txt. |
| -32005 | `TOO_LARGE` | Over the batch limit (`data.limit`, `data.got`), e.g. > 5000 notes in one call. | Split the note list into chunks of ≤ 500 and call `add_notes` repeatedly. |
| -32006 | `TIMEOUT` | A bounded operation (browser traversal) ran out of budget. Reserved; `browse` normally returns `truncated: true` instead. | Narrow the `query`/`categories`, or list a specific `uri`. |

## JSON-RPC errors (should not normally reach you)

| Code | Meaning | Action |
|---|---|---|
| -32700 | Parse error | Server bug; report it. |
| -32600 | Invalid request (line too long > 4 MiB) | Send less data per call. |
| -32601 | Method not found | Version mismatch between server and Remote Script; `ableton_status` shows both versions. |
| -32602 | Invalid params: wrong type, out of range, missing required param, `display` not in `value_items`, unknown scale name (comes with `available`). | Fix the argument. For `display`, read `value_items` first; for `set_scale`, use a name from `available`. |
| -32603 | Internal error in the Remote Script | Report; retry once; suggest reselecting ClaudeLive in Preferences. |

## Connection problems (from the MCP server, PROTOCOL.md §8)

| Symptom | Likely cause | What to tell the user |
|---|---|---|
| "Connection refused" / `ableton_status` → `connected: false` | Live is not running, or the ClaudeLive control surface is not selected. | Open Live → Preferences → Link, Tempo & MIDI → Control Surface → pick **ClaudeLive**. Confirm the port in the Remote Script `config.json` equals `CLAUDE_LIVE_PORT` (default 9892). |
| Timeout (reads 5 s, mutations 15 s, browser/overview 60 s) | Live is showing a modal dialog, loading a set, scanning plug-ins, or frozen. | Look at Live and close any dialog; wait for loading; then run `ableton_status` again. |
| Protocol error with a raw line | Version skew or a corrupted response. | Run `ableton_status`; compare script vs server versions; restart the server if they differ. |

The client reconnects transparently on the next call after a failure, so after the user fixes the
cause, simply call `ableton_status` and continue.

## Partial failures

- `set_parameters` returns `results` and `errors` side by side. Report both: which parameters changed and which failed (with their messages), then fix the failing ones individually.
- `modify_notes` returns `missing_ids`; if non-empty, `get_notes` again (ids changed because the clip was edited) and redo the change.
- `load_device` always loads *something* when `name` matches; check `matched` and clean up with `delete_device(confirm=true)` if it is the wrong device.
