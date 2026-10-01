"""MIDI note tools, including chunked writes (500 notes per request, 5000 per call)."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import Any

from mcp.server.fastmcp import FastMCP

from ..errors import invalid_params, too_large
from .common import MUTATE, READ, AppContext, clip_address, kw, require_list_of_dicts, run_tool

CHUNK_SIZE = 500
MAX_NOTES_PER_CALL = 5000
NOTE_FIELDS = ("pitch", "start", "duration", "velocity", "mute", "probability", "velocity_deviation", "release_velocity")


def _num(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def validate_notes(notes: Any, allow_empty: bool) -> list[dict[str, Any]]:
    """Each note needs pitch (0-127), start (>= 0 beats) and duration (> 0 beats)."""
    require_list_of_dicts(notes, "notes", ("pitch", "start", "duration"), allow_empty=allow_empty)
    if len(notes) > MAX_NOTES_PER_CALL:
        raise too_large(
            f"{len(notes)} notes exceeds the {MAX_NOTES_PER_CALL}-note limit per call; split into several calls",
            {"limit": MAX_NOTES_PER_CALL, "got": len(notes)},
        )
    for i, note in enumerate(notes):
        pitch, start, duration = note["pitch"], note["start"], note["duration"]
        if not _num(pitch) or not 0 <= pitch <= 127:
            raise invalid_params(f"notes[{i}].pitch must be a MIDI note number 0-127", {"index": i, "pitch": pitch})
        if not _num(start) or start < 0:
            raise invalid_params(f"notes[{i}].start must be >= 0 beats", {"index": i, "start": start})
        if not _num(duration) or duration <= 0:
            raise invalid_params(f"notes[{i}].duration must be > 0 beats", {"index": i, "duration": duration})
        velocity = note.get("velocity")
        if velocity is not None and (not _num(velocity) or not 1 <= velocity <= 127):
            raise invalid_params(f"notes[{i}].velocity must be 1-127", {"index": i, "velocity": velocity})
        unknown = [k for k in note if k not in NOTE_FIELDS and k != "id"]
        if unknown:
            raise invalid_params(f"notes[{i}] has unknown fields: {', '.join(unknown)}", {"index": i, "unknown": unknown})
    return [{k: v for k, v in n.items() if k != "id"} for n in notes]


def chunks(items: list[Any], size: int = CHUNK_SIZE) -> list[list[Any]]:
    return [items[i : i + size] for i in range(0, len(items), size)] or [[]]


def register(mcp: FastMCP, ctx: AppContext) -> None:
    @mcp.tool(title="Get notes", annotations=READ)
    async def get_notes(
        track: int,
        slot: int | None = None,
        arrangement_index: int | None = None,
        from_time: float | None = None,
        time_span: float | None = None,
        from_pitch: int | None = None,
        pitch_span: int | None = None,
    ) -> dict[str, Any]:
        """Read a MIDI clip's notes (with ids) sorted by start then pitch; optionally limit to a time/pitch window. Times are beats from clip start."""
        params = kw(
            track=track,
            slot=slot,
            arrangement_index=arrangement_index,
            from_time=from_time,
            time_span=time_span,
            from_pitch=from_pitch,
            pitch_span=pitch_span,
        )

        async def do() -> dict[str, Any]:
            address = clip_address(track, slot, arrangement_index)
            return await ctx.client.call("notes.get", {**address, **kw(from_time=from_time, time_span=time_span, from_pitch=from_pitch, pitch_span=pitch_span)})

        return await run_tool(ctx, "get_notes", "R", params, None, do)

    async def _write_notes(
        address: dict[str, Any],
        notes: list[dict[str, Any]],
        first_method: str,
    ) -> dict[str, Any]:
        """Send notes in 500-note chunks: ``first_method`` for the first, ``notes.add`` for the rest."""
        added = 0
        removed: int | None = None
        note_count: int | None = None
        sent = 0
        for i, chunk in enumerate(chunks(notes)):
            method = first_method if i == 0 else "notes.add"
            result = await ctx.client.call(method, {**address, "notes": chunk})
            sent += 1
            added += int(result.get("added", len(chunk)) or 0)
            if i == 0 and "removed" in result:
                removed = result["removed"]
            if "note_count" in result:
                note_count = result["note_count"]
        out: dict[str, Any] = {"added": added, "note_count": note_count, "chunks": sent}
        if removed is not None:
            out["removed"] = removed
        return out

    @mcp.tool(title="Add notes", annotations=MUTATE)
    async def add_notes(
        track: int,
        slot: int | None = None,
        arrangement_index: int | None = None,
        notes: list[dict[str, Any]] | None = None,
        why: str | None = None,
    ) -> dict[str, Any]:
        """Add notes to a MIDI clip: [{pitch, start, duration, velocity?=100, mute?, probability?, velocity_deviation?, release_velocity?}]. Times are beats from clip start; up to 5000 notes per call (sent in chunks)."""
        params = kw(track=track, slot=slot, arrangement_index=arrangement_index, notes=notes)

        async def do() -> dict[str, Any]:
            address = clip_address(track, slot, arrangement_index)
            clean = validate_notes(notes if notes is not None else [], allow_empty=False)
            return await _write_notes(address, clean, "notes.add")

        return await run_tool(ctx, "add_notes", "M", params, why, do)

    @mcp.tool(title="Replace notes", annotations=MUTATE)
    async def replace_notes(
        track: int,
        slot: int | None = None,
        arrangement_index: int | None = None,
        notes: list[dict[str, Any]] | None = None,
        why: str | None = None,
    ) -> dict[str, Any]:
        """Remove every note in a MIDI clip and write these instead (same note format as add_notes; an empty list clears the clip). Up to 5000 notes per call."""
        params = kw(track=track, slot=slot, arrangement_index=arrangement_index, notes=notes)

        async def do() -> dict[str, Any]:
            address = clip_address(track, slot, arrangement_index)
            clean = validate_notes(notes if notes is not None else [], allow_empty=True)
            return await _write_notes(address, clean, "notes.replace")

        return await run_tool(ctx, "replace_notes", "M", params, why, do)

    @mcp.tool(title="Remove notes", annotations=MUTATE)
    async def remove_notes(
        track: int,
        slot: int | None = None,
        arrangement_index: int | None = None,
        note_ids: list[int] | None = None,
        from_time: float | None = None,
        time_span: float | None = None,
        from_pitch: int | None = None,
        pitch_span: int | None = None,
        why: str | None = None,
    ) -> dict[str, Any]:
        """Remove notes by id, or every note in a time/pitch window (no filters = all notes). Times are beats from clip start."""
        params = kw(
            track=track,
            slot=slot,
            arrangement_index=arrangement_index,
            note_ids=note_ids,
            from_time=from_time,
            time_span=time_span,
            from_pitch=from_pitch,
            pitch_span=pitch_span,
        )

        async def do() -> dict[str, Any]:
            address = clip_address(track, slot, arrangement_index)
            return await ctx.client.call(
                "notes.remove",
                {**address, **kw(note_ids=note_ids, from_time=from_time, time_span=time_span, from_pitch=from_pitch, pitch_span=pitch_span)},
            )

        return await run_tool(ctx, "remove_notes", "M", params, why, do)

    @mcp.tool(title="Modify notes", annotations=MUTATE)
    async def modify_notes(
        track: int,
        slot: int | None = None,
        arrangement_index: int | None = None,
        changes: list[dict[str, Any]] | None = None,
        why: str | None = None,
    ) -> dict[str, Any]:
        """Edit existing notes in place by id: [{id, pitch?, start?, duration?, velocity?, mute?, probability?, velocity_deviation?, release_velocity?}]. Get ids from get_notes."""
        params = kw(track=track, slot=slot, arrangement_index=arrangement_index, changes=changes)

        async def do() -> dict[str, Any]:
            address = clip_address(track, slot, arrangement_index)
            require_list_of_dicts(changes, "changes", ("id",))
            return await ctx.client.call("notes.modify", {**address, "changes": changes})

        return await run_tool(ctx, "modify_notes", "M", params, why, do)

    @mcp.tool(title="Quantize notes", annotations=MUTATE)
    async def quantize_notes(
        track: int,
        slot: int | None = None,
        arrangement_index: int | None = None,
        grid: float = 0.25,
        amount: float = 1.0,
        swing: float = 0.0,
        why: str | None = None,
    ) -> dict[str, Any]:
        """Quantize note starts to a grid in beats (0.25 = 16th) by amount 0-1, with optional swing 0-1 on every second grid step."""
        params = kw(track=track, slot=slot, arrangement_index=arrangement_index, grid=grid, amount=amount, swing=swing)

        async def do() -> dict[str, Any]:
            address = clip_address(track, slot, arrangement_index)
            if grid <= 0:
                raise invalid_params("grid must be > 0 beats", {"grid": grid})
            if not 0 <= amount <= 1 or not 0 <= swing <= 1:
                raise invalid_params("amount and swing must be between 0 and 1", {"amount": amount, "swing": swing})
            return await ctx.client.call("notes.quantize", {**address, "grid": grid, "amount": amount, "swing": swing})

        return await run_tool(ctx, "quantize_notes", "M", params, why, do)

    @mcp.tool(title="Transpose notes", annotations=MUTATE)
    async def transpose_notes(
        track: int,
        slot: int | None = None,
        arrangement_index: int | None = None,
        semitones: int = 0,
        from_time: float | None = None,
        time_span: float | None = None,
        from_pitch: int | None = None,
        pitch_span: int | None = None,
        why: str | None = None,
    ) -> dict[str, Any]:
        """Shift notes by semitones (clamped to 0-127), optionally only within a time/pitch window."""
        params = kw(
            track=track,
            slot=slot,
            arrangement_index=arrangement_index,
            semitones=semitones,
            from_time=from_time,
            time_span=time_span,
            from_pitch=from_pitch,
            pitch_span=pitch_span,
        )

        async def do() -> dict[str, Any]:
            address = clip_address(track, slot, arrangement_index)
            if semitones == 0:
                raise invalid_params("semitones must be a non-zero integer")
            return await ctx.client.call(
                "notes.transpose",
                {**address, "semitones": semitones, **kw(from_time=from_time, time_span=time_span, from_pitch=from_pitch, pitch_span=pitch_span)},
            )

        return await run_tool(ctx, "transpose_notes", "M", params, why, do)
