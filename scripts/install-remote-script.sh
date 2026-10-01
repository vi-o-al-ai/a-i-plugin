#!/usr/bin/env bash
# Install the ClaudeLive Remote Script into Ableton Live's User Library and
# pre-build the MCP server's Python environment.  macOS.
#
# Usage:  scripts/install-remote-script.sh
#
# Environment:
#   ABLETON_USER_LIBRARY  Override the Ableton User Library path
#                         (default: ~/Music/Ableton/User Library).
#   CLAUDE_PLUGIN_DATA    The plugin's persistent data directory, where the
#                         server virtualenv is built. Claude Code provides it
#                         to hooks and skills; the default below matches a
#                         marketplace install of ableton-live@a-i-plugin.
#
# Idempotent: an existing ClaudeLive install is moved to
# ClaudeLive.bak-<timestamp> before the new copy is written.

set -euo pipefail

plugin_root="$(cd "$(dirname "$0")/.." && pwd)"
src="$plugin_root/remote-script/ClaudeLive"

info() { printf '%s\n' "$*"; }
warn() { printf 'warning: %s\n' "$*" >&2; }
die()  { printf 'error: %s\n' "$*" >&2; exit 1; }

# --- locate the User Library --------------------------------------------------
if [ -n "${ABLETON_USER_LIBRARY:-}" ]; then
  user_library="$ABLETON_USER_LIBRARY"
elif [ "$(uname -s)" = "Darwin" ]; then
  user_library="$HOME/Music/Ableton/User Library"
else
  die "This installer supports macOS. On another OS, set ABLETON_USER_LIBRARY to your Ableton User Library path and re-run."
fi
dest_parent="$user_library/Remote Scripts"
dest="$dest_parent/ClaudeLive"

# --- sanity checks ------------------------------------------------------------
[ -d "$src" ] || die "Remote Script source not found at $src. Is the plugin checkout complete?"
[ -f "$src/__init__.py" ] || die "$src has no __init__.py; refusing to install a broken Remote Script."

info "Plugin root:   $plugin_root"
info "Installing to: $dest"

# --- back up any existing install, then copy ----------------------------------
mkdir -p "$dest_parent"
backup=""
if [ -e "$dest" ]; then
  backup="$dest_parent/ClaudeLive.bak-$(date +%Y%m%d-%H%M%S)"
  mv "$dest" "$backup"
  info "Existing install moved to: $backup"
fi

cp -R "$src" "$dest"
# Strip caches and OS litter; Live compiles its own bytecode.
find "$dest" -type d -name '__pycache__' -prune -exec rm -rf {} +
find "$dest" -type f \( -name '*.pyc' -o -name '.DS_Store' \) -delete

[ -f "$dest/__init__.py" ] || die "Copy failed: $dest/__init__.py is missing."
info "Remote Script installed ($(find "$dest" -type f | wc -l | tr -d ' ') files)."

if [ -n "$backup" ] && [ -f "$backup/config.json" ] && ! cmp -s "$backup/config.json" "$dest/config.json"; then
  warn "Your previous config.json differs from the new one and was kept at $backup/config.json. If you had changed the port, re-apply it in $dest/config.json (and set CLAUDE_LIVE_PORT to match)."
fi

# --- pre-build the MCP server environment -------------------------------------
plugins_home="${CLAUDE_CODE_PLUGIN_CACHE_DIR:-$HOME/.claude/plugins}"
data_dir="${CLAUDE_PLUGIN_DATA:-$plugins_home/data/ableton-live-a-i-plugin}"
export UV_PROJECT_ENVIRONMENT="$data_dir/venv"

info ""
if ! command -v uv >/dev/null 2>&1; then
  info "uv is not installed, so the MCP server environment was not pre-built."
  info "Install it, open a new terminal, then restart Claude Code:"
  info "    curl -LsSf https://astral.sh/uv/install.sh | sh"
elif [ ! -f "$plugin_root/server/uv.lock" ]; then
  warn "$plugin_root/server/uv.lock not found; skipping the environment pre-build."
else
  info "Pre-building the MCP server environment with uv (the first run can take a minute)..."
  info "  venv: $UV_PROJECT_ENVIRONMENT"
  mkdir -p "$data_dir"
  if uv sync --frozen --directory "$plugin_root/server"; then
    info "Server environment ready."
  else
    warn "uv sync failed. Claude Code retries when it launches the server; see Troubleshooting in the README."
  fi
fi

cat <<'NEXT'

Next steps
  1. Restart Ableton Live (or start it) so it discovers the new Remote Script.
  2. Preferences -> Link, Tempo & MIDI -> Control Surface: choose "ClaudeLive".
     Leave Input and Output set to "None".
  3. Open any Live Set, then in Claude Code run:  /ableton-live:status
NEXT
