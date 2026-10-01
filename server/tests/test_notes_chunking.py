"""Chunking rules: 500 notes per request, 5000 per call, replace = replace + add + add."""

from __future__ import annotations


def make_notes(n: int) -> list[dict]:
    return [{"pitch": 36 + (i % 24), "start": i * 0.25, "duration": 0.25, "velocity": 100} for i in range(n)]


async def test_replace_1200_notes_is_three_requests(client, fake_script) -> None:
    res = await client.call_tool("replace_notes", {"track": 2, "slot": 0, "notes": make_notes(1200), "why": "new bass line"})
    assert res.isError is False, res.content[0].text
    methods = [m for m, _ in fake_script.calls]
    assert methods == ["notes.replace", "notes.add", "notes.add"]
    sizes = [len(p["notes"]) for _, p in fake_script.calls]
    assert sizes == [500, 500, 200]
    for _, p in fake_script.calls:
        assert p["track"] == 2 and p["slot"] == 0
    assert res.structuredContent == {"added": 1200, "removed": 16, "note_count": 1200, "chunks": 3}


async def test_add_1001_notes_is_three_adds(client, fake_script) -> None:
    res = await client.call_tool("add_notes", {"track": 2, "slot": 0, "notes": make_notes(1001)})
    assert res.isError is False
    assert [m for m, _ in fake_script.calls] == ["notes.add"] * 3
    assert [len(p["notes"]) for _, p in fake_script.calls] == [500, 500, 1]
    assert res.structuredContent["added"] == 1001
    assert res.structuredContent["chunks"] == 3
    assert "removed" not in res.structuredContent


async def test_small_add_is_one_request(client, fake_script) -> None:
    res = await client.call_tool("add_notes", {"track": 2, "arrangement_index": 0, "notes": make_notes(3)})
    assert res.isError is False
    assert len(fake_script.requests) == 1
    assert res.structuredContent == {"added": 3, "note_count": 19, "chunks": 1}


async def test_over_5000_notes_is_too_large_without_network(client, fake_script) -> None:
    res = await client.call_tool("add_notes", {"track": 2, "slot": 0, "notes": make_notes(5001)})
    assert res.isError is True
    assert "TOO_LARGE: 5001 notes exceeds the 5000-note limit" in res.content[0].text
    assert fake_script.requests == []


async def test_invalid_note_rejected_locally(client, fake_script) -> None:
    res = await client.call_tool("add_notes", {"track": 2, "slot": 0, "notes": [{"pitch": 60, "start": 0.0}]})
    assert res.isError is True
    assert "INVALID_PARAMS: notes[0] is missing duration" in res.content[0].text
    res = await client.call_tool("add_notes", {"track": 2, "slot": 0, "notes": [{"pitch": 200, "start": 0.0, "duration": 1.0}]})
    assert res.isError is True and "pitch" in res.content[0].text
    res = await client.call_tool("add_notes", {"track": 2, "slot": 0, "notes": []})
    assert res.isError is True and "must not be empty" in res.content[0].text
    assert fake_script.requests == []


async def test_empty_replace_clears_clip(client, fake_script) -> None:
    res = await client.call_tool("replace_notes", {"track": 2, "slot": 0, "notes": []})
    assert res.isError is False, res.content[0].text
    assert fake_script.calls == [("notes.replace", {"track": 2, "slot": 0, "notes": []})]
    assert res.structuredContent == {"added": 0, "removed": 16, "note_count": 0, "chunks": 1}


async def test_note_ids_are_stripped_from_specs(client, fake_script) -> None:
    res = await client.call_tool("add_notes", {"track": 2, "slot": 0, "notes": [{"id": 7, "pitch": 60, "start": 0.0, "duration": 1.0}]})
    assert res.isError is False
    assert fake_script.calls[0][1]["notes"] == [{"pitch": 60, "start": 0.0, "duration": 1.0}]
