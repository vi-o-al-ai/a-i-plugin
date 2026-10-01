#!/usr/bin/env bash
# SessionStart hook for the ableton-live plugin.
#
# Builds (or refreshes) the MCP server's virtualenv in the plugin's data
# directory so that the first `live` tool call of a session does not wait
# for uv to resolve and install dependencies.
#
# Rules for this script:
#   * never print to stdout  -- a SessionStart hook's stdout is added to
#                               Claude's context
#   * never exit non-zero    -- a missing uv or a failed sync must not break
#                               session start; `uv run --frozen` in .mcp.json
#                               retries lazily when the server is launched
#   * never write inside CLAUDE_PLUGIN_ROOT -- that is a versioned cache dir
#
# Claude Code exports CLAUDE_PLUGIN_ROOT and CLAUDE_PLUGIN_DATA to hook
# processes. The fallbacks below only matter when the script is run by hand.

plugin_root="${CLAUDE_PLUGIN_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"
plugins_home="${CLAUDE_CODE_PLUGIN_CACHE_DIR:-$HOME/.claude/plugins}"
data_dir="${CLAUDE_PLUGIN_DATA:-$plugins_home/data/ableton-live-a-i-plugin}"

export UV_PROJECT_ENVIRONMENT="$data_dir/venv"

if command -v uv >/dev/null 2>&1 && [ -f "$plugin_root/server/uv.lock" ]; then
  mkdir -p "$data_dir" >/dev/null 2>&1 || true
  uv sync --frozen --directory "$plugin_root/server" >/dev/null 2>&1 || true
fi

exit 0
