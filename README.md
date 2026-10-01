# Ableton Live for Claude Code

A Claude Code plugin that lets Claude **control** Ableton Live 12 and **teach you** to make music in it. Ask for a bassline in C minor on a new track and it appears in your set; ask what the compressor on your drum bus is doing and you get a plain-language answer about *your* settings; run a lesson and Claude builds the example in your own project, has you try the next step, and keeps a learning journal between sessions. Everything runs on your machine: a small Remote Script inside Live talks over localhost to an MCP server that Claude Code launches, and every change is a normal, undoable Live edit.

## Requirements

- **macOS.** The installer and troubleshooting paths are macOS-specific; the Remote Script and server are plain Python, but only macOS is supported in 0.1.
- **Ableton Live 12**, any edition (Intro, Standard or Suite). The Remote Script targets Live 12 and works with the Python 3.7 embedded in Live 12.0–12.2 and the Python 3.11 in 12.3+; Live 11 is not supported.
- **Claude Code** (Pro or Max plan, or an API key).
- **[uv](https://docs.astral.sh/uv/)** to run the Python MCP server. Install with `curl -LsSf https://astral.sh/uv/install.sh | sh` (or `brew install uv`) and restart Claude Code afterwards. The plugin looks for `uv` in `~/.local/bin`, `/opt/homebrew/bin`, `/usr/local/bin` and `~/.cargo/bin` as well as on your PATH, so the standard install is found even when Claude Code is launched from the Dock; if you installed it elsewhere, put that directory on the PATH of the shell that starts Claude Code.

## Install

In Claude Code:

```
/plugin marketplace add vi-o-al-ai/a-i-plugin
/plugin install ableton-live@a-i-plugin
```

The second command opens the plugin's details so you can review it and pick a scope (choose **user** so it is available in every project). On Claude Code 2.1.275 or later the one-step form `/plugin install ableton-live --marketplace vi-o-al-ai/a-i-plugin` does the same. From a shell:

```bash
claude plugin marketplace add vi-o-al-ai/a-i-plugin
claude plugin install ableton-live@a-i-plugin
```

Then, in Claude Code, run the guided setup:

```
/ableton-live:setup
```

It checks for `uv`, asks before running the installer that copies the `ClaudeLive` Remote Script into `~/Music/Ableton/User Library/Remote Scripts/`, pre-builds the server's Python environment, and tells you how to enable the control surface in Live. If you have moved your User Library, run the installer with `ABLETON_USER_LIBRARY="<path to your User Library>"` so it targets the right folder. If you prefer to do it by hand, the installer is `scripts/install-remote-script.sh` inside the plugin directory, and the manual steps are:

1. Copy `remote-script/ClaudeLive` to `~/Music/Ableton/User Library/Remote Scripts/ClaudeLive` (or into the `Remote Scripts` folder of your User Library, wherever you keep it).
2. Restart Live. In **Settings → Link, Tempo & MIDI** (the Settings window is called Preferences in older Live versions; Cmd+, opens it either way), pick **ClaudeLive** in a free **Control Surface** slot and leave **Input** and **Output** set to **None**.

Updates: `claude plugin update ableton-live@a-i-plugin` (or enable auto-update for the `a-i-plugin` marketplace in `/plugin`). After updating the plugin, re-run `/ableton-live:setup` so the Remote Script inside Live is updated too. Each re-install keeps the previous copy next to it as `ClaudeLive.bak-<timestamp>`; `scripts/uninstall-remote-script.sh --all` clears those backups.

## First run

1. Start Live with ClaudeLive enabled and open any set.
2. In Claude Code run `/ableton-live:status`. You should see the Live version, the round-trip time, and a summary of your set.
3. Try something: *"Add a MIDI track called Pad with Wavetable and write a four-chord progression in the set's key."* Claude creates the track, loads the instrument, writes the clip, and tells you what it did. Press Cmd+Z in Live if you do not like it.

The very first launch of the MCP server can take a minute or two while `uv` installs the dependencies and, when no suitable Python 3.11+ is on your machine, downloads a managed Python. The plugin's SessionStart hook does the same pre-build when a session starts (it gives up after three minutes and leaves the server to finish the job), so the first session after installing may start slowly; later sessions cost nothing. If the `live` server shows as failed in `/mcp`, choose **Reconnect** once the install has finished.

## What Claude can do

The MCP server exposes 55 tools (`docs/TOOLS.md` is the full list). By area:

| Area | Tools |
| :- | :- |
| **Status** | `ableton_status` (is Live reachable, versions, diagnosis), `get_history` (what changed this session), `ableton_describe_api` (dump the real Live API to `~/.claude-live/api/` for debugging) |
| **Session & transport** | read the whole set at once (`get_session`), tempo, time signature, loop, metronome, position, play/stop/continue, set the scale (Live 12), undo/redo |
| **Tracks** | create MIDI, audio and return tracks; rename, colour, mute, solo, arm, volume, pan, sends, fold; delete (with confirmation) |
| **Scenes** | create, rename, colour, scene tempo, fire, duplicate, delete |
| **Clips** | create MIDI clips, read and set name, colour, loop points, markers, launch quantization; fire, stop, duplicate, double the loop; delete; copy a Session clip into the Arrangement |
| **Notes** | read, add, replace, remove and modify notes by id (pitch, start, duration, velocity, probability, velocity deviation, mute); quantize with swing; transpose a range |
| **Devices** | list device chains including racks and drum pads, read parameters with display values, set one or many parameters by value, normalized value or display string, enable/disable, delete |
| **Browser** | search Live's browser (instruments, drums, effects, sounds, plugins, packs, user library) and load a device onto a track by URI or by name |
| **Arrangement** | overview with song length, locators and clip positions; add and delete locators |
| **Automation** | read, write (steps or ramps) and clear clip envelopes for any device or mixer parameter |
| **View** | read the current selection; select tracks, scenes, slots and devices; switch between Session, Arranger, Clip, Device and Browser views |

Every mutating tool takes an optional `why`, which the server writes into the action history so the log reads as a story of the session, not a list of calls. Destructive tools (`delete_*`, clearing all automation) refuse to run without an explicit `confirm`.

## Learning features

Six knowledge skills ship with the plugin and load when relevant: `ableton-live` (the operating manual for driving Live through the tools: addressing, beat math, the write-then-verify loop, confirm/undo safety, recipes), `live-devices` (Live's instruments, audio effects and MIDI effects and what their parameters do), `midi-writing` (drum grids, chord progressions and voicings, bass, arps and hooks, arrangement patterns and humanization, with synth-pop and riddim/dubstep as the worked examples), `production-mentor` (how Claude teaches: four teaching modes, verifying by reading the set back, pointing at Live's UI, and the learning journal), `curriculum` (a beginner's path from loops to finished tracks: a topic tree with a 15–20 minute plan per topic, genre conventions and bar-by-bar structure templates) and `song-study` (how to analyse a reference song and rebuild its ideas as a sketch).

On top of those, five commands turn your open set into the classroom:

| Command | What it does |
| :- | :- |
| `/ableton-live:lesson [topic]` | A hands-on lesson in your set, following the curriculum and your journal; proposes the next topic when none is given |
| `/ableton-live:explain [what]` | Explains the selected track, clip or device (or whatever you name) in beginner terms: what it is and what it is doing musically |
| `/ableton-live:review` | A structured critique of the set: what works, what to change and why, and one exercise |
| `/ableton-live:quiz` | Five short questions on recent topics, checked against your set where possible |
| `/ableton-live:study "<song>" by <artist>` | Studies a reference song's structure, harmony, rhythm and sound, and rebuilds the ideas as a learning sketch |

Plus two utilities: `/ableton-live:status` (connection and set summary) and `/ableton-live:history [count]` (what Claude changed this session, by track). The short forms `/lesson`, `/explain`, `/quiz`, `/study` also work when no other command uses those names.

Two files persist between sessions, both under `~/.claude-live/`:

- **`journal.md`** — the learning journal. Lessons and quizzes append to it; `/lesson` reads it to pick up where you left off.
- **`history/`** — one `.jsonl` and one `.md` file per session, listing every change Claude made (with the `why`), so you can see what happened and recreate or revert it later.

## How it works

```
Claude Code ──MCP (stdio)──▶ ableton-live-mcp ──JSON-RPC over TCP 127.0.0.1:9892──▶ ClaudeLive Remote Script ──▶ Live Object Model
             (plugin .mcp.json)   (Python, run by uv)                                  (inside Live, its Python 3.7 or 3.11)
```

- **Two processes.** The Remote Script runs inside Live as a Control Surface. The MCP server is a separate process that Claude Code starts with `uv run`; it is a thin client that turns tool calls into protocol requests. The contract between them is `docs/PROTOCOL.md`.
- **JSON-RPC 2.0 over localhost.** Newline-delimited JSON on the loopback interface only (`127.0.0.1` by default). The script refuses to bind any other interface, and nothing is sent anywhere else: no telemetry, no cloud, no uploads. The only thing that leaves your machine is the conversation you are already having with Claude.
- **Main-thread execution.** A background thread accepts connections and queues requests; a 100 ms tick on Live's main thread drains the queue, processing a bounded number of requests per tick (at most 32, within about 50 ms), so Live's UI never stalls and the LOM is only ever touched from the thread Live expects.
- **No code execution.** The script implements a fixed set of named methods (`notes.add`, `device.set_parameter`, ...). It never evaluates code sent by Claude. Every index is validated and every error is a readable sentence Claude can act on.
- **Undo-friendly.** Every change is an ordinary Live edit, so Cmd+Z works, and Claude can call `undo` itself. Destructive operations need `confirm: true`. Nothing is batched behind your back: one tool call, one visible change.
- **Never saves.** The plugin never saves your set. You decide when to press Cmd+S.
- **State lives in your home directory, not the plugin.** History and the journal are in `~/.claude-live/` rather than in Claude Code's per-plugin data directory, so they survive uninstalling or reinstalling the plugin and are easy to find and back up. The server's Python environment, which is disposable, lives in the plugin data directory (`~/.claude/plugins/data/ableton-live-a-i-plugin/venv`) and is removed when you uninstall.

## Configuration

| Setting | Where | Default |
| :- | :- | :- |
| Port | `config.json` inside the installed Remote Script (`Remote Scripts/ClaudeLive/config.json` in your User Library) **and** `CLAUDE_LIVE_PORT` for the server. Both must match. | `9892` |
| Host | `CLAUDE_LIVE_HOST` (server side; the script binds the loopback interface only) | `127.0.0.1` |
| Data directory | `CLAUDE_LIVE_HOME` — history, logs and the journal | `~/.claude-live` |
| Server log level | `CLAUDE_LIVE_LOG_LEVEL` (stderr and `$CLAUDE_LIVE_HOME/logs/server.log`) | `INFO` |
| User Library | `ABLETON_USER_LIBRARY` for the install and uninstall scripts, if you moved your User Library | `~/Music/Ableton/User Library` |

Server-side variables are read from the environment Claude Code was started in, so export them in your shell (for example in `~/.zshrc`) before launching `claude`. The plugin's own `.mcp.json` sets only `UV_PROJECT_ENVIRONMENT`, so that the server's virtualenv is built in the plugin data directory instead of inside the plugin; everything else passes through to the server untouched.

## Troubleshooting

Start with `/ableton-live:status`; its failure output already names the most likely cause. Then:

- **ClaudeLive is not in the Control Surface list.** The folder is in the wrong place or incomplete. It must be `Remote Scripts/ClaudeLive/` inside your User Library (`~/Music/Ableton/User Library` unless you moved it; Live shows the location under Settings → Library) and contain `__init__.py`. Re-run `/ableton-live:setup` (or `scripts/install-remote-script.sh`, with `ABLETON_USER_LIBRARY="<path>"` for a moved library) and restart Live; Live only scans for scripts at startup.
- **Connection refused.** Live is not running, or ClaudeLive is not selected as a Control Surface, or the port in `config.json` does not match `CLAUDE_LIVE_PORT`. Select it in Settings → Link, Tempo & MIDI → Control Surface; if you changed the port, change it on both sides.
- **Timeouts.** Live is showing a modal dialog (a save prompt, a missing-file dialog, a plug-in window), is still loading a set, or is frozen. Dismiss the dialog and try again; the server reconnects on the next call.
- **The `live` MCP server does not start.** Is `uv` installed? The launcher (`scripts/run-server.sh`) searches the standard install locations and writes a one-paragraph diagnosis to Claude Code's debug log when it cannot find `uv`; an outdated `uv` can also refuse the lockfile, so try `uv self update`. Run `/mcp` and look at `plugin:ableton-live:live`; the first start can take a minute while uv builds the environment, so try **Reconnect**. For the launcher's and the server's own error output start Claude Code with `claude --debug` and read `~/.claude/debug/<session-id>.txt`, or look at `~/.claude-live/logs/server.log`.
- **Live's log.** The Remote Script writes to Live's log at `~/Library/Preferences/Ableton/Live 12.x.x/Log.txt` (replace `12.x.x` with your version). Search it for `ClaudeLive` to see the script loading, the port it bound, and any exceptions.
- **Something in Live's API is not what Claude expects.** Ask Claude to call `ableton_describe_api`. It writes a Markdown dump of the real Live API, taken from inside *your* Live, under `~/.claude-live/api/` (or `$CLAUDE_LIVE_HOME/api/`) and returns the path, so Claude can read it to correct itself.
- **Uninstalling.** `claude plugin uninstall ableton-live@a-i-plugin` removes the plugin; `scripts/uninstall-remote-script.sh` removes the Remote Script from Live. `~/.claude-live/` is never deleted automatically.

## Development

```
.claude-plugin/     plugin.json + marketplace.json (the repo is its own marketplace)
.mcp.json           launches the server via scripts/run-server.sh: uv run --frozen --no-dev --directory ${CLAUDE_PLUGIN_ROOT}/server ableton-live-mcp
hooks/              SessionStart hook that pre-builds the server venv (scripts/prewarm.sh)
remote-script/      ClaudeLive, the Remote Script (stdlib-only Python; runs on Live's embedded 3.7 or 3.11)
server/             ableton-live-mcp, the MCP server (uv project)
skills/             knowledge skills and slash commands (skills with disable-model-invocation: true)
scripts/            server launcher (run-server.sh), installer, uninstaller, pre-warm hook
tests/              tests for the Remote Script and protocol; integration/ drives the real server end to end
docs/               PROTOCOL.md and TOOLS.md are the contracts; research/ holds the background notes
```

Run the tests:

```bash
uv run --directory server pytest                       # MCP server
python3 -m pytest tests                                # Remote Script and protocol
uv run --directory server pytest ../tests/integration  # end to end, through the server venv
```

Validate the plugin and try it locally without installing:

```bash
claude plugin validate .                              # marketplace.json + plugin.json
claude plugin validate ./.claude-plugin/plugin.json   # plugin.json + .mcp.json
claude --plugin-dir .                                 # one-session load; /reload-plugins after edits
```

`docs/PROTOCOL.md` and `docs/TOOLS.md` are the source of truth for the two halves; when code and contract disagree, fix one of them. Contributor notes are in `CLAUDE.md`.

## Limitations

- **Claude cannot hear audio.** It reasons from notes, parameters and names. Judgements about how something sounds are yours to make; Claude will say when a suggestion depends on listening.
- **No audio clip import yet.** Audio tracks can be created and mixed, but samples and audio clips cannot be imported or edited in 0.1.
- **Sidechain routing must be set by hand.** Live's scripting API does not expose a compressor's sidechain source, so Claude can load and tune the compressor but you pick the sidechain input in the device yourself.
- **Live 12 only**, and macOS only in this release. Automation is written to Session clip envelopes; Arrangement clip envelopes work only where Live's API allows it.
- Claude Code's MCP output limit applies: very large sets are read in parts (`include_clips=false`, per-track calls) rather than all at once.

## License

MIT. See `LICENSE`.
