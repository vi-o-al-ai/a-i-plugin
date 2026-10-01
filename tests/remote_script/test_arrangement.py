"""arrangement.* handlers."""


def test_get_overview_shape(rpc):
    overview = rpc("arrangement.get_overview")
    assert set(overview) == {"song_length", "loop", "locators", "tracks"}
    assert overview["song_length"] == 16.0
    assert overview["loop"] == {"enabled": False, "start": 0.0, "length": 16.0}
    assert overview["locators"] == [{"index": 0, "name": "Drop", "time": 64.0}]
    assert len(overview["tracks"]) == 6
    drums = overview["tracks"][0]
    assert set(drums) == {"index", "name", "clips"}
    assert drums["index"] == 0 and drums["name"] == "Drums"
    clips = drums["clips"]
    assert [(c["start_time"], c["end_time"]) for c in clips] == [(0.0, 4.0), (8.0, 16.0)]
    assert [c["arrangement_index"] for c in clips] == [0, 1]
    assert all(c["is_arrangement_clip"] for c in clips) and all(c["slot"] is None for c in clips)
    # Counting notes is expensive: list-style methods leave note_count null unless asked.
    assert clips[0]["name"] == "Drums 1" and clips[0]["note_count"] is None
    assert overview["tracks"][1]["clips"] == []


def test_get_overview_include_note_counts(rpc):
    overview = rpc("arrangement.get_overview", include_note_counts=True)
    assert [c["note_count"] for c in overview["tracks"][0]["clips"]] == [10, 8]
    assert rpc.err("arrangement.get_overview", include_note_counts="yes")["code"] == -32602


def test_get_overview_without_clips(rpc):
    overview = rpc("arrangement.get_overview", include_clips=False)
    assert overview["tracks"][0]["clip_count"] == 2 and "clips" not in overview["tracks"][0]


def test_get_clips(rpc):
    clips = rpc("arrangement.get_clips", track=0)["clips"]
    assert len(clips) == 2 and all(c["note_count"] is None for c in clips)
    counted = rpc("arrangement.get_clips", track=0, include_note_counts=True)["clips"]
    assert [c["note_count"] for c in counted] == [10, 8]
    assert rpc("arrangement.get_clips", track=1) == {"clips": []}
    assert rpc("arrangement.get_clips", track_type="master") == {"clips": []}
    assert rpc.err("arrangement.get_clips", track=9)["code"] == -32000


def test_add_clip_from_slot(rpc, fake_live):
    clip = rpc("arrangement.add_clip_from_slot", track=1, slot=0, time=16.0)
    assert clip["is_arrangement_clip"] is True and clip["track"] == 1 and clip["slot"] is None
    assert clip["arrangement_index"] == 0
    assert clip["start_time"] == 16.0 and clip["end_time"] == 20.0 and clip["length"] == 4.0
    assert clip["name"] == "Bass 1" and clip["note_count"] == 5
    assert fake_live.song.tracks[1].clip_slots[0].has_clip is True
    assert rpc("song.get_transport")["song_length"] == 20.0
    assert rpc("notes.get", track=1, arrangement_index=0)["count"] == 5


def test_add_clip_from_slot_delete_source_requires_confirm(rpc, fake_live):
    error = rpc.err("arrangement.add_clip_from_slot", track=1, slot=1, time=0.0, delete_source=True)
    assert error["code"] == -32002
    assert error["data"]["method"] == "arrangement.add_clip_from_slot" and "Bass 2" in error["data"]["target"]
    # Nothing happened: neither the copy nor the delete.
    assert fake_live.song.tracks[1].clip_slots[1].has_clip is True
    assert len(fake_live.song.tracks[1].arrangement_clips) == 0
    assert rpc.err("arrangement.add_clip_from_slot", track=1, slot=1, time=0.0, delete_source=True,
                   confirm="yes")["code"] == -32002


def test_add_clip_from_slot_delete_source(rpc, fake_live):
    clip = rpc("arrangement.add_clip_from_slot", track=1, slot=1, time=0.0, delete_source=True, confirm=True)
    assert clip["start_time"] == 0.0 and clip["name"] == "Bass 2"
    assert fake_live.song.tracks[1].clip_slots[1].has_clip is False
    assert len(fake_live.song.tracks[1].arrangement_clips) == 1
    # Without delete_source no confirm is needed.
    rpc("arrangement.add_clip_from_slot", track=1, slot=0, time=8.0, delete_source=False)
    assert fake_live.song.tracks[1].clip_slots[0].has_clip is True


def test_add_clip_index_follows_time_order(rpc):
    first = rpc("arrangement.add_clip_from_slot", track=1, slot=0, time=16.0)
    assert first["arrangement_index"] == 0
    second = rpc("arrangement.add_clip_from_slot", track=1, slot=1, time=0.0)
    assert second["arrangement_index"] == 0
    clips = rpc("arrangement.get_clips", track=1)["clips"]
    assert [c["name"] for c in clips] == ["Bass 2", "Bass 1"]


def test_add_clip_from_slot_errors(rpc):
    error = rpc.err("arrangement.add_clip_from_slot", track=0, slot=3, time=0.0)
    assert error["code"] == -32001 and error["data"]["reason"] == "slot_empty"
    assert rpc.err("arrangement.add_clip_from_slot", track=0, slot=0, time=-1.0)["code"] == -32602
    assert rpc.err("arrangement.add_clip_from_slot", track=0, slot=0)["code"] == -32602
    assert rpc.err("arrangement.add_clip_from_slot", track=0, track_type="return", slot=0, time=0.0)["code"] == -32001
    assert rpc.err("arrangement.add_clip_from_slot", track=0, slot=99, time=0.0)["code"] == -32000


def test_set_locator_creates_and_renames(rpc, fake_live):
    fake_live.song.current_song_time = 3.0
    cue = rpc("arrangement.set_locator", time=32.0, name="Chorus")
    assert cue == {"index": 0, "name": "Chorus", "time": 32.0}
    assert [c.name for c in fake_live.song.cue_points] == ["Chorus", "Drop"]
    assert fake_live.song.current_song_time == 3.0  # playhead restored
    renamed = rpc("arrangement.set_locator", time=32.0, name="Chorus 2")
    assert renamed == {"index": 0, "name": "Chorus 2", "time": 32.0}
    assert len(fake_live.song.cue_points) == 2
    unnamed = rpc("arrangement.set_locator", time=96.0)
    assert unnamed["index"] == 2 and unnamed["time"] == 96.0 and unnamed["name"]
    assert rpc("arrangement.get_overview")["locators"][2]["name"] == unnamed["name"]


def test_locators_refused_while_playing(rpc, fake_live):
    fake_live.song.current_song_time = 10.0
    fake_live.song.start_playing()
    error = rpc.err("arrangement.set_locator", time=40.0, name="Break")
    assert error["code"] == -32001 and error["data"]["reason"] == "transport_running"
    assert error["message"] == "Stop playback first: creating or deleting a locator moves the playhead."
    assert fake_live.song.current_song_time == 10.0  # the playhead was never touched
    assert [c.name for c in fake_live.song.cue_points] == ["Drop"]
    error = rpc.err("arrangement.delete_locator", index=0)
    assert error["code"] == -32001 and error["data"]["reason"] == "transport_running"
    assert len(fake_live.song.cue_points) == 1 and fake_live.song.current_song_time == 10.0
    # Renaming an existing locator does not move the playhead, so it is allowed while playing.
    assert rpc("arrangement.set_locator", time=64.0, name="The Drop")["name"] == "The Drop"
    fake_live.song.stop_playing()
    assert rpc("arrangement.set_locator", time=40.0, name="Break")["time"] == 40.0
    assert fake_live.song.current_song_time == 10.0


def test_set_locator_invalid(rpc):
    assert rpc.err("arrangement.set_locator", time=-4.0)["code"] == -32602
    assert rpc.err("arrangement.set_locator", name="x")["code"] == -32602


def test_delete_locator(rpc, fake_live):
    fake_live.song.current_song_time = 2.0
    assert rpc("arrangement.delete_locator", index=0) == {"deleted": "Drop", "time": 64.0}
    assert fake_live.song.cue_points == ()
    assert fake_live.song.current_song_time == 2.0
    error = rpc.err("arrangement.delete_locator", index=0)
    assert error["code"] == -32000 and error["data"] == {"kind": "cue_point", "index": 0, "count": 0}
    assert rpc.err("arrangement.delete_locator")["code"] == -32602
