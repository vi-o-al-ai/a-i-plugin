---
name: setup
description: Install the ClaudeLive Remote Script into Ableton Live, pre-build the MCP server environment, and verify that Claude can talk to Live.
disable-model-invocation: true
allowed-tools:
  - Read
  - Bash(command -v uv)
  - mcp__plugin_ableton-live_live__ableton_status
---

# Set up the Ableton Live plugin

You are walking the user through a one-time install. The plugin files are at `${CLAUDE_PLUGIN_ROOT}` and the plugin's persistent data directory is `${CLAUDE_PLUGIN_DATA}` (Claude Code substitutes both paths when this skill loads; if either still reads literally as `${...}`, the plugin root is two directories above this `SKILL.md`, since skills live at `<plugin root>/skills/<name>/SKILL.md`, and the data directory may be left unset).

Work through the steps in order. Stop and wait for the user wherever a step says so. Keep every message short; the user wants to make music, not read logs.

## 1. Say what is about to happen

In a few lines:
- The plugin has two halves: a **Remote Script** called `ClaudeLive` that runs inside Ableton Live and listens on `127.0.0.1:9892`, and an **MCP server** that Claude Code launches with `uv` and that talks to the script.
- This setup copies the Remote Script into Live's User Library, pre-builds the server's Python environment, and then checks the connection.
- Nothing leaves the machine, and the script never saves the user's Live Set.

## 2. Check for `uv`

Run `command -v uv`. If it prints nothing, give the install command and say that `uv` has to be on the PATH of the shell that starts Claude Code (the installer puts it in `~/.local/bin`), so they should open a new terminal and restart Claude Code afterwards:

```
curl -LsSf https://astral.sh/uv/install.sh | sh
```

Without `uv` the MCP server cannot start, but the Remote Script can still be installed, so continue with step 3 either way and remind them to re-run `/ableton-live:setup` once `uv` is installed.

## 3. Install the Remote Script (ask before running)

Show the user the exact command you are about to run and summarise what it does, then ask for confirmation. Only run it after they say yes.

```
CLAUDE_PLUGIN_DATA="${CLAUDE_PLUGIN_DATA}" bash "${CLAUDE_PLUGIN_ROOT}/scripts/install-remote-script.sh"
```

What the script does:
1. Copies `remote-script/ClaudeLive` from the plugin to `~/Music/Ableton/User Library/Remote Scripts/ClaudeLive`, creating the folders. If an older copy is there it is first renamed to `ClaudeLive.bak-<timestamp>`. `__pycache__` folders are stripped.
2. Verifies that `__init__.py` landed in the destination.
3. If `uv` is installed, runs `uv sync --frozen` for the server with its virtualenv inside the plugin data directory. The first run can take a minute while uv downloads Python and the dependencies.
4. Prints the next steps.

Show the user the script's output. If it fails, read the error and act on it (for example a missing `remote-script/ClaudeLive` folder means the plugin install is incomplete; `claude plugin update ableton-live@a-i-plugin` or reinstalling fixes it) and point them to the Troubleshooting section of `${CLAUDE_PLUGIN_ROOT}/README.md`.

## 4. Enable the control surface in Live (the user does this)

Ask the user to:
1. **Restart Ableton Live** (or start it) so it discovers the new Remote Script.
2. Open **Preferences → Link, Tempo & MIDI**.
3. In a free **Control Surface** slot choose **ClaudeLive**. Leave **Input** and **Output** set to **None**.
4. Open or create any Live Set.

Wait for them to say it is done before continuing.

## 5. Verify the connection

Call `ableton_status` and interpret the result:

- **`connected: true`** → report the Live version, script version and round-trip time, and where the action history is written (the history paths in the result). Suggest `/ableton-live:status` to see the set, `/ableton-live:lesson` to start learning, or simply asking Claude to do something in the set.
- **`connected: false`** → relay the `diagnosis` and the most likely cause, in order:
  - *Connection refused*: Live is not running, or ClaudeLive is not selected as a Control Surface, or the port in `remote-script/ClaudeLive/config.json` does not match `CLAUDE_LIVE_PORT`.
  - *ClaudeLive does not appear in the Control Surface list*: the folder is in the wrong place or `__init__.py` is missing. Re-run step 3 and restart Live.
  - *Timeout*: Live is showing a modal dialog, loading a set, or frozen.
  - For details, point to Live's log at `~/Library/Preferences/Ableton/Live 12.x.x/Log.txt` (replace `12.x.x` with the installed version; search the file for `ClaudeLive`) and to the Troubleshooting section of `${CLAUDE_PLUGIN_ROOT}/README.md`.
- **The `ableton_status` tool does not exist at all** → the MCP server did not start. Ask the user to run `/mcp` and reconnect `plugin:ableton-live:live` (the first launch can be slow while uv builds the environment). If it still fails: is `uv` installed and on PATH? Otherwise start Claude Code with `claude --debug` and read the server's stderr in `~/.claude/debug/<session-id>.txt`.
