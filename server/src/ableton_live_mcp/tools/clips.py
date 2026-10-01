"""Clip tools."""

from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from ..errors import invalid_params
from .common import DESTROY, MUTATE, READ, AppContext, clip_address, kw, require_confirm, run_tool


def register(mcp: FastMCP, ctx: AppContext) -> None:
    @mcp.tool(title="Create clip", annotations=MUTATE)
    async def create_clip(
        track: int,
        slot: int,
        length: float = 4.0,
        name: str | None = None,
        why: str | None = None,
    ) -> dict[str, Any]:
        """Create an empty MIDI clip of `length` beats in a session slot (fails if the slot is occupied or the track is audio)."""
        params = kw(track=track, slot=slot, length=length, name=name)

        async def do() -> dict[str, Any]:
            if length <= 0:
                raise invalid_params("length must be greater than 0 beats", {"length": length})
            return await ctx.client.call("clip.create", params)

        return await run_tool(ctx, "create_clip", "M", params, why, do)

    @mcp.tool(title="Get clip", annotations=READ)
    async def get_clip(track: int, slot: int | None = None, arrangement_index: int | None = None) -> dict[str, Any]:
        """Read one clip's name, color, loop/markers, play state and note count. Address it with slot (session) or arrangement_index."""
        params = kw(track=track, slot=slot, arrangement_index=arrangement_index)

        async def do() -> dict[str, Any]:
            return await ctx.client.call("clip.get", clip_address(track, slot, arrangement_index))

        return await run_tool(ctx, "get_clip", "R", params, None, do)

    @mcp.tool(title="Set clip", annotations=MUTATE)
    async def set_clip(
        track: int,
        slot: int | None = None,
        arrangement_index: int | None = None,
        name: str | None = None,
        color_index: int | None = None,
        loop_start: float | None = None,
        loop_end: float | None = None,
        looping: bool | None = None,
        start_marker: float | None = None,
        end_marker: float | None = None,
        launch_quantization: str | None = None,
        why: str | None = None,
    ) -> dict[str, Any]:
        """Change a clip's name, color_index, loop range, looping flag, start/end markers (beats from clip start) or launch quantization (a name such as "q_global", "q_bar", "q_quarter", "q_sixteenth")."""
        fields = kw(
            name=name,
            color_index=color_index,
            loop_start=loop_start,
            loop_end=loop_end,
            looping=looping,
            start_marker=start_marker,
            end_marker=end_marker,
            launch_quantization=launch_quantization,
        )
        params = {**kw(track=track, slot=slot, arrangement_index=arrangement_index), **fields}

        async def do() -> dict[str, Any]:
            address = clip_address(track, slot, arrangement_index)
            if not fields:
                raise invalid_params("set_clip needs at least one field to change")
            return await ctx.client.call("clip.set", {**address, **fields})

        return await run_tool(ctx, "set_clip", "M", params, why, do)

    @mcp.tool(title="Fire clip", annotations=MUTATE)
    async def fire_clip(track: int, slot: int, why: str | None = None) -> dict[str, Any]:
        """Launch the clip in a session slot (firing an empty slot stops the track's clip)."""
        params = kw(track=track, slot=slot)
        return await run_tool(ctx, "fire_clip", "M", params, why, lambda: ctx.client.call("clip.fire", params))

    @mcp.tool(title="Stop clip", annotations=MUTATE)
    async def stop_clip(track: int, slot: int | None = None, why: str | None = None) -> dict[str, Any]:
        """Stop the clip in a slot, or every clip on the track when slot is omitted."""
        params = kw(track=track, slot=slot)
        return await run_tool(ctx, "stop_clip", "M", params, why, lambda: ctx.client.call("clip.stop", params))

    @mcp.tool(title="Duplicate clip", annotations=MUTATE)
    async def duplicate_clip(
        track: int,
        slot: int,
        target_slot: int,
        target_track: int | None = None,
        why: str | None = None,
    ) -> dict[str, Any]:
        """Copy a session clip to target_slot (on target_track, default the same track). The target slot must be empty."""
        params = kw(track=track, slot=slot, target_slot=target_slot, target_track=target_track)
        return await run_tool(ctx, "duplicate_clip", "M", params, why, lambda: ctx.client.call("clip.duplicate", params))

    @mcp.tool(title="Duplicate clip loop", annotations=MUTATE)
    async def duplicate_clip_loop(track: int, slot: int, why: str | None = None) -> dict[str, Any]:
        """Double a MIDI clip's loop: the loop content is repeated and the clip length doubles."""
        params = kw(track=track, slot=slot)
        return await run_tool(ctx, "duplicate_clip_loop", "M", params, why, lambda: ctx.client.call("clip.duplicate_loop", params))

    @mcp.tool(title="Delete clip", annotations=DESTROY)
    async def delete_clip(
        track: int,
        slot: int | None = None,
        arrangement_index: int | None = None,
        confirm: bool = False,
        why: str | None = None,
    ) -> dict[str, Any]:
        """Delete a session or arrangement clip. Requires confirm=True; ask the user first."""
        params = kw(track=track, slot=slot, arrangement_index=arrangement_index, confirm=confirm)

        async def do() -> dict[str, Any]:
            address = clip_address(track, slot, arrangement_index)
            where = f"slot {slot}" if slot is not None else f"arrangement clip {arrangement_index}"
            require_confirm(confirm, "delete_clip", f"the clip in track {track} {where}")
            return await ctx.client.call("clip.delete", {**address, "confirm": True})

        return await run_tool(ctx, "delete_clip", "MD", params, why, do)
