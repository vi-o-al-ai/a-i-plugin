"""clip.* handlers."""
import Live

CLIP_KEYS = {"track", "slot", "arrangement_index", "name", "color_index", "color", "is_midi", "is_audio",
             "is_arrangement_clip", "length", "loop_start", "loop_end", "looping", "start_marker", "end_marker",
             "start_time", "end_time", "is_playing", "is_recording", "is_triggered", "signature_numerator",
             "signature_denominator", "note_count"}


def test_clip_create(rpc):
    clip = rpc("clip.create", track=0, slot=2, length=8.0, name="Fill")
    assert set(clip) == CLIP_KEYS
    assert clip["track"] == 0 and clip["slot"] == 2 and clip["arrangement_index"] is None
    assert clip["name"] == "Fill" and clip["is_midi"] is True and clip["is_audio"] is False
    assert clip["length"] == 8.0 and clip["loop_start"] == 0.0 and clip["loop_end"] == 8.0
    assert clip["looping"] is True and clip["start_marker"] == 0.0 and clip["end_marker"] == 8.0
    assert clip["note_count"] == 0 and clip["is_arrangement_clip"] is False
    assert clip["start_time"] is None and clip["end_time"] is None
    assert clip["signature_numerator"] == 4 and clip["color"].startswith("#")


def test_clip_create_errors(rpc):
    error = rpc.err("clip.create", track=0, slot=0, length=4.0)
    assert error["code"] == -32001 and error["data"]["reason"] == "slot_occupied"
    error = rpc.err("clip.create", track=3, slot=1, length=4.0)
    assert error["code"] == -32001 and error["data"]["reason"] == "track_not_midi"
    assert rpc.err("clip.create", track=0, slot=2, length=0)["code"] == -32602
    assert rpc.err("clip.create", track=0, slot=2)["code"] == -32602
    error = rpc.err("clip.create", track=0, slot=99, length=4.0)
    assert error["data"] == {"kind": "slot", "index": 99, "count": 8}
    assert rpc.err("clip.create", track=0, track_type="return", slot=0, length=4.0)["code"] == -32001


def test_clip_get_session(rpc):
    clip = rpc("clip.get", track=1, slot=0)
    assert clip["name"] == "Bass 1" and clip["note_count"] == 5
    assert clip["length"] == 4.0 and clip["is_playing"] is False


def test_clip_get_audio(rpc):
    clip = rpc("clip.get", track=3, slot=0)
    assert clip["is_audio"] is True and clip["is_midi"] is False and clip["note_count"] is None
    assert clip["name"] == "Vox Take 1"


def test_clip_get_arrangement(rpc):
    clip = rpc("clip.get", track=0, arrangement_index=1)
    assert clip["name"] == "Drums 2" and clip["is_arrangement_clip"] is True
    assert clip["slot"] is None and clip["arrangement_index"] == 1
    assert clip["start_time"] == 8.0 and clip["end_time"] == 16.0


def test_clip_address_validation(rpc):
    assert rpc.err("clip.get", track=0)["code"] == -32602
    assert rpc.err("clip.get", track=0, slot=0, arrangement_index=0)["code"] == -32602
    error = rpc.err("clip.get", track=0, arrangement_index=5)
    assert error["code"] == -32000 and error["data"] == {"kind": "arrangement_clip", "index": 5, "count": 2}
    error = rpc.err("clip.get", track=0, slot=3)
    assert error["code"] == -32001 and error["data"]["reason"] == "slot_empty"
    assert rpc.err("clip.get", track=0, slot=-1)["code"] == -32602


def test_clip_set_loop_order(rpc):
    clip = rpc("clip.set", track=1, slot=0, loop_start=4.0, loop_end=8.0)
    assert clip["loop_start"] == 4.0 and clip["loop_end"] == 8.0 and clip["length"] == 4.0


def test_clip_set_loop_earlier(rpc):
    rpc("clip.set", track=1, slot=0, loop_start=4.0, loop_end=8.0)
    clip = rpc("clip.set", track=1, slot=0, loop_start=0.0, loop_end=2.0)
    assert clip["loop_start"] == 0.0 and clip["loop_end"] == 2.0


def test_clip_set_fields(rpc, fake_live):
    clip = rpc("clip.set", track=1, slot=0, name="Bass A", color_index=5, looping=False, start_marker=1.0,
               end_marker=3.0, launch_quantization="q_bar")
    assert clip["name"] == "Bass A" and clip["color_index"] == 5
    assert clip["looping"] is False and clip["start_marker"] == 1.0 and clip["end_marker"] == 3.0
    assert clip["length"] == 2.0
    live_clip = fake_live.song.tracks[1].clip_slots[0].clip
    assert live_clip.launch_quantization == Live.Clip.ClipLaunchQuantization.q_bar
    assert rpc("clip.set", track=1, slot=0, launch_quantization="quarter")["name"] == "Bass A"
    assert live_clip.launch_quantization == Live.Clip.ClipLaunchQuantization.q_quarter


def test_clip_set_invalid(rpc):
    assert rpc.err("clip.set", track=1, slot=0, loop_start=8.0, loop_end=4.0)["code"] == -32602
    assert rpc.err("clip.set", track=1, slot=0, start_marker=3.0, end_marker=3.0)["code"] == -32602
    error = rpc.err("clip.set", track=1, slot=0, launch_quantization="weird")
    assert error["code"] == -32602 and "q_bar" in error["data"]["available"]
    assert rpc.err("clip.set", track=1, slot=0, color_index=-1)["code"] == -32602
    # Live itself refuses loop_start >= loop_end: surfaced as LIVE_ERROR.
    error = rpc.err("clip.set", track=1, slot=0, loop_start=4.0)
    assert error["code"] == -32004 and error["data"]["exception"] == "RuntimeError"


PUBLIC_QUANTIZATIONS = (
    "q_global", "q_none", "q_8_bars", "q_4_bars", "q_2_bars", "q_bar", "q_half", "q_half_triplet", "q_quarter",
    "q_quarter_triplet", "q_eight", "q_eight_triplet", "q_sixteenth", "q_sixteenth_triplet", "q_thirtysecond",
)


def test_launch_quantization_public_names_resolve_to_live_spellings(rpc, fake_live):
    enum = Live.Clip.ClipLaunchQuantization
    live_clip = fake_live.song.tracks[1].clip_slots[0].clip
    # The mock enum carries Ableton's historical misspellings; the public names must still work.
    assert not hasattr(enum, "q_sixteenth") and hasattr(enum, "q_sixtenth")
    expected = {"q_sixteenth": enum.q_sixtenth, "q_sixteenth_triplet": enum.q_sixtenth_triplet,
                "q_thirtysecond": enum.q_thirtytwoth}
    for name in PUBLIC_QUANTIZATIONS:
        rpc("clip.set", track=1, slot=0, launch_quantization=name)
        member = expected[name] if name in expected else getattr(enum, name)
        assert live_clip.launch_quantization == member, name
    # The historical spellings are accepted as input too.
    rpc("clip.set", track=1, slot=0, launch_quantization="q_thirtytwoth")
    assert live_clip.launch_quantization == enum.q_thirtytwoth
    error = rpc.err("clip.set", track=1, slot=0, launch_quantization="q_sixtyfourth")
    assert error["code"] == -32602 and error["data"]["available"] == list(PUBLIC_QUANTIZATIONS)


def test_launch_quantization_unsupported_when_live_lacks_member(rpc, monkeypatch):
    from Live import _core
    reduced = _core.make_enum("Live.Clip.ClipLaunchQuantization", ("q_global", "q_none", "q_bar"))
    monkeypatch.setattr(Live.Clip, "ClipLaunchQuantization", reduced)
    assert rpc("clip.set", track=1, slot=0, launch_quantization="q_bar")["name"] == "Bass 1"
    error = rpc.err("clip.set", track=1, slot=0, launch_quantization="q_sixteenth")
    assert error["code"] == -32003
    assert error["data"]["needs"] == "Live.Clip.ClipLaunchQuantization.q_sixteenth"
    assert "q_sixtenth" in error["message"]
    monkeypatch.setattr(Live.Clip, "ClipLaunchQuantization", None)
    assert rpc.err("clip.set", track=1, slot=0, launch_quantization="q_bar")["code"] == -32003


def test_clip_set_rejects_conflicting_pairs_on_unlooped_clips(rpc, fake_live):
    live_clip = fake_live.song.tracks[1].clip_slots[0].clip
    error = rpc.err("clip.set", track=1, slot=0, looping=False, loop_start=0.0, loop_end=2.0,
                    start_marker=0.0, end_marker=2.0)
    assert error["code"] == -32602 and error["data"]["reason"] == "loop_marker_alias"
    assert "alias" in error["message"]
    assert live_clip.looping is True  # rejected before touching Live
    # A clip that is already unlooped trips the same check without an explicit `looping`.
    rpc("clip.set", track=1, slot=0, looping=False)
    assert rpc.err("clip.set", track=1, slot=0, loop_end=2.0, end_marker=2.0)["code"] == -32602
    # One pair at a time is fine on an unlooped clip ...
    assert rpc("clip.set", track=1, slot=0, start_marker=1.0, end_marker=3.0)["end_marker"] == 3.0
    assert rpc("clip.set", track=1, slot=0, loop_start=0.0, loop_end=2.0)["loop_end"] == 2.0
    # ... and both pairs are independent (and allowed) once the clip loops again.
    clip = rpc("clip.set", track=1, slot=0, looping=True, loop_start=0.0, loop_end=4.0, start_marker=0.0,
               end_marker=4.0)
    assert clip["looping"] is True and clip["loop_end"] == 4.0 and clip["end_marker"] == 4.0


def test_clip_set_arrangement_clip(rpc):
    clip = rpc("clip.set", track=0, arrangement_index=0, name="Intro Drums")
    assert clip["name"] == "Intro Drums" and clip["arrangement_index"] == 0


def test_clip_fire_and_stop(rpc, fake_live):
    clip = rpc("clip.fire", track=0, slot=0)
    assert clip["is_playing"] is True and clip["slot"] == 0
    assert fake_live.song.tracks[0].playing_slot_index == 0
    assert rpc("clip.stop", track=0, slot=0) == {"ok": True}
    assert fake_live.song.tracks[0].playing_slot_index == -1
    rpc("clip.fire", track=0, slot=1)
    assert rpc("clip.stop", track=0) == {"ok": True}
    assert fake_live.song.tracks[0].playing_slot_index == -1


def test_clip_fire_empty_slot_stops_track(rpc, fake_live):
    rpc("clip.fire", track=0, slot=0)
    result = rpc("clip.fire", track=0, slot=3)
    assert result["fired_empty_slot"] is True
    assert fake_live.song.tracks[0].playing_slot_index == -1


def test_clip_duplicate_same_track(rpc):
    copy = rpc("clip.duplicate", track=1, slot=0, target_slot=3)
    assert copy["track"] == 1 and copy["slot"] == 3 and copy["name"] == "Bass 1" and copy["note_count"] == 5
    assert rpc("clip.get", track=1, slot=0)["name"] == "Bass 1"


def test_clip_duplicate_other_track(rpc):
    copy = rpc("clip.duplicate", track=1, slot=0, target_track=5, target_slot=0)
    assert copy["track"] == 5 and copy["slot"] == 0 and copy["note_count"] == 5


def test_clip_duplicate_errors(rpc):
    error = rpc.err("clip.duplicate", track=1, slot=0, target_slot=1)
    assert error["code"] == -32001 and error["data"]["reason"] == "slot_occupied"
    error = rpc.err("clip.duplicate", track=1, slot=0, target_track=3, target_slot=1)
    assert error["code"] == -32001 and error["data"]["reason"] == "track_type_mismatch"
    error = rpc.err("clip.duplicate", track=0, slot=3, target_slot=4)
    assert error["code"] == -32001 and error["data"]["reason"] == "slot_empty"
    assert rpc.err("clip.duplicate", track=1, slot=0)["code"] == -32602
    assert rpc.err("clip.duplicate", track=1, slot=0, target_track=9, target_slot=0)["code"] == -32000


def test_clip_duplicate_loop(rpc):
    clip = rpc("clip.duplicate_loop", track=1, slot=0)
    assert clip["length"] == 8.0 and clip["loop_end"] == 8.0 and clip["note_count"] == 10
    starts = [n["start"] for n in rpc("notes.get", track=1, slot=0)["notes"]]
    assert 4.0 in starts and 7.0 in starts
    assert rpc.err("clip.duplicate_loop", track=0, arrangement_index=0)["code"] == -32602


def test_clip_delete(rpc, fake_live):
    error = rpc.err("clip.delete", track=1, slot=0)
    assert error["code"] == -32002
    assert error["data"]["method"] == "clip.delete" and "Bass 1" in error["data"]["target"]
    assert rpc("clip.delete", track=1, slot=0, confirm=True) == {"deleted": "Bass 1"}
    assert fake_live.song.tracks[1].clip_slots[0].has_clip is False
    assert rpc.err("clip.delete", track=1, slot=0, confirm=True)["data"]["reason"] == "slot_empty"


def test_clip_delete_arrangement(rpc, fake_live):
    assert rpc("clip.delete", track=0, arrangement_index=0, confirm=True) == {"deleted": "Drums 1"}
    assert len(fake_live.song.tracks[0].arrangement_clips) == 1
    assert fake_live.song.tracks[0].arrangement_clips[0].name == "Drums 2"
