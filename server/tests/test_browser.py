"""browse and load_device routing."""

from __future__ import annotations


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
