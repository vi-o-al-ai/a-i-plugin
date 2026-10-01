"""Track tools."""

from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from ..errors import invalid_params
from .common import DESTROY, MUTATE, READ, AppContext, TrackType, kw, require_confirm, require_list_of_dicts, run_tool


def register(mcp: FastMCP, ctx: AppContext) -> None:
    @mcp.tool(title="Get track", annotations=READ)
    async def get_track(
        track: int,
        track_type: TrackType = None,
        include_clips: bool = True,
        include_devices: bool = True,
        include_params: bool = False,
        include_note_counts: bool = False,
    ) -> dict[str, Any]:
        """Read one track (track_type "track" | "return" | "master") with its mixer state, clips and devices; include_note_counts fills note_count on its MIDI clips."""
        params = kw(
            track=track,
            track_type=track_type,
            include_clips=include_clips,
            include_devices=include_devices,
            include_params=include_params,
            include_note_counts=include_note_counts,
        )
        return await run_tool(ctx, "get_track", "R", params, None, lambda: ctx.client.call("track.get", params))

    @mcp.tool(title="Create MIDI track", annotations=MUTATE)
    async def create_midi_track(name: str | None = None, index: int = -1, why: str | None = None) -> dict[str, Any]:
        """Create a MIDI track at index (-1 = end) and optionally name it. Track indices after it shift; re-read before using them."""
        params = kw(index=index, name=name)
        return await run_tool(ctx, "create_midi_track", "M", params, why, lambda: ctx.client.call("song.create_midi_track", params))

    @mcp.tool(title="Create audio track", annotations=MUTATE)
    async def create_audio_track(name: str | None = None, index: int = -1, why: str | None = None) -> dict[str, Any]:
        """Create an audio track at index (-1 = end) and optionally name it. Track indices after it shift; re-read before using them."""
        params = kw(index=index, name=name)
        return await run_tool(ctx, "create_audio_track", "M", params, why, lambda: ctx.client.call("song.create_audio_track", params))

    @mcp.tool(title="Create return track", annotations=MUTATE)
    async def create_return_track(name: str | None = None, why: str | None = None) -> dict[str, Any]:
        """Create a return track (addressed afterwards with track_type="return")."""
        params = kw(name=name)
        return await run_tool(ctx, "create_return_track", "M", params, why, lambda: ctx.client.call("song.create_return_track", params))

    @mcp.tool(title="Set track", annotations=MUTATE)
    async def set_track(
        track: int,
        track_type: TrackType = None,
        name: str | None = None,
        color_index: int | None = None,
        mute: bool | None = None,
        solo: bool | None = None,
        arm: bool | None = None,
        volume: float | None = None,
        pan: float | None = None,
        sends: list[dict[str, Any]] | None = None,
        fold: bool | None = None,
        why: str | None = None,
    ) -> dict[str, Any]:
        """Change a track's name, color_index (0-69), mute/solo/arm, volume (0-1, 0.85 = 0 dB), pan (-1..1), sends ([{index, value}]) or fold state."""
        params = kw(
            track=track,
            track_type=track_type,
            name=name,
            color_index=color_index,
            mute=mute,
            solo=solo,
            arm=arm,
            volume=volume,
            pan=pan,
            sends=sends,
            fold=fold,
        )

        async def do() -> dict[str, Any]:
            if len(params) - (1 if track_type is not None else 0) <= 1:
                raise invalid_params("set_track needs at least one field to change")
            if sends is not None:
                require_list_of_dicts(sends, "sends", ("index", "value"))
            return await ctx.client.call("track.set", params)

        return await run_tool(ctx, "set_track", "M", params, why, do)

    @mcp.tool(title="Delete track", annotations=DESTROY)
    async def delete_track(
        track: int,
        track_type: str = "track",
        confirm: bool = False,
        why: str | None = None,
    ) -> dict[str, Any]:
        """Delete a track ("track") or return track ("return") and everything on it. Requires confirm=True; ask the user first. Later indices of that kind shift down."""
        params = kw(track=track, track_type=track_type, confirm=confirm)

        async def do() -> dict[str, Any]:
            if track_type not in ("track", "return"):
                raise invalid_params(
                    'delete_track track_type must be "track" or "return" (the master track cannot be deleted)',
                    {"track_type": track_type, "available": ["track", "return"]},
                )
            label = f"return track {track}" if track_type == "return" else f"track {track}"
            require_confirm(confirm, "delete_track", f"{label} and all of its clips and devices")
            return await ctx.client.call("song.delete_track", {"track": track, "track_type": track_type, "confirm": True})

        return await run_tool(ctx, "delete_track", "MD", params, why, do)
