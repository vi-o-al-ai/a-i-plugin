"""Error mapping: protocol error codes -> named tool errors with actionable hints.

Every error surfaced to Claude reads ``"<NAME>: <message>. <hint>"`` (TOOLS.md), optionally
followed by the protocol ``data`` as compact JSON.
"""

from __future__ import annotations

import json
from typing import Any

from mcp.server.fastmcp.exceptions import ToolError

# JSON-RPC standard codes
PARSE_ERROR = -32700
INVALID_REQUEST = -32600
METHOD_NOT_FOUND = -32601
INVALID_PARAMS = -32602
INTERNAL_ERROR = -32603
# Application codes (PROTOCOL.md section 3)
NOT_FOUND = -32000
INVALID_STATE = -32001
CONFIRM_REQUIRED = -32002
UNSUPPORTED = -32003
LIVE_ERROR = -32004
TOO_LARGE = -32005
SCRIPT_TIMEOUT = -32006

# Local (client-side) codes are strings.
CONNECTION = "CONNECTION"
TIMEOUT = "TIMEOUT"
PROTOCOL = "PROTOCOL"

CODE_NAMES: dict[int, str] = {
    PARSE_ERROR: "PARSE_ERROR",
    INVALID_REQUEST: "INVALID_REQUEST",
    METHOD_NOT_FOUND: "METHOD_NOT_FOUND",
    INVALID_PARAMS: "INVALID_PARAMS",
    INTERNAL_ERROR: "INTERNAL_ERROR",
    NOT_FOUND: "NOT_FOUND",
    INVALID_STATE: "INVALID_STATE",
    CONFIRM_REQUIRED: "CONFIRM_REQUIRED",
    UNSUPPORTED: "UNSUPPORTED",
    LIVE_ERROR: "LIVE_ERROR",
    TOO_LARGE: "TOO_LARGE",
    SCRIPT_TIMEOUT: "TIMEOUT",
}

# PROTOCOL.md section 8 wording.
CONNECTION_HINT = (
    "Live is not running, or the ClaudeLive control surface is not selected "
    "(Preferences → Link, Tempo & MIDI → Control Surface), or the port does not match "
    "(CLAUDE_LIVE_PORT on the server vs config.json in the Remote Script)."
)
TIMEOUT_HINT = "Live is not responding. It may be showing a modal dialog, loading a set, or frozen."

HINTS: dict[str, str] = {
    "NOT_FOUND": "Call get_session or get_track to refresh indices.",
    "INVALID_STATE": "Check the object's state with get_clip/get_track.",
    "CONFIRM_REQUIRED": "Ask the user, then call again with confirm=True.",
    "CONNECTION": CONNECTION_HINT,
    "TIMEOUT": TIMEOUT_HINT,
    "UNSUPPORTED": "The installed Live version lacks this API; see the data for what is needed.",
    "TOO_LARGE": "Split the request into smaller batches.",
    "METHOD_NOT_FOUND": "The Remote Script may be older than this server; compare versions with ableton_status.",
    "INVALID_PARAMS": "Check the parameter names, types and ranges in the tool description.",
    "PROTOCOL": "The Remote Script sent an unexpected response; check Live's Log.txt.",
    "INTERNAL_ERROR": "This is a bug in the ClaudeLive Remote Script; check Live's Log.txt.",
}

# The script's own -32006 is a traversal budget, not a frozen Live; give it a different hint.
_SCRIPT_TIMEOUT_HINT = "Narrow the search (fewer categories, a smaller max_nodes) and try again."


def code_name(code: int | str) -> str:
    """Name for a protocol code (``-32000`` -> ``NOT_FOUND``) or a local string code."""
    if isinstance(code, str):
        return code
    return CODE_NAMES.get(code, f"ERROR_{code}")


def hint_for(code: int | str) -> str | None:
    if code == SCRIPT_TIMEOUT:
        return _SCRIPT_TIMEOUT_HINT
    return HINTS.get(code_name(code))


def format_error(code: int | str, message: str, data: Any = None) -> str:
    """Render ``"<NAME>: <message>. <hint> Data: {...}"``."""
    name = code_name(code)
    msg = (message or "").strip().rstrip(".") or "unknown error"
    parts = [f"{name}: {msg}."]
    if name == "LIVE_ERROR" and isinstance(data, dict) and data.get("detail"):
        detail = str(data["detail"]).strip().rstrip(".")
        parts.append(f"Live reported: {detail}.")
    hint = hint_for(code)
    if hint:
        parts.append(hint)
    if data not in (None, {}, [], ""):
        try:
            parts.append("Data: " + json.dumps(data, separators=(",", ":"), ensure_ascii=False, default=str))
        except (TypeError, ValueError):  # pragma: no cover - defensive
            parts.append(f"Data: {data!r}")
    return " ".join(parts)


class LiveError(Exception):
    """A protocol error from the Remote Script, or a local connection/timeout/protocol failure."""

    def __init__(self, code: int | str, message: str, data: Any = None):
        self.code = code
        self.message = message
        self.data = data
        super().__init__(self.text)

    @property
    def name(self) -> str:
        return code_name(self.code)

    @property
    def text(self) -> str:
        return format_error(self.code, self.message, self.data)

    def to_tool_error(self) -> ToolError:
        return ToolError(self.text)

    def __repr__(self) -> str:  # pragma: no cover - debugging aid
        return f"LiveError({self.code!r}, {self.message!r}, {self.data!r})"


def to_tool_error(err: LiveError) -> ToolError:
    """Convert a ``LiveError`` into the ``ToolError`` Claude sees."""
    return err.to_tool_error()


# -- helpers for errors raised locally, before any network call ------------------------


def tool_error(code: int | str, message: str, data: Any = None) -> ToolError:
    return ToolError(format_error(code, message, data))


def invalid_params(message: str, data: Any = None) -> ToolError:
    return tool_error(INVALID_PARAMS, message, data)


def not_found(message: str, data: Any = None) -> ToolError:
    return tool_error(NOT_FOUND, message, data)


def too_large(message: str, data: Any = None) -> ToolError:
    return tool_error(TOO_LARGE, message, data)


def confirm_required(tool: str, what: str) -> ToolError:
    """``CONFIRM_REQUIRED: <tool> would delete <what>. Ask the user, then call again with confirm=True.``"""
    return tool_error(CONFIRM_REQUIRED, f"{tool} would delete {what}")
