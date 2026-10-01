"""Clip automation envelope tools."""

from __future__ import annotations

from typing import Any, Literal

from mcp.server.fastmcp import FastMCP

from ..errors import invalid_params
from .common import DESTROY, MUTATE, READ, AppContext, clip_address, kw, require_confirm, require_list_of_dicts, run_tool


def register(mcp: FastMCP, ctx: AppContext) -> None:
    @mcp.tool(title="Get automation", annotations=READ)
    async def get_automation(
        track: int,
        device_path: str,
        parameter: int | str,
        slot: int | None = None,
        arrangement_index: int | None = None,
        from_time: float | None = None,
        time_span: float | None = None,
        resolution: float = 0.25,
    ) -> dict[str, Any]:
        """Read a clip's automation envelope for one parameter (device_path may be "mixer"), sampled every `resolution` beats."""
        params = kw(
            track=track,
            slot=slot,
            arrangement_index=arrangement_index,
            device_path=device_path,
            parameter=parameter,
            from_time=from_time,
            time_span=time_span,
            resolution=resolution,
        )

        async def do() -> dict[str, Any]:
            address = clip_address(track, slot, arrangement_index)
            return await ctx.client.call(
                "automation.get",
                {**address, **kw(device_path=device_path, parameter=parameter, from_time=from_time, time_span=time_span, resolution=resolution)},
            )

        return await run_tool(ctx, "get_automation", "R", params, None, do)

    @mcp.tool(title="Set automation", annotations=MUTATE)
    async def set_automation(
        track: int,
        device_path: str,
        parameter: int | str,
        points: list[dict[str, Any]],
        slot: int | None = None,
        arrangement_index: int | None = None,
        mode: Literal["ramp", "steps"] = "ramp",
        resolution: float = 0.0625,
        why: str | None = None,
    ) -> dict[str, Any]:
        """Write a clip automation envelope from points=[{time, value}] (time in beats from clip start, value in the parameter's native range); mode "ramp" interpolates, "steps" holds each value."""
        params = kw(
            track=track,
            slot=slot,
            arrangement_index=arrangement_index,
            device_path=device_path,
            parameter=parameter,
            points=points,
            mode=mode,
            resolution=resolution,
        )

        async def do() -> dict[str, Any]:
            address = clip_address(track, slot, arrangement_index)
            require_list_of_dicts(points, "points", ("time", "value"))
            if resolution <= 0:
                raise invalid_params("resolution must be > 0 beats", {"resolution": resolution})
            return await ctx.client.call(
                "automation.set",
                {**address, "device_path": device_path, "parameter": parameter, "points": points, "mode": mode, "resolution": resolution},
            )

        return await run_tool(ctx, "set_automation", "M", params, why, do)

    @mcp.tool(title="Clear automation", annotations=DESTROY)
    async def clear_automation(
        track: int,
        slot: int | None = None,
        arrangement_index: int | None = None,
        device_path: str | None = None,
        parameter: int | str | None = None,
        confirm: bool = False,
        why: str | None = None,
    ) -> dict[str, Any]:
        """Clear one parameter's automation envelope in a clip, or with no parameter every envelope in the clip (that needs confirm=True; ask the user first)."""
        params = kw(track=track, slot=slot, arrangement_index=arrangement_index, device_path=device_path, parameter=parameter, confirm=confirm)
        clearing_all = parameter is None
        flags = "MD" if clearing_all else "M"

        async def do() -> dict[str, Any]:
            address = clip_address(track, slot, arrangement_index)
            if clearing_all:
                where = f"slot {slot}" if slot is not None else f"arrangement clip {arrangement_index}"
                require_confirm(confirm, "clear_automation", f"every automation envelope in track {track} {where}")
            elif device_path is None:
                raise invalid_params("device_path is required when parameter is given")
            proto = {**address, **kw(device_path=device_path, parameter=parameter)}
            if confirm:
                proto["confirm"] = True
            return await ctx.client.call("automation.clear", proto)

        return await run_tool(ctx, "clear_automation", flags, params, why, do)
