#!/usr/bin/env bash
# Launch the ableton-live MCP server. This is the `command` in .mcp.json:
#
#     bash "${CLAUDE_PLUGIN_ROOT}/scripts/run-server.sh"
#
# Why a wrapper instead of a bare `uv` command: on macOS, a Claude Code
# started from the Dock, Spotlight or an IDE inherits the launchd PATH
# (/usr/bin:/bin:/usr/sbin:/sbin), which does not contain the directories uv
# is normally installed into. Prepending them here makes the server start no
# matter how Claude Code was launched. Everything else in the environment is
# passed through untouched (.mcp.json sets UV_PROJECT_ENVIRONMENT so that the
# venv is built in the plugin data directory, never under the plugin root).
#
# stdout is the MCP transport: never print to it. Diagnostics go to stderr,
# which Claude Code records in its debug log (`claude --debug`, then
# ~/.claude/debug/<session-id>.txt).

set -euo pipefail

plugin_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

export PATH="${HOME:-}/.local/bin:/opt/homebrew/bin:/usr/local/bin:${HOME:-}/.cargo/bin:$PATH"

if ! command -v uv >/dev/null 2>&1; then
  printf '%s\n' "ableton-live: the MCP server cannot start because 'uv' was not found. Looked on PATH and in ~/.local/bin, /opt/homebrew/bin, /usr/local/bin and ~/.cargo/bin. Install uv with:  curl -LsSf https://astral.sh/uv/install.sh | sh  (or 'brew install uv'), then quit and restart Claude Code so the new installation is picked up, and run /ableton-live:setup to finish the install. If uv is installed somewhere else, add that directory to the PATH of the shell that starts Claude Code." >&2
  exit 1
fi

exec uv run --frozen --no-dev --directory "$plugin_root/server" ableton-live-mcp
