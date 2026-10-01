"""Arrangement tools."""

from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from .common import MUTATE, READ, AppContext, kw, run_tool


def register(mcp: FastMCP, ctx: AppContext) -> None:
    @mcp.tool(title="Get arrangement", annotations=READ)
    async def get_arrangement(include_clips: bool = True) -> dict[str, Any]:
        """Read the arrangement: song length, loop, locators and each track's arrangement clips with start/end times in song beats."""
        params = kw(include_clips=include_clips)
        return await run_tool(ctx, "get_arrangement", "R", params, None, lambda: ctx.client.call("arrangement.get_overview", params))

    @mcp.tool(title="Add clip to arrangement", annotations=MUTATE)
    async def add_clip_to_arrangement(
        track: int,
        slot: int,
        time: float,
        delete_source: bool = False,
        why: str | None = None,
    ) -> dict[str, Any]:
        """Copy a session clip into the arrangement at `time` (song beats from 0); delete_source removes it from the session afterwards."""
        params = kw(track=track, slot=slot, time=time, delete_source=delete_source)
        return await run_tool(
            ctx, "add_clip_to_arrangement", "M", params, why, lambda: ctx.client.call("arrangement.add_clip_from_slot", params)
        )

    @mcp.tool(title="Set locator", annotations=MUTATE)
    async def set_locator(time: float, name: str | None = None, why: str | None = None) -> dict[str, Any]:
        """Create a locator (cue point) at `time` in song beats, or rename the one already there."""
        params = kw(time=time, name=name)
        return await run_tool(ctx, "set_locator", "M", params, why, lambda: ctx.client.call("arrangement.set_locator", params))

    @mcp.tool(title="Delete locator", annotations=MUTATE)
    async def delete_locator(index: int, why: str | None = None) -> dict[str, Any]:
        """Delete the locator with this index (from get_arrangement)."""
        params = kw(index=index)
        return await run_tool(ctx, "delete_locator", "M", params, why, lambda: ctx.client.call("arrangement.delete_locator", params))
