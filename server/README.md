# ableton-live-mcp

The MCP server half of the ClaudeLive plugin. It speaks MCP over stdio to Claude Code and
newline-delimited JSON-RPC 2.0 over TCP to the ClaudeLive Remote Script running inside
Ableton Live 12 (see `docs/PROTOCOL.md`). It exposes the 55 tools listed in `docs/TOOLS.md`.

## Run

```sh
cd server
uv sync                      # once; creates .venv and installs the locked dependencies
uv run ableton-live-mcp      # stdio MCP server; logs go to stderr, never stdout
```

From another directory, the way the plugin's `scripts/run-server.sh` (called from `.mcp.json`)
launches it. `--frozen` installs exactly what `uv.lock` pins without re-resolving; `--no-dev`
leaves pytest out of the user's venv:

```sh
uv run --frozen --no-dev --directory <repo>/server ableton-live-mcp
```

## Environment variables

| Var | Default | Purpose |
|---|---|---|
| `CLAUDE_LIVE_HOST` | `127.0.0.1` | Remote Script host. Only loopback is accepted (`127.0.0.1`, `::1`, `localhost`, …); anything else is ignored with a warning and the default is used. |
| `CLAUDE_LIVE_PORT` | `9892` | Remote Script port (must match the script's `config.json`); 1–65535 |
| `CLAUDE_LIVE_HOME` | `~/.claude-live` | Action history (`history/`), server log (`logs/server.log`) and the API dumps the Remote Script writes (`api/`). Must be an absolute path (`~` is expanded); a relative value is ignored with a warning. |
| `CLAUDE_LIVE_LOG_LEVEL` | `INFO` | Server log level (`DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`) |

Invalid values never stop the server: each one is replaced by its default, logged at startup
and reported by the `ableton_status` tool as `config_warnings`.

The home directory lives outside the plugin install so history survives plugin updates
and uninstalls; it is created with mode 0700. Every session writes
`history/<YYYY-MM-DD>_<HHMMSS>_<pid>.jsonl` (all tool calls, including reads) and a sibling
`.md` (one line per mutating/UI action).

## Tests

```sh
uv run --locked pytest -q     # --locked fails if uv.lock has drifted from pyproject.toml (CI runs it this way)
```

The tests run a fake Remote Script on an ephemeral TCP port and drive the server through
the SDK's in-memory client session; Live is not required.
