"""ableton_status, ableton_describe_api, get_history."""

from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from ..errors import LiveError
from .common import READ, AppContext, kw, run_tool

EXPECTED_PROTOCOL_VERSION = 1


def _diagnosis(ctx: AppContext, err: LiveError) -> list[str]:
    s = ctx.settings
    port_step = (
        f"Check the port: this server uses {s.host}:{s.port} (CLAUDE_LIVE_PORT); the Remote Script's "
        "config.json must use the same port."
    )
    refused = [
        "Check that Ableton Live 12 is running with a set open.",
        "In Live, open Preferences → Link, Tempo & MIDI → Control Surface and select ClaudeLive "
        "(the ClaudeLive folder must be in Live's Remote Scripts directory; restart Live after installing it).",
        port_step,
        "If Live was just started, wait a few seconds and call ableton_status again.",
    ]
    frozen = [
        "Live is not responding: dismiss any modal dialog (file chooser, plugin window, crash report) in Live.",
        "If Live is loading a set or a large plugin, wait and call ableton_status again.",
        "If Live is frozen, check Live's Log.txt and restart Live.",
        port_step,
    ]
    protocol = [
        "The Remote Script answered with something this server could not parse; check Live's Log.txt for "
        "[ClaudeLive] errors and make sure the Remote Script version matches this server.",
        port_step,
    ]
    if err.name == "TIMEOUT":
        return frozen
    if err.name == "PROTOCOL":
        return protocol
    return refused


def register(mcp: FastMCP, ctx: AppContext) -> None:
    @mcp.tool(title="Ableton status", annotations=READ)
    async def ableton_status() -> dict[str, Any]:
        """Check whether Live is reachable through the ClaudeLive Remote Script. Never fails: returns connected=false plus ordered troubleshooting steps when it is not."""
        s = ctx.settings
        h = ctx.history
        base: dict[str, Any] = {
            "host": s.host,
            "port": s.port,
            "home": str(s.home),
            "history_jsonl": str(h.jsonl_path),
            "history_md": str(h.md_path),
        }
        if s.warnings:
            base["config_warnings"] = list(s.warnings)

        async def do() -> dict[str, Any]:
            try:
                pong = await ctx.client.ping()
            except LiveError as exc:
                return {
                    "connected": False,
                    "error": exc.text,
                    "error_code": exc.name,
                    "diagnosis": _diagnosis(ctx, exc),
                    **base,
                }
            out: dict[str, Any] = {
                "connected": True,
                "script_version": pong.get("script_version"),
                "protocol_version": pong.get("protocol_version"),
                "live_version": pong.get("live_version"),
                "python_version": pong.get("python_version"),
                "round_trip_ms": pong.get("round_trip_ms"),
                **base,
            }
            if pong.get("protocol_version") != EXPECTED_PROTOCOL_VERSION:
                out["warning"] = (
                    f"Protocol version mismatch: the Remote Script speaks version {pong.get('protocol_version')!r}, "
                    f"this server expects {EXPECTED_PROTOCOL_VERSION}. Update whichever side is older; some tools may fail."
                )
            return out

        return await run_tool(ctx, "ableton_status", "R", {}, None, do)

    @mcp.tool(title="Describe Live API", annotations=READ)
    async def ableton_describe_api(path: str | None = None) -> dict[str, Any]:
        """Dump the real Live API (classes and docstrings) from inside the user's Live to a Markdown file for debugging. Returns the file path and size."""
        params = kw(path=path)
        return await run_tool(ctx, "ableton_describe_api", "R", params, None, lambda: ctx.client.call("sys.describe_api", params))

    @mcp.tool(title="Get action history", annotations=READ)
    async def get_history(limit: int = 50, include_reads: bool = False) -> dict[str, Any]:
        """Return this session's recorded actions (most recent last) with their `why` notes, plus the history file paths. Reads are included only with include_reads=true."""
        return ctx.history.get(limit=limit, include_reads=include_reads)
