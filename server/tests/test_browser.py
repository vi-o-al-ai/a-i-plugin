"""browse and load_device routing, resumable search and TIMEOUT retries."""

from __future__ import annotations

import json

from .fake_script import BROWSER_ITEMS


async def test_browse_query_searches(client, fake_script) -> None:
    res = await client.call_tool("browse", {"query": "reverb", "categories": ["audio_effects"], "limit": 5, "loadable_only": False})
    assert res.isError is False
    assert fake_script.calls == [("browser.search", {"query": "reverb", "categories": ["audio_effects"], "limit": 5, "loadable_only": False})]
    names = [i["name"] for i in res.structuredContent["items"]]
    assert names == ["Reverb", "Hybrid Reverb"]


async def test_browse_uri_lists(client, fake_script) -> None:
    res = await client.call_tool("browse", {"uri": "query:Synths"})
    assert res.isError is False
    assert fake_script.calls == [("browser.list", {"uri": "query:Synths", "limit": 25})]


async def test_browse_categories_only_lists_first(client, fake_script) -> None:
    res = await client.call_tool("browse", {"categories": ["instruments", "drums"]})
    assert res.isError is False
    assert fake_script.calls == [("browser.list", {"category": "instruments", "limit": 25})]
    assert all(i["category"] == "instruments" for i in res.structuredContent["items"])


async def test_browse_nothing_lists_roots(client, fake_script) -> None:
    res = await client.call_tool("browse", {})
    assert res.isError is False
    assert fake_script.calls == [("browser.list", {"limit": 25})]


async def test_browse_rejects_unknown_category(client, fake_script) -> None:
    res = await client.call_tool("browse", {"categories": ["synths"]})
    assert res.isError is True and "INVALID_PARAMS: Unknown browser categories: synths" in res.content[0].text
    assert fake_script.requests == []


async def test_load_device_by_uri(client, fake_script) -> None:
    res = await client.call_tool("load_device", {"track": 2, "uri": "query:AudioFx#Reverb", "after_device_path": "0", "why": "space"})
    assert res.isError is False
    assert fake_script.calls == [("browser.load", {"uri": "query:AudioFx#Reverb", "track": 2, "after_device_path": "0"})]
    assert res.structuredContent["loaded"]["name"] == "Reverb"
    assert "matched" not in res.structuredContent


async def test_load_device_by_name_exact_match(client, fake_script) -> None:
    res = await client.call_tool("load_device", {"track": 2, "name": "REVERB", "category": "audio_effects"})
    assert res.isError is False, res.content[0].text
    assert fake_script.calls == [
        ("browser.search", {"query": "REVERB", "categories": ["audio_effects"], "limit": 10, "loadable_only": True}),
        ("browser.load", {"uri": "query:AudioFx#Reverb", "track": 2}),
    ]
    s = res.structuredContent
    assert s["matched"] == {"name": "Reverb", "uri": "query:AudioFx#Reverb", "category": "audio_effects"}
    assert s["alternatives"] == [{"name": "Hybrid Reverb", "uri": "query:AudioFx#Hybrid%20Reverb", "category": "audio_effects"}]
    assert s["loaded"]["name"] == "Reverb"
    assert s["method"] == "load_item"


async def test_load_device_by_name_falls_back_to_first(client, fake_script) -> None:
    res = await client.call_tool("load_device", {"track": 2, "name": "wave"})
    assert res.isError is False
    assert fake_script.calls[0][0] == "browser.search" and "categories" not in fake_script.calls[0][1]
    assert fake_script.calls[1] == ("browser.load", {"uri": "query:Synths#Wavetable", "track": 2})
    s = res.structuredContent
    assert s["matched"]["name"] == "Wavetable"
    assert [a["name"] for a in s["alternatives"]] == ["Wavetable Bass"]


async def test_load_device_alternatives_capped_at_five(client, fake_script) -> None:
    fake_script.handlers["browser.search"] = lambda p: {
        "items": [{"name": f"Thing {i}", "uri": f"u{i}", "category": "instruments", "is_loadable": True} for i in range(10)],
        "truncated": False, "nodes_visited": 1,
    }
    res = await client.call_tool("load_device", {"track": 2, "name": "thing"})
    assert res.isError is False
    assert res.structuredContent["matched"]["uri"] == "u0"
    assert len(res.structuredContent["alternatives"]) == 5


async def test_load_device_name_not_found(client, fake_script) -> None:
    res = await client.call_tool("load_device", {"track": 2, "name": "zzz"})
    assert res.isError is True
    assert "NOT_FOUND: No loadable browser item matches 'zzz'. Call get_session" in res.content[0].text
    assert [m for m, _ in fake_script.calls] == ["browser.search"]


async def test_load_device_requires_exactly_one_of_uri_name(client, fake_script) -> None:
    for args in ({"track": 2}, {"track": 2, "uri": "x", "name": "y"}):
        res = await client.call_tool("load_device", args)
        assert res.isError is True and "INVALID_PARAMS: load_device needs exactly one of uri or name" in res.content[0].text
    assert fake_script.requests == []


# -- resumable search (PROTOCOL.md section 8): loop while truncated, merge by uri ------------


async def test_browse_merges_truncated_pages(client, fake_script) -> None:
    fake_script.search_truncated_calls = 2
    fake_script.search_pages = [
        [{"name": "Hybrid Reverb", "uri": "query:AudioFx#Hybrid%20Reverb", "category": "audio_effects", "path": ["Audio Effects", "Hybrid Reverb"]}],
        [{"name": "Reverb Rack", "uri": "query:AudioFx#Reverb%20Rack", "category": "audio_effects", "path": ["Audio Effects", "Reverb Rack"]}],
    ]
    res = await client.call_tool("browse", {"query": "reverb"})
    assert res.isError is False, res.content[0].text
    calls = fake_script.requests_for("browser.search")
    assert len(calls) == 3  # two truncated pages, then the finished traversal
    assert len({json.dumps(c["params"], sort_keys=True) for c in calls}) == 1  # the same call, repeated
    s = res.structuredContent
    # Merged across all three pages (the first two pages' items are not in the final one), re-ranked:
    # exact name match first, then prefix matches, then substring matches (case-insensitive).
    assert [i["name"] for i in s["items"]] == ["Reverb", "Reverb Rack", "Hybrid Reverb"]
    assert len({i["uri"] for i in s["items"]}) == 3
    assert s["truncated"] is False
    assert s["calls"] == 3
    assert s["nodes_visited"] == 1 + 1 + len(BROWSER_ITEMS)  # summed over the three calls
    assert s["total_matches"] >= 3


async def test_browse_duplicates_across_pages_are_merged_once(client, fake_script) -> None:
    fake_script.search_truncated_calls = 3  # cumulative default pages: 2, 4, 6 items, then all
    res = await client.call_tool("browse", {"query": "wave"})
    assert res.isError is False
    assert len(fake_script.requests_for("browser.search")) == 4
    names = [i["name"] for i in res.structuredContent["items"]]
    assert names == ["Wavetable", "Wavetable Bass"]  # each uri once, prefix order kept
    assert res.structuredContent["truncated"] is False and res.structuredContent["calls"] == 4


async def test_browse_stops_at_the_call_cap_and_reports_truncated(client, fake_script) -> None:
    fake_script.search_truncated_calls = 10_000
    res = await client.call_tool("browse", {"query": "reverb", "limit": 1})
    assert res.isError is False, res.content[0].text
    assert len(fake_script.requests_for("browser.search")) == 25
    s = res.structuredContent
    assert s["truncated"] is True and s["calls"] == 25
    assert len(s["items"]) == 1 and s["items"][0]["name"] == "Reverb"  # cut to limit after merging
    assert s["nodes_visited"] > 25


async def test_browse_respects_limit_after_merging(client, fake_script) -> None:
    res = await client.call_tool("browse", {"query": "e", "limit": 2})
    assert res.isError is False
    assert len(res.structuredContent["items"]) == 2
    assert res.structuredContent["total_matches"] > 2


# -- load_device by name waits for an exact match across pages ------------------------------


async def test_load_device_waits_for_exact_match_across_truncated_pages(client, fake_script) -> None:
    # Page 1 only has "Wavetable Bass"; the exact "Wavetable" shows up on page 2 (still truncated).
    fake_script.search_truncated_calls = 3
    fake_script.search_pages = [
        [{"name": "Wavetable Bass", "uri": "query:Sounds#Bass:Wavetable%20Bass", "category": "sounds", "path": ["Sounds"]}],
        [{"name": "Wavetable", "uri": "query:Synths#Wavetable", "category": "instruments", "path": ["Instruments"]}],
        [],
    ]
    res = await client.call_tool("load_device", {"track": 2, "name": "wavetable"})
    assert res.isError is False, res.content[0].text
    methods = [m for m, _ in fake_script.calls]
    assert methods == ["browser.search", "browser.search", "browser.load"]  # stopped early on the exact match
    assert fake_script.calls[-1] == ("browser.load", {"uri": "query:Synths#Wavetable", "track": 2})
    s = res.structuredContent
    assert s["matched"]["name"] == "Wavetable" and s["loaded"]["name"] == "Wavetable"
    assert [a["name"] for a in s["alternatives"]] == ["Wavetable Bass"]


async def test_load_device_never_guesses_while_truncated(client, fake_script) -> None:
    fake_script.search_truncated_calls = 10_000
    fake_script.search_pages = [[{"name": "Wavetable Bass", "uri": "u-bass", "category": "sounds", "path": []}]] * 30
    res = await client.call_tool("load_device", {"track": 2, "name": "wavetable"})
    assert res.isError is True
    text = res.content[0].text
    assert "TIMEOUT: No exact match for 'wavetable' in the part of the browser indexed so far (25 searches)" in text
    assert "still indexing the browser" in text
    assert '"candidates":[{"name":"Wavetable Bass"' in text
    methods = [m for m, _ in fake_script.calls]
    assert methods == ["browser.search"] * 25  # nothing was loaded


async def test_load_device_falls_back_once_the_traversal_finishes(client, fake_script) -> None:
    fake_script.search_truncated_calls = 2  # no exact match for "wave" anywhere; pages then finish
    res = await client.call_tool("load_device", {"track": 2, "name": "wave"})
    assert res.isError is False, res.content[0].text
    methods = [m for m, _ in fake_script.calls]
    assert methods == ["browser.search"] * 3 + ["browser.load"]
    assert fake_script.calls[-1] == ("browser.load", {"uri": "query:Synths#Wavetable", "track": 2})
    assert res.structuredContent["matched"]["name"] == "Wavetable"


async def test_load_device_not_found_only_after_full_traversal(client, fake_script) -> None:
    fake_script.search_truncated_calls = 2
    res = await client.call_tool("load_device", {"track": 2, "name": "zzz"})
    assert res.isError is True
    assert "NOT_FOUND: No loadable browser item matches 'zzz'" in res.content[0].text
    assert [m for m, _ in fake_script.calls] == ["browser.search"] * 3


# -- -32006 TIMEOUT with retry: true is repeated (PROTOCOL.md section 8) --------------------


async def test_load_device_retries_script_timeout(client, app, fake_script) -> None:
    app.client.retry_delay = 0.0
    fake_script.retry_timeouts["browser.load"] = 2
    res = await client.call_tool("load_device", {"track": 2, "uri": "query:AudioFx#Reverb"})
    assert res.isError is False, res.content[0].text
    assert [m for m, _ in fake_script.calls] == ["browser.load"] * 3  # succeeded on the third attempt
    assert res.structuredContent["loaded"]["name"] == "Reverb"


async def test_browse_uri_retries_then_surfaces_after_ten(client, app, fake_script) -> None:
    app.client.retry_delay = 0.0
    fake_script.retry_timeouts["browser.list"] = 2
    res = await client.call_tool("browse", {"uri": "query:Synths"})
    assert res.isError is False
    assert [m for m, _ in fake_script.calls] == ["browser.list"] * 3
    fake_script.requests.clear()
    fake_script.retry_timeouts["browser.list"] = 100
    res = await client.call_tool("browse", {"uri": "query:Synths"})
    assert res.isError is True
    assert "TIMEOUT: Browser traversal hit its time budget" in res.content[0].text
    assert "the server retries automatically. If you see this, call again." in res.content[0].text
    assert [m for m, _ in fake_script.calls] == ["browser.list"] * 10
