"""Device and parameter tools."""

from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from ..errors import invalid_params
from .common import DESTROY, MUTATE, READ, AppContext, TrackType, kw, require_confirm, require_list_of_dicts, run_tool


def _check_value_spec(spec: dict[str, Any], where: str) -> None:
    given = [k for k in ("value", "normalized", "display") if spec.get(k) is not None]
    if len(given) != 1:
        raise invalid_params(f"{where} needs exactly one of value, normalized or display", {"given": given})


def register(mcp: FastMCP, ctx: AppContext) -> None:
    @mcp.tool(title="Get devices", annotations=READ)
    async def get_devices(
        track: int,
        track_type: TrackType = None,
        device_path: str | None = None,
        include_params: bool | None = None,
        depth: int = 2,
    ) -> dict[str, Any]:
        """List a track's devices (plus the mixer's parameters), or with device_path read one device in detail. include_params defaults to false for the list and true for a single device."""
        params = kw(track=track, track_type=track_type, device_path=device_path, include_params=include_params, depth=depth)

        async def do() -> dict[str, Any]:
            if device_path is not None:
                return await ctx.client.call(
                    "device.get",
                    kw(track=track, track_type=track_type, path=device_path, include_params=True if include_params is None else include_params),
                )
            return await ctx.client.call(
                "device.list",
                kw(track=track, track_type=track_type, include_params=False if include_params is None else include_params, depth=depth),
            )

        return await run_tool(ctx, "get_devices", "R", params, None, do)

    @mcp.tool(title="Set parameter", annotations=MUTATE)
    async def set_parameter(
        track: int,
        device_path: str,
        parameter: int | str,
        value: float | None = None,
        normalized: float | None = None,
        display: str | None = None,
        track_type: TrackType = None,
        why: str | None = None,
    ) -> dict[str, Any]:
        """Set one device parameter (by name or index) using exactly one of value (native range), normalized (0-1) or display (e.g. "-6 dB", or an item name for switches). device_path "mixer" reaches Volume, Pan and sends."""
        params = kw(track=track, track_type=track_type, device_path=device_path, parameter=parameter, value=value, normalized=normalized, display=display)

        async def do() -> dict[str, Any]:
            _check_value_spec(params, "set_parameter")
            return await ctx.client.call(
                "device.set_parameter",
                kw(track=track, track_type=track_type, path=device_path, parameter=parameter, value=value, normalized=normalized, display=display),
            )

        return await run_tool(ctx, "set_parameter", "M", params, why, do)

    @mcp.tool(title="Set parameters", annotations=MUTATE)
    async def set_parameters(
        track: int,
        device_path: str,
        values: list[dict[str, Any]],
        track_type: TrackType = None,
        why: str | None = None,
    ) -> dict[str, Any]:
        """Set several parameters on one device at once: values=[{parameter, value? | normalized? | display?}]. Partial success is reported per parameter."""
        params = kw(track=track, track_type=track_type, device_path=device_path, values=values)

        async def do() -> dict[str, Any]:
            require_list_of_dicts(values, "values", ("parameter",))
            for i, spec in enumerate(values):
                _check_value_spec(spec, f"values[{i}]")
            return await ctx.client.call("device.set_parameters", kw(track=track, track_type=track_type, path=device_path, values=values))

        return await run_tool(ctx, "set_parameters", "M", params, why, do)

    @mcp.tool(title="Set device enabled", annotations=MUTATE)
    async def set_device_enabled(
        track: int,
        device_path: str,
        enabled: bool,
        track_type: TrackType = None,
        why: str | None = None,
    ) -> dict[str, Any]:
        """Switch a device on or off (its Device On button)."""
        params = kw(track=track, track_type=track_type, device_path=device_path, enabled=enabled)
        return await run_tool(
            ctx,
            "set_device_enabled",
            "M",
            params,
            why,
            lambda: ctx.client.call("device.set_enabled", kw(track=track, track_type=track_type, path=device_path, enabled=enabled)),
        )

    @mcp.tool(title="Delete device", annotations=DESTROY)
    async def delete_device(
        track: int,
        device_path: str,
        confirm: bool = False,
        track_type: TrackType = None,
        why: str | None = None,
    ) -> dict[str, Any]:
        """Remove a device from a track. Requires confirm=True; ask the user first. Later device paths on the track shift."""
        params = kw(track=track, track_type=track_type, device_path=device_path, confirm=confirm)

        async def do() -> dict[str, Any]:
            require_confirm(confirm, "delete_device", f"device {device_path} on track {track}")
            return await ctx.client.call("device.delete", kw(track=track, track_type=track_type, path=device_path, confirm=True))

        return await run_tool(ctx, "delete_device", "MD", params, why, do)
