#!/usr/bin/env bash
# SessionStart hook for the ableton-live plugin (hooks/hooks.json).
#
# Builds the MCP server's virtualenv in the plugin's data directory so that
# the first `live` tool call of a session does not wait for uv to resolve and
# install dependencies. Once the venv exists the script returns in a few
# milliseconds without running uv at all.
#
# Rules for this script:
#   * never print to stdout  -- a SessionStart hook's stdout is added to
#                               Claude's context
#   * never exit non-zero    -- a missing uv or a failed sync must not break
#                               session start; `uv run --frozen` in
#                               scripts/run-server.sh does the same work when
#                               the server is launched (and re-syncs after a
#                               plugin update, so skipping here is safe)
#   * never write inside CLAUDE_PLUGIN_ROOT -- that is a versioned cache dir
#
# Claude Code exports CLAUDE_PLUGIN_ROOT and CLAUDE_PLUGIN_DATA to hook
# processes. The fallbacks below only matter when the script is run by hand.
#
# Everything runs in a subshell with stdout and stderr discarded, so a failed
# `${HOME:?}` guard, a missing uv or a failed sync all end with exit 0 here.

(
  : "${HOME:?HOME is not set}"

  # Same PATH prefix as scripts/run-server.sh: uv's usual install locations,
  # which are missing from the PATH Claude Code gets when launched from a GUI.
  export PATH="$HOME/.local/bin:/opt/homebrew/bin:/usr/local/bin:$HOME/.cargo/bin:$PATH"

  plugin_root="${CLAUDE_PLUGIN_ROOT:-$(cd "$(dirname "$0")/.." && pwd)}"
  plugins_home="${CLAUDE_CODE_PLUGIN_CACHE_DIR:-$HOME/.claude/plugins}"
  data_dir="${CLAUDE_PLUGIN_DATA:-$plugins_home/data/ableton-live-a-i-plugin}"
  export UV_PROJECT_ENVIRONMENT="$data_dir/venv"

  # Warm venv: nothing to do.
  [ -x "$UV_PROJECT_ENVIRONMENT/bin/ableton-live-mcp" ] && exit 0

  command -v uv >/dev/null 2>&1 || exit 0
  [ -f "$plugin_root/server/uv.lock" ] || exit 0

  mkdir -p "$data_dir"
  uv sync --frozen --no-dev --directory "$plugin_root/server"
) >/dev/null 2>&1 || true

exit 0
