<!-- Contributor notes for working ON this repository. Claude Code does not load a plugin's root CLAUDE.md for people who INSTALL the plugin (and `claude plugin validate` warns that it is here); user-facing instructions belong in skills/. -->

# a-i-plugin — contributor notes

This repo is a Claude Code plugin (`ableton-live`) and its own one-entry marketplace (`a-i-plugin`). The plugin root is the repo root.

## Layout

| Path | What |
| :- | :- |
| `.claude-plugin/plugin.json`, `.claude-plugin/marketplace.json` | Plugin manifest and self-hosting marketplace |
| `.mcp.json` | Launches the MCP server: `uv run --frozen --directory ${CLAUDE_PLUGIN_ROOT}/server ableton-live-mcp` |
| `hooks/hooks.json`, `scripts/prewarm.sh` | SessionStart hook that pre-builds the server venv in `${CLAUDE_PLUGIN_DATA}/venv` |
| `remote-script/ClaudeLive/` | The Remote Script that runs inside Live 12 (embedded Python 3.11, **stdlib only**) |
| `server/` | The MCP server, a uv project; console script `ableton-live-mcp`; commit `uv.lock` |
| `skills/<name>/SKILL.md` | Knowledge skills (`ableton-live`, `live-devices`, `midi-writing`, `production-mentor`, `curriculum`, `song-study`) and slash commands (`setup`, `status`, `history`, `explain`, `lesson`, `review`, `quiz`, `study`, all `disable-model-invocation: true`) |
| `scripts/install-remote-script.sh`, `scripts/uninstall-remote-script.sh` | macOS installers for the Remote Script |
| `tests/` | Tests for the Remote Script and the protocol (plain pytest, no third-party deps) |
| `docs/PROTOCOL.md`, `docs/TOOLS.md` | **The contracts** (see below) |
| `docs/research/` | Research notes (plugin format, MCP SDK) |

## Source of truth

`docs/PROTOCOL.md` (wire protocol between the Remote Script and the server) and `docs/TOOLS.md` (the MCP tool surface) are the contracts. The Remote Script, the server, the tests, the skills and the README are all written from them. If code and a contract disagree, fix one of them in the same change; never let them drift. Tool names in skills are the plugin-qualified form `mcp__plugin_ableton-live_live__<tool>`.

## Running tests

```bash
uv run --directory server pytest   # MCP server tests (uv project in server/)
python3 -m pytest tests            # Remote Script / protocol tests (stdlib + pytest)
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
- The Remote Script binds `127.0.0.1` only and executes a fixed set of JSON-RPC methods on Live's main thread; it never evaluates code.
- Bump `version` in `plugin.json` for every release; it pins installed users until it changes. Do not add `version` to the marketplace entry.
- Keep `SKILL.md` files under 500 lines; put long reference material in sibling files.
