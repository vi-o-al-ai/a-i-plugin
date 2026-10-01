"""View and selection tools (UI only; recorded, not undoable)."""

from __future__ import annotations

from typing import Any, Literal

from mcp.server.fastmcp import FastMCP

from ..errors import invalid_params
from .common import READ, UI, AppContext, TrackType, kw, run_tool

ViewName = Literal["Session", "Arranger", "Detail/Clip", "Detail/DeviceChain", "Browser"]


def register(mcp: FastMCP, ctx: AppContext) -> None:
    @mcp.tool(title="Get selection", annotations=READ)
    async def get_selection() -> dict[str, Any]:
        """Read what is selected in Live: track, scene, clip slot, detail clip, device and parameter."""
        return await run_tool(ctx, "get_selection", "R", {}, None, lambda: ctx.client.call("view.get_selection", {}))

    @mcp.tool(title="Select", annotations=UI)
    async def select(
        track: int | None = None,
        track_type: TrackType = None,
        scene: int | None = None,
        slot: int | None = None,
        device_path: str | None = None,
        show_clip_detail: bool | None = None,
        show_device_detail: bool | None = None,
        why: str | None = None,
    ) -> dict[str, Any]:
        """Select a track, scene, clip slot (also selects its track and scene) or device in Live's UI, optionally opening the clip or device detail view. Changes the view only, not the set."""
        params = kw(
            track=track,
            track_type=track_type,
            scene=scene,
            slot=slot,
            device_path=device_path,
            show_clip_detail=show_clip_detail,
            show_device_detail=show_device_detail,
        )

        async def do() -> dict[str, Any]:
            if not params:
                raise invalid_params("select needs at least one of track, scene, slot, device_path, show_clip_detail, show_device_detail")
            if slot is not None and track is None:
                raise invalid_params("slot needs a track")
            if device_path is not None and track is None:
                raise invalid_params("device_path needs a track")
            return await ctx.client.call("view.select", params)

        return await run_tool(ctx, "select", "UI", params, why, do)

    @mcp.tool(title="Show view", annotations=UI)
    async def show_view(view: ViewName, why: str | None = None) -> dict[str, Any]:
        """Bring a Live view to the front: "Session", "Arranger", "Detail/Clip", "Detail/DeviceChain" or "Browser"."""
        params = kw(view=view)
        return await run_tool(ctx, "show_view", "UI", params, why, lambda: ctx.client.call("view.show_view", params))
