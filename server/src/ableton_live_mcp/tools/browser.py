"""Browser tools: browse and load_device."""

from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from ..errors import invalid_params, not_found
from .common import MUTATE, READ, AppContext, TrackType, kw, run_tool

CATEGORIES = (
    "instruments",
    "sounds",
    "drums",
    "audio_effects",
    "midi_effects",
    "plugins",
    "max_for_live",
    "packs",
    "user_library",
    "samples",
    "clips",
)
SEARCH_LIMIT_FOR_LOAD = 10
MAX_ALTERNATIVES = 5


def _brief(item: dict[str, Any]) -> dict[str, Any]:
    return {"name": item.get("name"), "uri": item.get("uri"), "category": item.get("category")}


def pick_best(items: list[dict[str, Any]], name: str) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Exact case-insensitive name match wins, else the first result (already ranked by the script)."""
    wanted = name.strip().lower()
    best = next((i for i in items if str(i.get("name", "")).strip().lower() == wanted), items[0])
    others = [i for i in items if i is not best][:MAX_ALTERNATIVES]
    return best, others


def register(mcp: FastMCP, ctx: AppContext) -> None:
    @mcp.tool(title="Browse Live's browser", annotations=READ)
    async def browse(
        query: str | None = None,
        categories: list[str] | None = None,
        uri: str | None = None,
        limit: int = 25,
        loadable_only: bool = True,
    ) -> dict[str, Any]:
        """Search Live's browser by name (query, optionally within categories such as instruments, drums, audio_effects, midi_effects, sounds) or list the children of a category or of a folder uri. Returns items with uris for load_device."""
        params = kw(query=query, categories=categories, uri=uri, limit=limit, loadable_only=loadable_only)

        async def do() -> dict[str, Any]:
            if categories:
                bad = [c for c in categories if c not in CATEGORIES]
                if bad:
                    raise invalid_params(f"Unknown browser categories: {', '.join(bad)}", {"available": list(CATEGORIES)})
            if query:
                return await ctx.client.call(
                    "browser.search",
                    kw(query=query, categories=categories, limit=limit, loadable_only=loadable_only),
                )
            if uri:
                return await ctx.client.call("browser.list", kw(uri=uri, limit=limit))
            return await ctx.client.call("browser.list", kw(category=categories[0] if categories else None, limit=limit))

        return await run_tool(ctx, "browse", "R", params, None, do)

    @mcp.tool(title="Load device", annotations=MUTATE)
    async def load_device(
        track: int,
        uri: str | None = None,
        name: str | None = None,
        track_type: TrackType = None,
        after_device_path: str | None = None,
        category: str | None = None,
        why: str | None = None,
    ) -> dict[str, Any]:
        """Load a device, preset or sample onto a track by browser uri, or by name (the best search match is loaded and `matched`/`alternatives` are returned so a wrong pick can be corrected). Optionally insert after after_device_path."""
        params = kw(track=track, track_type=track_type, uri=uri, name=name, after_device_path=after_device_path, category=category)

        async def do() -> dict[str, Any]:
            if (uri is None) == (name is None):
                raise invalid_params("load_device needs exactly one of uri or name")
            if category is not None and category not in CATEGORIES:
                raise invalid_params(f"Unknown browser category: {category}", {"available": list(CATEGORIES)})
            matched: dict[str, Any] | None = None
            alternatives: list[dict[str, Any]] = []
            target_uri = uri
            if name is not None:
                search = await ctx.client.call(
                    "browser.search",
                    kw(query=name, categories=[category] if category else None, limit=SEARCH_LIMIT_FOR_LOAD, loadable_only=True),
                )
                items = [i for i in search.get("items") or [] if isinstance(i, dict) and i.get("uri")]
                if not items:
                    raise not_found(
                        f"No loadable browser item matches {name!r}" + (f" in {category}" if category else ""),
                        {"kind": "browser_item", "name": name, "category": category},
                    )
                best, others = pick_best(items, name)
                matched, alternatives = _brief(best), [_brief(o) for o in others]
                target_uri = best["uri"]
            result = await ctx.client.call(
                "browser.load",
                kw(uri=target_uri, track=track, track_type=track_type, after_device_path=after_device_path),
            )
            out = dict(result)
            if matched is not None:
                out["matched"] = matched
                out["alternatives"] = alternatives
            return out

        return await run_tool(ctx, "load_device", "M", params, why, do)
