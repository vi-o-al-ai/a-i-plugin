"""Browser tools: browse and load_device.

PROTOCOL.md section 7 (browser.*) and 8: ``browser.search`` is resumable and answers
``truncated: true`` while the traversal is unfinished, so the server calls it again (bounded)
and merges the pages by ``uri``; ``browser.list``/``browser.load`` may answer ``-32006`` with
``retry: true`` while a uri is being resolved, which ``LiveClient.call_retrying`` repeats.
"""

from __future__ import annotations

from typing import Any

from mcp.server.fastmcp import FastMCP

from ..errors import SCRIPT_TIMEOUT, invalid_params, not_found, tool_error
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
MAX_SEARCH_CALLS = 25  # PROTOCOL.md section 8: repeat browser.search while truncated, at most 25 times


def _brief(item: dict[str, Any]) -> dict[str, Any]:
    return {"name": item.get("name"), "uri": item.get("uri"), "category": item.get("category")}


def _name(item: dict[str, Any]) -> str:
    return str(item.get("name", "")).strip().lower()


def rank(name: str, query: str) -> int:
    """The script's ordering: exact name match 0, prefix 1, substring 2, anything else 3 (case-insensitive)."""
    name, query = name.strip().lower(), query.strip().lower()
    if name == query:
        return 0
    if name.startswith(query):
        return 1
    if query in name:
        return 2
    return 3


def merge_items(merged: dict[str, dict[str, Any]], items: Any) -> None:
    """Add the items of one search page to ``merged`` (keyed by uri; first occurrence wins)."""
    for item in items or []:
        if isinstance(item, dict) and item.get("uri") and item["uri"] not in merged:
            merged[item["uri"]] = item


def sort_items(items: list[dict[str, Any]], query: str) -> list[dict[str, Any]]:
    """Stable re-sort of a merged set by the script's rank rule."""
    return sorted(items, key=lambda i: rank(_name(i), query))


def pick_best(items: list[dict[str, Any]], name: str) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Exact case-insensitive name match wins, else the best-ranked item; plus up to five alternatives."""
    ordered = sort_items(items, name)
    best = ordered[0]
    others = [i for i in ordered if i is not best][:MAX_ALTERNATIVES]
    return best, others


def exact_match(items: list[dict[str, Any]], name: str) -> dict[str, Any] | None:
    wanted = name.strip().lower()
    return next((i for i in items if _name(i) == wanted), None)


def register(mcp: FastMCP, ctx: AppContext) -> None:
    async def search_pages(params: dict[str, Any], *, stop_when: Any = None) -> dict[str, Any]:
        """Call ``browser.search`` until the traversal finishes, ``MAX_SEARCH_CALLS`` is hit, or
        ``stop_when(items)`` says the caller has what it needs. Returns the merged result."""
        merged: dict[str, dict[str, Any]] = {}
        calls = 0
        nodes_visited = 0
        total_matches = 0
        truncated = True
        while truncated and calls < MAX_SEARCH_CALLS:
            page = await ctx.client.call_retrying("browser.search", params)
            calls += 1
            merge_items(merged, page.get("items"))
            nodes_visited += int(page.get("nodes_visited") or 0)
            total_matches = max(total_matches, int(page.get("total_matches") or 0), len(merged))
            truncated = bool(page.get("truncated"))
            if stop_when is not None and stop_when(list(merged.values())):
                break
        return {
            "items": sort_items(list(merged.values()), str(params.get("query", ""))),
            "truncated": truncated,
            "nodes_visited": nodes_visited,
            "total_matches": total_matches,
            "calls": calls,
        }

    @mcp.tool(title="Browse Live's browser", annotations=READ)
    async def browse(
        query: str | None = None,
        categories: list[str] | None = None,
        uri: str | None = None,
        limit: int = 25,
        loadable_only: bool = True,
    ) -> dict[str, Any]:
        """Search Live's browser by name (query, optionally within categories such as instruments, drums, audio_effects, midi_effects, sounds) or list the children of a category or of a folder uri. Returns items with uris for load_device; truncated=true means the browser index was still being built after 25 searches, so call again."""
        params = kw(query=query, categories=categories, uri=uri, limit=limit, loadable_only=loadable_only)

        async def do() -> dict[str, Any]:
            if categories:
                bad = [c for c in categories if c not in CATEGORIES]
                if bad:
                    raise invalid_params(f"Unknown browser categories: {', '.join(bad)}", {"available": list(CATEGORIES)})
            if query:
                result = await search_pages(kw(query=query, categories=categories, limit=limit, loadable_only=loadable_only))
                result["items"] = result["items"][: max(1, int(limit))]
                return result
            if uri:
                return await ctx.client.call_retrying("browser.list", kw(uri=uri, limit=limit))
            return await ctx.client.call_retrying("browser.list", kw(category=categories[0] if categories else None, limit=limit))

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
        """Load a device, preset or sample onto a track by browser uri, or by name (an exact name match is preferred; otherwise the best search match is loaded and `matched`/`alternatives` are returned so a wrong pick can be corrected). Optionally insert after after_device_path."""
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
                search = await search_pages(
                    kw(query=name, categories=[category] if category else None, limit=SEARCH_LIMIT_FOR_LOAD, loadable_only=True),
                    stop_when=lambda items: exact_match(items, name) is not None,
                )
                items = search["items"]
                where = f" in {category}" if category else ""
                if exact_match(items, name) is None and search["truncated"]:
                    # Never load a guess while the traversal is unfinished: the exact item may
                    # simply not have been indexed yet.
                    raise tool_error(
                        SCRIPT_TIMEOUT,
                        f"No exact match for {name!r}{where} in the part of the browser indexed so far "
                        f"({search['calls']} searches); call again, or pick a uri with browse",
                        {"retry": True, "name": name, "category": category, "candidates": [_brief(i) for i in items[:MAX_ALTERNATIVES]]},
                    )
                if not items:
                    raise not_found(
                        f"No loadable browser item matches {name!r}{where}",
                        {"kind": "browser_item", "name": name, "category": category},
                    )
                best, others = pick_best(items, name)
                matched, alternatives = _brief(best), [_brief(o) for o in others]
                target_uri = best["uri"]
            result = await ctx.client.call_retrying(
                "browser.load",
                kw(uri=target_uri, track=track, track_type=track_type, after_device_path=after_device_path),
            )
            out = dict(result)
            if matched is not None:
                out["matched"] = matched
                out["alternatives"] = alternatives
            return out

        return await run_tool(ctx, "load_device", "M", params, why, do)
