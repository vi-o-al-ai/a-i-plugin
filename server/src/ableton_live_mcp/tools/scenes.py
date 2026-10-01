"""Scene tools."""

from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from ..errors import invalid_params
from .common import DESTROY, MUTATE, AppContext, kw, require_confirm, run_tool


def register(mcp: FastMCP, ctx: AppContext) -> None:
    @mcp.tool(title="Create scene", annotations=MUTATE)
    async def create_scene(name: str | None = None, index: int = -1, why: str | None = None) -> dict[str, Any]:
        """Create a scene at index (-1 = end) and optionally name it. Scene and slot indices after it shift."""
        params = kw(index=index, name=name)
        return await run_tool(ctx, "create_scene", "M", params, why, lambda: ctx.client.call("song.create_scene", params))

    @mcp.tool(title="Set scene", annotations=MUTATE)
    async def set_scene(
        scene: int,
        name: str | None = None,
        color_index: int | None = None,
        tempo: float | None = None,
        why: str | None = None,
    ) -> dict[str, Any]:
        """Rename a scene, set its color_index (0-69) or give it a scene tempo (BPM)."""
        params = kw(scene=scene, name=name, color_index=color_index, tempo=tempo)

        async def do() -> dict[str, Any]:
            if len(params) <= 1:
                raise invalid_params("set_scene needs at least one of name, color_index, tempo")
            return await ctx.client.call("scene.set", params)

        return await run_tool(ctx, "set_scene", "M", params, why, do)

    @mcp.tool(title="Fire scene", annotations=MUTATE)
    async def fire_scene(scene: int, why: str | None = None) -> dict[str, Any]:
        """Launch a scene (all its clips start at the next launch quantization)."""
        params = kw(scene=scene)
        return await run_tool(ctx, "fire_scene", "M", params, why, lambda: ctx.client.call("scene.fire", params))

    @mcp.tool(title="Duplicate scene", annotations=MUTATE)
    async def duplicate_scene(scene: int, why: str | None = None) -> dict[str, Any]:
        """Duplicate a scene with its clips; the copy is inserted right after it and returned. Later scene indices shift."""
        params = kw(scene=scene)
        return await run_tool(ctx, "duplicate_scene", "M", params, why, lambda: ctx.client.call("song.duplicate_scene", params))

    @mcp.tool(title="Delete scene", annotations=DESTROY)
    async def delete_scene(scene: int, confirm: bool = False, why: str | None = None) -> dict[str, Any]:
        """Delete a scene and the clips in it. Requires confirm=True; ask the user first. Later scene indices shift down."""
        params = kw(scene=scene, confirm=confirm)

        async def do() -> dict[str, Any]:
            require_confirm(confirm, "delete_scene", f"scene {scene} and all clips in it")
            return await ctx.client.call("song.delete_scene", {"scene": scene, "confirm": True})

        return await run_tool(ctx, "delete_scene", "MD", params, why, do)
