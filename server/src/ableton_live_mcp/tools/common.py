"""Shared helpers for tool modules: app context, annotations, param building, recording."""

from __future__ import annotations

import logging
import time
from collections.abc import Awaitable, Callable
from typing import Any, Literal

from mcp.server.fastmcp.exceptions import ToolError
from mcp.types import ToolAnnotations

from ..client import LiveClient
from ..config import Settings
from ..errors import LiveError, confirm_required, format_error, invalid_params
from ..history import ActionHistory

log = logging.getLogger("ableton_live_mcp.tools")

TrackType = Literal["track", "return", "master"] | None

# TOOLS.md: reads readOnlyHint=true; deletes destructiveHint=true; everything else
# destructiveHint=false, idempotentHint=false. openWorldHint is always false (localhost only).
READ = ToolAnnotations(readOnlyHint=True, destructiveHint=False, idempotentHint=True, openWorldHint=False)
MUTATE = ToolAnnotations(readOnlyHint=False, destructiveHint=False, idempotentHint=False, openWorldHint=False)
DESTROY = ToolAnnotations(readOnlyHint=False, destructiveHint=True, idempotentHint=False, openWorldHint=False)
UI = ToolAnnotations(readOnlyHint=False, destructiveHint=False, idempotentHint=False, openWorldHint=False)


class AppContext:
    """What every tool needs: settings, the Live client and the action history.

    ``client`` and ``history`` are created by the server lifespan (or on first access);
    both are lazy internally, so construction has no side effects.
    """

    def __init__(self, settings: Settings, client: LiveClient | None = None, history: ActionHistory | None = None):
        self.settings = settings
        self._client = client
        self._history = history

    @property
    def client(self) -> LiveClient:
        if self._client is None:
            self._client = LiveClient(self.settings.host, self.settings.port)
        return self._client

    @property
    def history(self) -> ActionHistory:
        if self._history is None:
            self._history = ActionHistory(self.settings.history_dir)
        return self._history

    def start(self) -> None:
        """Create the client and history (called from the server lifespan)."""
        _ = self.client, self.history

    async def aclose(self) -> None:
        if self._client is not None:
            await self._client.close()


def kw(**kwargs: Any) -> dict[str, Any]:
    """Keyword arguments minus ``None`` values; the basis of every protocol params object."""
    return {k: v for k, v in kwargs.items() if v is not None}


def rename(params: dict[str, Any], **mapping: str) -> dict[str, Any]:
    """Copy ``params`` renaming keys (``device_path="path"``)."""
    return {mapping.get(k, k): v for k, v in params.items()}


def clip_address(track: int, slot: int | None, arrangement_index: int | None) -> dict[str, Any]:
    """PROTOCOL.md section 5: exactly one of ``slot`` / ``arrangement_index``."""
    if (slot is None) == (arrangement_index is None):
        raise invalid_params(
            "A clip is addressed by track plus exactly one of slot (session clip) or arrangement_index (arrangement clip)",
            {"track": track, "slot": slot, "arrangement_index": arrangement_index},
        )
    return kw(track=track, slot=slot, arrangement_index=arrangement_index)


def require_confirm(confirm: bool, tool: str, what: str) -> None:
    """Refuse destructive calls without ``confirm=True`` before touching Live."""
    if confirm is not True:
        raise confirm_required(tool, what)


def require_list_of_dicts(items: Any, name: str, required_keys: tuple[str, ...] = (), allow_empty: bool = False) -> None:
    if not isinstance(items, list):
        raise invalid_params(f"{name} must be a list")
    if not items and not allow_empty:
        raise invalid_params(f"{name} must not be empty")
    for i, item in enumerate(items):
        if not isinstance(item, dict):
            raise invalid_params(f"{name}[{i}] must be an object", {"index": i})
        missing = [k for k in required_keys if k not in item]
        if missing:
            raise invalid_params(f"{name}[{i}] is missing {', '.join(missing)}", {"index": i, "missing": missing})


async def run_tool(
    ctx: AppContext,
    tool: str,
    flags: str,
    params: dict[str, Any],
    why: str | None,
    fn: Callable[[], Awaitable[dict[str, Any]]],
) -> dict[str, Any]:
    """Run ``fn`` and record the outcome; ``LiveError`` becomes a ``ToolError``."""
    started = time.perf_counter()
    try:
        result = await fn()
    except LiveError as exc:
        ctx.history.record(tool, flags, params, why, None, exc.text, (time.perf_counter() - started) * 1000)
        raise exc.to_tool_error() from None
    except ToolError as exc:
        ctx.history.record(tool, flags, params, why, None, str(exc), (time.perf_counter() - started) * 1000)
        raise
    except Exception as exc:  # noqa: BLE001 - surface bugs as structured tool errors
        log.exception("tool %s failed", tool)
        text = format_error("INTERNAL_ERROR", f"{type(exc).__name__}: {exc}")
        ctx.history.record(tool, flags, params, why, None, text, (time.perf_counter() - started) * 1000)
        raise ToolError(text) from exc
    ctx.history.record(tool, flags, params, why, result, None, (time.perf_counter() - started) * 1000)
    return result
