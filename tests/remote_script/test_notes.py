"""notes.* handlers."""
import pytest

BASS = {"track": 1, "slot": 0}
NOTE_KEYS = {"id", "pitch", "start", "duration", "velocity", "mute", "probability", "velocity_deviation",
             "release_velocity"}


@pytest.fixture
def scratch(rpc):
    """An empty 4-beat MIDI clip on Drums slot 2."""
    rpc("clip.create", track=0, slot=2, length=4.0, name="Scratch")
    return {"track": 0, "slot": 2}


def test_notes_get(rpc):
    result = rpc("notes.get", **BASS)
    assert set(result) == {"notes", "count", "clip_length"}
    assert result["count"] == 5 and result["clip_length"] == 4.0
    assert [n["start"] for n in result["notes"]] == [0.0, 1.0, 1.5, 2.0, 3.0]
    assert set(result["notes"][0]) == NOTE_KEYS
    ids = [n["id"] for n in result["notes"]]
    assert len(set(ids)) == 5 and all(isinstance(i, int) for i in ids)
    assert result["notes"][0] == {"id": ids[0], "pitch": 36, "start": 0.0, "duration": 1.0, "velocity": 100.0,
                                  "mute": False, "probability": 1.0, "velocity_deviation": 0.0,
                                  "release_velocity": 64.0}


def test_notes_get_sorted_by_start_then_pitch(rpc):
    notes = rpc("notes.get", track=2, slot=0)["notes"]
    assert [(n["start"], n["pitch"]) for n in notes] == [(0.0, 60), (0.0, 64), (0.0, 67), (8.0, 62), (8.0, 65),
                                                          (8.0, 69)]


def test_notes_get_window(rpc):
    result = rpc("notes.get", from_time=1.0, time_span=1.0, **BASS)
    assert [n["start"] for n in result["notes"]] == [1.0, 1.5]
    result = rpc("notes.get", from_pitch=43, pitch_span=1, **BASS)
    assert result["count"] == 1 and result["notes"][0]["pitch"] == 43
    assert rpc.err("notes.get", time_span=0, **BASS)["code"] == -32602
    assert rpc.err("notes.get", from_pitch=200, **BASS)["code"] == -32602


def test_notes_get_default_span_is_loop_end(rpc):
    rpc("notes.add", notes=[{"pitch": 60, "start": 6.0, "duration": 0.5}], **BASS)
    assert rpc("notes.get", **BASS)["count"] == 5
    assert rpc("notes.get", time_span=100.0, **BASS)["count"] == 6


def test_notes_add_then_get_roundtrip(rpc, scratch):
    specs = [
        {"pitch": 60, "start": 0.0, "duration": 0.5, "velocity": 100},
        {"pitch": 64, "start": 0.5, "duration": 0.25, "velocity": 90.5, "mute": True, "probability": 0.5,
         "velocity_deviation": 10, "release_velocity": 30},
        {"pitch": 67, "start": 1.0, "duration": 1.0},
    ]
    assert rpc("notes.add", notes=specs, **scratch) == {"added": 3, "note_count": 3}
    notes = rpc("notes.get", **scratch)["notes"]
    assert len(notes) == 3
    for spec, note in zip(specs, notes):
        for key, value in spec.items():
            assert note[key] == value, key
        assert isinstance(note["id"], int)
    assert notes[0]["mute"] is False and notes[0]["probability"] == 1.0
    assert notes[0]["velocity_deviation"] == 0.0 and notes[0]["release_velocity"] == 64.0
    assert notes[2]["velocity"] == 100.0
    assert len(set(n["id"] for n in notes)) == 3
    assert rpc("clip.get", **scratch)["note_count"] == 3


def test_notes_add_velocity_clamped_to_one(rpc, scratch):
    rpc("notes.add", notes=[{"pitch": 60, "start": 0.0, "duration": 0.5, "velocity": 0}], **scratch)
    assert rpc("notes.get", **scratch)["notes"][0]["velocity"] == 1.0


def test_notes_add_ignores_id(rpc, scratch):
    rpc("notes.add", notes=[{"id": 777, "pitch": 60, "start": 0.0, "duration": 0.5}], **scratch)
    assert rpc("notes.get", **scratch)["notes"][0]["id"] != 777


def test_notes_add_empty(rpc, scratch):
    assert rpc("notes.add", notes=[], **scratch) == {"added": 0, "note_count": 0}


def test_notes_add_invalid(rpc, scratch):
    error = rpc.err("notes.add", notes=[{"pitch": 128, "start": 0, "duration": 1}], **scratch)
    assert error["code"] == -32602 and "notes[0].pitch" in error["message"]
    error = rpc.err("notes.add", notes=[{"pitch": 60, "start": 0}], **scratch)
    assert error["code"] == -32602 and "duration" in error["message"]
    assert rpc.err("notes.add", notes=[{"pitch": 60, "start": -1, "duration": 1}], **scratch)["code"] == -32602
    assert rpc.err("notes.add", notes=[{"pitch": 60, "start": 0, "duration": 0}], **scratch)["code"] == -32602
    assert rpc.err("notes.add", notes=[{"pitch": 60, "start": 0, "duration": 1, "velocity": 200}], **scratch)["code"] == -32602
    assert rpc.err("notes.add", notes=[{"pitch": 60, "start": 0, "duration": 1, "probability": 2}], **scratch)["code"] == -32602
    assert rpc.err("notes.add", notes=[{"pitch": 60, "start": 0, "duration": 1, "mute": 1}], **scratch)["code"] == -32602
    assert rpc.err("notes.add", notes=[{"pitch": "C4", "start": 0, "duration": 1}], **scratch)["code"] == -32602
    assert rpc.err("notes.add", notes=["nope"], **scratch)["code"] == -32602
    assert rpc.err("notes.add", notes="nope", **scratch)["code"] == -32602
    assert rpc.err("notes.add", **scratch)["code"] == -32602
    assert rpc("notes.get", **scratch)["count"] == 0


def test_notes_add_too_large(rpc, scratch):
    notes = [{"pitch": 60, "start": 0.0, "duration": 0.1}] * 1001
    error = rpc.err("notes.add", notes=notes, **scratch)
    assert error["code"] == -32005 and error["data"] == {"limit": 1000, "got": 1001}
    assert rpc.err("notes.replace", notes=notes, **scratch)["code"] == -32005
    assert rpc("notes.add", notes=notes[:1000], **scratch)["added"] == 1000


def test_notes_on_audio_clip(rpc):
    error = rpc.err("notes.get", track=3, slot=0)
    assert error["code"] == -32001 and error["data"]["reason"] == "not_midi"
    assert rpc.err("notes.add", track=3, slot=0, notes=[])["data"]["reason"] == "not_midi"


def test_notes_on_empty_slot(rpc):
    error = rpc.err("notes.get", track=0, slot=3)
    assert error["code"] == -32001 and error["data"]["reason"] == "slot_empty"


def test_notes_on_arrangement_clip(rpc):
    result = rpc("notes.get", track=0, arrangement_index=0)
    assert result["count"] == 10


def test_notes_modify(rpc):
    before = rpc("notes.get", **BASS)["notes"]
    target = before[0]
    result = rpc("notes.modify", changes=[{"id": target["id"], "velocity": 50, "start": 0.25}], **BASS)
    assert result == {"modified": 1, "missing_ids": []}
    after = rpc("notes.get", **BASS)["notes"]
    moved = [n for n in after if n["id"] == target["id"]][0]
    assert moved["velocity"] == 50.0 and moved["start"] == 0.25
    assert moved["pitch"] == target["pitch"] and moved["duration"] == target["duration"]
    assert moved["mute"] == target["mute"]
    untouched_before = sorted((n["id"], n["pitch"], n["start"]) for n in before[1:])
    untouched_after = sorted((n["id"], n["pitch"], n["start"]) for n in after if n["id"] != target["id"])
    assert untouched_before == untouched_after


def test_notes_modify_several_fields(rpc):
    notes = rpc("notes.get", **BASS)["notes"]
    changes = [{"id": notes[0]["id"], "pitch": 48, "mute": True, "probability": 0.25, "release_velocity": 10,
                "velocity_deviation": -5, "duration": 0.125}]
    assert rpc("notes.modify", changes=changes, **BASS)["modified"] == 1
    changed = [n for n in rpc("notes.get", **BASS)["notes"] if n["id"] == notes[0]["id"]][0]
    assert changed["pitch"] == 48 and changed["mute"] is True and changed["probability"] == 0.25
    assert changed["release_velocity"] == 10.0 and changed["velocity_deviation"] == -5.0
    assert changed["duration"] == 0.125


def test_notes_modify_missing_and_invalid(rpc):
    result = rpc("notes.modify", changes=[{"id": 9999, "pitch": 40}], **BASS)
    assert result == {"modified": 0, "missing_ids": [9999]}
    assert rpc.err("notes.modify", changes=[{"pitch": 40}], **BASS)["code"] == -32602
    assert rpc.err("notes.modify", changes=[{"id": 1, "pitch": 200}], **BASS)["code"] == -32602
    assert rpc.err("notes.modify", changes=[{"id": 1, "duration": 0}], **BASS)["code"] == -32602
    assert rpc("notes.modify", changes=[], **BASS) == {"modified": 0, "missing_ids": []}


def test_notes_remove_by_ids(rpc):
    notes = rpc("notes.get", **BASS)["notes"]
    ids = [notes[0]["id"], notes[1]["id"]]
    assert rpc("notes.remove", note_ids=ids, **BASS) == {"removed": 2, "note_count": 3}
    remaining = [n["id"] for n in rpc("notes.get", **BASS)["notes"]]
    assert not set(ids) & set(remaining) and len(remaining) == 3
    assert rpc("notes.remove", note_ids=[424242], **BASS) == {"removed": 0, "note_count": 3}
    assert rpc.err("notes.remove", note_ids=["a"], **BASS)["code"] == -32602


def test_notes_remove_by_range(rpc):
    assert rpc("notes.remove", from_time=2.0, time_span=2.0, **BASS) == {"removed": 2, "note_count": 3}
    assert rpc("notes.remove", from_pitch=43, pitch_span=1, **BASS) == {"removed": 1, "note_count": 2}
    assert [n["pitch"] for n in rpc("notes.get", **BASS)["notes"]] == [36, 36]


def test_notes_remove_all_by_default(rpc):
    assert rpc("notes.remove", **BASS) == {"removed": 5, "note_count": 0}


def test_notes_replace(rpc):
    old_ids = set(n["id"] for n in rpc("notes.get", **BASS)["notes"])
    result = rpc("notes.replace", notes=[{"pitch": 48, "start": 0, "duration": 4}], **BASS)
    assert result == {"removed": 5, "added": 1, "note_count": 1}
    notes = rpc("notes.get", **BASS)["notes"]
    assert len(notes) == 1 and notes[0]["pitch"] == 48 and notes[0]["id"] not in old_ids


def test_notes_replace_with_empty_clears(rpc):
    assert rpc("notes.replace", notes=[], **BASS) == {"removed": 5, "added": 0, "note_count": 0}


def test_notes_quantize(rpc, scratch):
    rpc("notes.add", notes=[{"pitch": 60, "start": 0.26, "duration": 0.25},
                            {"pitch": 62, "start": 0.52, "duration": 0.25},
                            {"pitch": 64, "start": 1.01, "duration": 0.25},
                            {"pitch": 65, "start": 0.0, "duration": 0.25}], **scratch)
    assert rpc("notes.quantize", grid=0.25, **scratch) == {"modified": 3}
    starts = sorted(n["start"] for n in rpc("notes.get", **scratch)["notes"])
    assert starts == [0.0, 0.25, 0.5, 1.0]
    assert rpc("notes.quantize", grid=0.25, **scratch) == {"modified": 0}


def test_notes_quantize_amount(rpc, scratch):
    rpc("notes.add", notes=[{"pitch": 60, "start": 0.3, "duration": 0.25}], **scratch)
    rpc("notes.quantize", grid=0.25, amount=0.5, **scratch)
    assert rpc("notes.get", **scratch)["notes"][0]["start"] == pytest.approx(0.275)


def test_notes_quantize_swing(rpc, scratch):
    rpc("notes.add", notes=[{"pitch": 60, "start": 0.26, "duration": 0.2},
                            {"pitch": 62, "start": 0.52, "duration": 0.2},
                            {"pitch": 64, "start": 0.77, "duration": 0.2}], **scratch)
    assert rpc("notes.quantize", grid=0.25, swing=0.5, **scratch)["modified"] == 3
    starts = [n["start"] for n in rpc("notes.get", **scratch)["notes"]]
    # odd grid steps (1 and 3) are delayed by swing * grid / 2 = 0.0625; even step 2 is not
    assert starts == pytest.approx([0.3125, 0.5, 0.8125])


def test_notes_quantize_ends(rpc, scratch):
    rpc("notes.add", notes=[{"pitch": 60, "start": 0.26, "duration": 0.3}], **scratch)
    rpc("notes.quantize", grid=0.25, quantize_ends=True, **scratch)
    note = rpc("notes.get", **scratch)["notes"][0]
    assert note["start"] == pytest.approx(0.25) and note["duration"] == pytest.approx(0.25)


def test_notes_quantize_invalid(rpc):
    assert rpc.err("notes.quantize", grid=0, **BASS)["code"] == -32602
    assert rpc.err("notes.quantize", amount=2, **BASS)["code"] == -32602
    assert rpc.err("notes.quantize", swing=-0.1, **BASS)["code"] == -32602


def test_notes_transpose(rpc):
    original = [n["pitch"] for n in rpc("notes.get", **BASS)["notes"]]
    assert rpc("notes.transpose", semitones=12, **BASS) == {"modified": 5}
    assert [n["pitch"] for n in rpc("notes.get", **BASS)["notes"]] == [p + 12 for p in original]
    assert rpc("notes.transpose", semitones=100, **BASS) == {"modified": 5}
    assert [n["pitch"] for n in rpc("notes.get", **BASS)["notes"]] == [127] * 5
    assert rpc("notes.transpose", semitones=1, **BASS) == {"modified": 0}
    assert rpc("notes.transpose", semitones=-127, **BASS)["modified"] == 5
    assert [n["pitch"] for n in rpc("notes.get", **BASS)["notes"]] == [0] * 5
    assert rpc.err("notes.transpose", semitones=-200, **BASS)["code"] == -32602


def test_notes_transpose_range(rpc):
    assert rpc("notes.transpose", semitones=-12, from_time=2.0, time_span=2.0, **BASS) == {"modified": 2}
    notes = rpc("notes.get", **BASS)["notes"]
    assert [n["pitch"] for n in notes] == [36, 36, 43, 24, 29]


def test_notes_transpose_invalid(rpc):
    assert rpc.err("notes.transpose", semitones=1.5, **BASS)["code"] == -32602
    assert rpc.err("notes.transpose", **BASS)["code"] == -32602
    assert rpc("notes.transpose", semitones=0, **BASS) == {"modified": 0}
