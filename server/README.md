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

From another directory (as the plugin's `.mcp.json` does):

```sh
uv run --directory <repo>/server --locked ableton-live-mcp
```

## Environment variables

| Var | Default | Purpose |
|---|---|---|
| `CLAUDE_LIVE_HOST` | `127.0.0.1` | Remote Script host |
| `CLAUDE_LIVE_PORT` | `9892` | Remote Script port (must match the script's `config.json`) |
| `CLAUDE_LIVE_HOME` | `~/.claude-live` | Action history (`history/`) and server log (`logs/server.log`) |
| `CLAUDE_LIVE_LOG_LEVEL` | `INFO` | Server log level |

The home directory lives outside the plugin install so history survives plugin updates
and uninstalls. Every session writes `history/<YYYY-MM-DD>_<HHMMSS>_<pid>.jsonl` (all tool
calls, including reads) and a sibling `.md` (one line per mutating/UI action).

## Tests

```sh
uv run pytest -q
```

The tests run a fake Remote Script on an ephemeral TCP port and drive the server through
the SDK's in-memory client session; Live is not required.
