<!-- Contributor notes for working ON this repository. Claude Code does not load a plugin's root CLAUDE.md for people who INSTALL the plugin (and `claude plugin validate` warns that it is here); user-facing instructions belong in skills/. -->

# a-i-plugin — contributor notes

This repo is a Claude Code plugin (`ableton-live`) and its own one-entry marketplace (`a-i-plugin`). The plugin root is the repo root.

## Layout

| Path | What |
| :- | :- |
| `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json` | Plugin manifest and self-hosting marketplace |
| `.mcp.json`, `scripts/run-server.sh` | Launches the MCP server: `bash scripts/run-server.sh`, which prepends uv's usual install locations to PATH and then `exec`s `uv run --frozen --no-dev --directory ${CLAUDE_PLUGIN_ROOT}/server ableton-live-mcp`. Diagnostics go to stderr only; stdout is the MCP transport |
| `hooks/hooks.json`, `scripts/prewarm.sh` | SessionStart hook that pre-builds the server venv in `${CLAUDE_PLUGIN_DATA}/venv` (180 s timeout; returns at once when the venv already has `bin/ableton-live-mcp`; never prints to stdout, never exits non-zero) |
| `remote-script/ClaudeLive/` | The Remote Script that runs inside Live 12 on Live's embedded Python: **3.7 in Live 12.0–12.2, 3.11 in 12.3+**, so **stdlib only and no 3.8+ syntax** (no walrus, positional-only parameters, dict-union operator or `match`); `tests/remote_script/test_py37_syntax.py` enforces it |
| `server/` | The MCP server, a uv project; console script `ableton-live-mcp`; commit `uv.lock` |
| `skills/<name>/SKILL.md` | Knowledge skills (`ableton-live`, `live-devices`, `midi-writing`, `production-mentor`, `curriculum`, `song-study`) and slash commands (`setup`, `status`, `history`, `explain`, `lesson`, `review`, `quiz`, `study`, all `disable-model-invocation: true`) |
| `scripts/install-remote-script.sh`, `scripts/uninstall-remote-script.sh` | macOS installer and uninstaller for the Remote Script (`ABLETON_USER_LIBRARY` overrides the User Library path; a re-install keeps the previous copy as `ClaudeLive.bak-<timestamp>`) |
| `tests/` | Tests for the Remote Script and the protocol (plain pytest, no third-party deps); `tests/integration/` is end to end through the real server and runs in the server venv (it skips where `mcp` is missing) |
| `docs/PROTOCOL.md`, `docs/TOOLS.md` | **The contracts** (see below) |
| `docs/research/` | Research notes: `claude-code-plugin.md` (plugin format), `mcp-sdk.md` (MCP SDK), `live-api.md` (Live's Python API, the embedded Python versions, Log.txt and User Library paths) |

## Source of truth

`docs/PROTOCOL.md` (wire protocol between the Remote Script and the server) and `docs/TOOLS.md` (the MCP tool surface) are the contracts. The Remote Script, the server, the tests, the skills and the README are all written from them. If code and a contract disagree, fix one of them in the same change; never let them drift. Tool names in skills are the plugin-qualified form `mcp__plugin_ableton-live_live__<tool>`.

## Running tests

```bash
uv run --directory server pytest                       # MCP server tests (uv project in server/)
python3 -m pytest tests                                # Remote Script / protocol tests (stdlib + pytest)
uv run --directory server pytest ../tests/integration  # end-to-end tests, through the server venv (needs uv)
```

## Validating the plugin

```bash
claude plugin validate .                            # marketplace.json + plugin.json
claude plugin validate ./.claude-plugin/plugin.json # plugin.json + .mcp.json
claude --plugin-dir . plugin details ableton-live   # component inventory
claude --plugin-dir .                               # try it in a session; /reload-plugins after edits
```

## Rules

- Never write state under the plugin root at runtime (it is a versioned cache dir once installed); the server venv goes to `${CLAUDE_PLUGIN_DATA}/venv`, user data to `~/.claude-live` (`CLAUDE_LIVE_HOME`).
- The Remote Script binds the loopback interface only (`127.0.0.1` by default) and executes a fixed set of JSON-RPC methods on Live's main thread; it never evaluates code.
- Bump `version` in `plugin.json` for every release; it pins installed users until it changes. Do not add `version` to the marketplace entry.
- Keep `SKILL.md` files under 500 lines; put long reference material in sibling files.
- Live 12 UI wording in every user-facing text: the menu is **Settings** (called Preferences in older Live versions; say so on first mention in each file), the tab is **Link, Tempo & MIDI**, the dropdown is **Control Surface**.
- Scripts that Claude Code runs itself (`scripts/run-server.sh`, `scripts/prewarm.sh`) must never print to stdout, and the uv PATH prefix (`~/.local/bin:/opt/homebrew/bin:/usr/local/bin:~/.cargo/bin`) must stay identical across all scripts.
