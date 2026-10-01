"""Session and transport tools."""

from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from ..errors import invalid_params
from .common import MUTATE, READ, AppContext, kw, run_tool


def register(mcp: FastMCP, ctx: AppContext) -> None:
    @mcp.tool(title="Get session overview", annotations=READ)
    async def get_session(
        include_clips: bool = True,
        include_devices: bool = True,
        include_params: bool = False,
        include_returns: bool = True,
    ) -> dict[str, Any]:
        """Read the whole set: transport, scale, tracks (with clips and devices), return tracks, master, scenes and selection. Use the indices it returns in every other tool."""
        params = kw(
            include_clips=include_clips,
            include_devices=include_devices,
            include_params=include_params,
            include_returns=include_returns,
        )
        return await run_tool(ctx, "get_session", "R", params, None, lambda: ctx.client.call("song.get_overview", params))

    @mcp.tool(title="Get transport", annotations=READ)
    async def get_transport() -> dict[str, Any]:
        """Read tempo, time signature, play state, playhead position (beats), loop, metronome and record state."""
        return await run_tool(ctx, "get_transport", "R", {}, None, lambda: ctx.client.call("song.get_transport", {}))

    @mcp.tool(title="Set transport", annotations=MUTATE)
    async def set_transport(
        tempo: float | None = None,
        metronome: bool | None = None,
        loop_enabled: bool | None = None,
        loop_start: float | None = None,
        loop_length: float | None = None,
        position: float | None = None,
        record_mode: bool | None = None,
        session_record: bool | None = None,
        signature_numerator: int | None = None,
        signature_denominator: int | None = None,
        why: str | None = None,
    ) -> dict[str, Any]:
        """Change tempo, metronome, arrangement loop, playhead position, record modes or time signature. Positions and lengths are in beats."""
        params = kw(
            tempo=tempo,
            metronome=metronome,
            loop_enabled=loop_enabled,
            loop_start=loop_start,
            loop_length=loop_length,
            position=position,
            record_mode=record_mode,
            session_record=session_record,
            signature_numerator=signature_numerator,
            signature_denominator=signature_denominator,
        )

        async def do() -> dict[str, Any]:
            if not params:
                raise invalid_params("set_transport needs at least one field to change")
            return await ctx.client.call("song.set_transport", params)

        return await run_tool(ctx, "set_transport", "M", params, why, do)

    @mcp.tool(title="Play", annotations=MUTATE)
    async def play(from_start: bool = False, why: str | None = None) -> dict[str, Any]:
        """Start playback (optionally from beat 0). Returns the transport state."""
        params = kw(from_start=from_start)
        return await run_tool(ctx, "play", "M", params, why, lambda: ctx.client.call("song.play", params))

    @mcp.tool(title="Stop", annotations=MUTATE)
    async def stop(why: str | None = None) -> dict[str, Any]:
        """Stop playback. Returns the transport state."""
        return await run_tool(ctx, "stop", "M", {}, why, lambda: ctx.client.call("song.stop", {}))

    @mcp.tool(title="Continue playing", annotations=MUTATE)
    async def continue_playing(why: str | None = None) -> dict[str, Any]:
        """Resume playback from the current playhead position without jumping back. Returns the transport state."""
        return await run_tool(ctx, "continue_playing", "M", {}, why, lambda: ctx.client.call("song.continue", {}))

    @mcp.tool(title="Set scale", annotations=MUTATE)
    async def set_scale(
        root_note: int | str | None = None,
        scale_name: str | None = None,
        why: str | None = None,
    ) -> dict[str, Any]:
        """Set the set's root note (0-11 or "C".."B") and/or scale name (Live 12). An unknown scale name fails with the list of available names."""
        params = kw(root_note=root_note, scale_name=scale_name)

        async def do() -> dict[str, Any]:
            if not params:
                raise invalid_params("set_scale needs root_note and/or scale_name")
            return await ctx.client.call("song.set_scale", params)

        return await run_tool(ctx, "set_scale", "M", params, why, do)

    async def _repeat(method: str, tool: str, steps: int) -> dict[str, Any]:
        if not isinstance(steps, int) or not 1 <= steps <= 20:
            raise invalid_params("steps must be an integer between 1 and 20", {"steps": steps})
        done = 0
        for _ in range(steps):
            await ctx.client.call(method, {})
            done += 1
        return {"ok": True, "steps": done}

    @mcp.tool(title="Undo", annotations=MUTATE)
    async def undo(steps: int = 1) -> dict[str, Any]:
        """Undo the last Live action (steps 1-20 undoes several). View and selection changes are not undoable."""
        params = kw(steps=steps)
        return await run_tool(ctx, "undo", "M", params, None, lambda: _repeat("song.undo", "undo", steps))

    @mcp.tool(title="Redo", annotations=MUTATE)
    async def redo(steps: int = 1) -> dict[str, Any]:
        """Redo the last undone Live action (steps 1-20 redoes several)."""
        params = kw(steps=steps)
        return await run_tool(ctx, "redo", "M", params, None, lambda: _repeat("song.redo", "redo", steps))
