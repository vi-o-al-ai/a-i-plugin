#!/usr/bin/env bash
# Remove the ClaudeLive Remote Script from Ableton Live's User Library.
#
# Usage:  scripts/uninstall-remote-script.sh [--all]
#   --all   also delete ClaudeLive.bak-* backups left by earlier installs
#
# Environment:
#   ABLETON_USER_LIBRARY  Override the Ableton User Library path
#                         (default: ~/Music/Ableton/User Library).
#
# Leaves ~/.claude-live (history, logs, learning journal) and the plugin
# itself untouched. Uninstall the plugin with:
#   claude plugin uninstall ableton-live@a-i-plugin

set -euo pipefail

remove_backups=0
for arg in "$@"; do
  case "$arg" in
    --all) remove_backups=1 ;;
    -h|--help) sed -n '2,13p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    *) printf 'error: unknown argument %s\n' "$arg" >&2; exit 1 ;;
  esac
done

if [ -n "${ABLETON_USER_LIBRARY:-}" ]; then
  user_library="$ABLETON_USER_LIBRARY"
elif [ "$(uname -s)" = "Darwin" ]; then
  user_library="$HOME/Music/Ableton/User Library"
else
  printf 'error: set ABLETON_USER_LIBRARY to your Ableton User Library path on this OS.\n' >&2
  exit 1
fi
dest_parent="$user_library/Remote Scripts"
dest="$dest_parent/ClaudeLive"

if [ -e "$dest" ]; then
  rm -rf "$dest"
  printf 'Removed %s\n' "$dest"
else
  printf 'Nothing to remove at %s\n' "$dest"
fi

if [ -d "$dest_parent" ]; then
  backups="$(find "$dest_parent" -maxdepth 1 -name 'ClaudeLive.bak-*' | sort)"
  if [ -n "$backups" ]; then
    if [ "$remove_backups" -eq 1 ]; then
      printf '%s\n' "$backups" | while IFS= read -r b; do rm -rf "$b"; printf 'Removed %s\n' "$b"; done
    else
      printf 'Backups from earlier installs were left in place (re-run with --all to delete them):\n%s\n' "$backups"
    fi
  fi
fi

cat <<'NEXT'

If Live is running: Preferences -> Link, Tempo & MIDI -> set the ClaudeLive
Control Surface slot back to "None", then restart Live.
Your action history and learning journal in ~/.claude-live were not touched.
NEXT
