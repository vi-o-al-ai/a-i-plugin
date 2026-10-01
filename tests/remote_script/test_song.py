"""song.* handlers."""
TRACK_KEYS = {"index", "track_type", "name", "type", "color_index", "color", "mute", "solo", "arm", "can_be_armed",
              "is_foldable", "is_grouped", "group_track_index", "volume", "pan", "sends", "playing_slot_index",
              "fired_slot_index", "clip_count", "device_count"}
SCENE_KEYS = {"index", "name", "color_index", "color", "is_triggered", "tempo", "is_empty"}
TRANSPORT_KEYS = {"tempo", "signature_numerator", "signature_denominator", "is_playing", "position", "loop",
                  "metronome", "record_mode", "session_record", "song_length"}


def test_get_overview_shape(rpc):
    overview = rpc("song.get_overview")
    assert set(overview) == {"transport", "scale", "tracks", "return_tracks", "master", "scenes", "selection",
                             "live_version"}
    assert overview["live_version"] == "12.1.5"
    assert set(overview["transport"]) == TRANSPORT_KEYS
    assert overview["scale"] == {"root_note": 0, "root_name": "C", "scale_name": "Major",
                                 "scale_intervals": [0, 2, 4, 5, 7, 9, 11]}

    tracks = overview["tracks"]
    assert [t["name"] for t in tracks] == ["Drums", "Bass", "Pad", "Vox", "Synths", "Lead"]
    drums = tracks[0]
    assert TRACK_KEYS | {"clips", "devices"} <= set(drums)
    assert drums["index"] == 0 and drums["track_type"] == "track" and drums["type"] == "midi"
    assert drums["clip_count"] == 2 and drums["device_count"] == 2
    assert drums["color_index"] == 1 and drums["color"].startswith("#") and len(drums["color"]) == 7
    assert drums["volume"] == {"value": 0.85, "display": "0.0 dB"}
    assert drums["pan"] == {"value": 0.0, "display": "C"}
    assert drums["sends"] == [{"index": 0, "name": "A-Reverb", "value": 0.0, "display": "-inf dB"},
                              {"index": 1, "name": "B-Delay", "value": 0.0, "display": "-inf dB"}]
    assert drums["playing_slot_index"] == -1 and drums["fired_slot_index"] == -1
    assert [c["name"] for c in drums["clips"]] == ["Drums 1", "Drums 2"]
    assert drums["clips"][1]["slot"] == 1
    assert drums["devices"][0]["is_rack"] is True and "chains" in drums["devices"][0]
    assert "parameters" not in drums["devices"][0]

    assert tracks[3]["type"] == "audio" and tracks[3]["can_be_armed"] is True
    assert tracks[4]["type"] == "group" and tracks[4]["is_foldable"] is True and tracks[4]["can_be_armed"] is False
    assert tracks[5]["is_grouped"] is True and tracks[5]["group_track_index"] == 4

    returns = overview["return_tracks"]
    assert [r["name"] for r in returns] == ["A-Reverb", "B-Delay"]
    assert returns[0]["track_type"] == "return" and returns[0]["type"] == "return" and returns[0]["index"] == 0
    assert returns[0]["devices"][0]["name"] == "Reverb"
    assert "clips" not in returns[0]

    master = overview["master"]
    assert master["track_type"] == "master" and master["type"] == "master"
    assert master["device_count"] == 1 and master["devices"][0]["name"] == "Limiter"
    assert master["sends"] == []

    scenes = overview["scenes"]
    assert len(scenes) == 8
    assert set(scenes[0]) == SCENE_KEYS
    assert scenes[0]["name"] == "Intro" and scenes[0]["is_empty"] is False and scenes[0]["tempo"] is None
    assert scenes[7]["is_empty"] is True

    assert overview["selection"]["track"]["name"] == "Bass"


def test_get_overview_flags(rpc):
    overview = rpc("song.get_overview", include_clips=False, include_devices=False, include_returns=False)
    assert "clips" not in overview["tracks"][0]
    assert "devices" not in overview["tracks"][0]
    assert overview["return_tracks"] == []
    assert "devices" not in overview["master"]


def test_get_overview_include_params(rpc):
    overview = rpc("song.get_overview", include_params=True)
    params = overview["tracks"][1]["devices"][0]["parameters"]
    assert params[0]["name"] == "Device On"
    assert overview["return_tracks"][0]["devices"][0]["parameters"][1]["name"] == "Decay Time"


def test_get_transport(rpc):
    transport = rpc("song.get_transport")
    assert set(transport) == TRANSPORT_KEYS
    assert transport["tempo"] == 120.0
    assert transport["signature_numerator"] == 4 and transport["signature_denominator"] == 4
    assert transport["is_playing"] is False and transport["position"] == 0.0
    assert transport["loop"] == {"enabled": False, "start": 0.0, "length": 16.0}
    assert transport["song_length"] == 16.0


def test_set_transport(rpc, fake_live):
    transport = rpc("song.set_transport", tempo=124.5, metronome=True, loop_enabled=True, loop_start=8.0,
                    loop_length=8.0, signature_numerator=3, signature_denominator=8, position=4.0,
                    record_mode=True, session_record=True)
    assert transport["tempo"] == 124.5
    assert transport["metronome"] is True
    assert transport["loop"] == {"enabled": True, "start": 8.0, "length": 8.0}
    assert transport["signature_numerator"] == 3 and transport["signature_denominator"] == 8
    assert transport["position"] == 4.0
    assert transport["record_mode"] is True and transport["session_record"] is True
    assert fake_live.song.tempo == 124.5


def test_set_transport_invalid(rpc):
    assert rpc.err("song.set_transport", tempo=5)["code"] == -32602
    error = rpc.err("song.set_transport", signature_denominator=3)
    assert error["code"] == -32602 and error["data"]["available"] == [1, 2, 4, 8, 16]
    assert rpc.err("song.set_transport", loop_length=0)["code"] == -32602
    assert rpc.err("song.set_transport", tempo="fast")["code"] == -32602
    assert rpc.err("song.set_transport", metronome="yes")["code"] == -32602


def test_play_stop_continue(rpc, fake_live):
    fake_live.song.current_song_time = 8.0
    transport = rpc("song.play")
    assert transport["is_playing"] is True and transport["position"] == 8.0
    assert rpc("song.stop")["is_playing"] is False
    assert rpc("song.continue")["is_playing"] is True
    transport = rpc("song.play", from_start=True)
    assert transport["is_playing"] is True and transport["position"] == 0.0


def test_stop_all_clips(rpc, fake_live):
    rpc("clip.fire", track=0, slot=0)
    assert fake_live.song.tracks[0].playing_slot_index == 0
    assert rpc("song.stop_all_clips") == {"ok": True}
    assert fake_live.song.tracks[0].playing_slot_index == -1


def test_scale_get_and_set(rpc):
    assert rpc("song.get_scale") == {"root_note": 0, "root_name": "C", "scale_name": "Major",
                                     "scale_intervals": [0, 2, 4, 5, 7, 9, 11]}
    scale = rpc("song.set_scale", root_note="D", scale_name="minor")
    assert scale == {"root_note": 2, "root_name": "D", "scale_name": "Minor",
                     "scale_intervals": [0, 2, 3, 5, 7, 8, 10]}
    scale = rpc("song.set_scale", root_note=7)
    assert scale["root_name"] == "G" and scale["scale_name"] == "Minor"
    assert rpc("song.set_scale", root_note="Bb")["root_note"] == 10


def test_set_scale_invalid(rpc):
    error = rpc.err("song.set_scale", scale_name="Klingon")
    assert error["code"] == -32602
    assert "Major" in error["data"]["available"] and "Hirajoshi" in error["data"]["available"]
    assert rpc.err("song.set_scale", root_note=12)["code"] == -32602
    assert rpc.err("song.set_scale", root_note="H")["code"] == -32602
    assert rpc.err("song.set_scale")["code"] == -32602


def test_scale_unsupported_when_api_missing(rpc, fake_live):
    del fake_live.song.scale_name
    error = rpc.err("song.get_scale")
    assert error["code"] == -32003
    assert error["data"]["have"] == "12.1.5" and "scale" in error["data"]["needs"]
    assert rpc.err("song.set_scale", scale_name="Minor")["code"] == -32003
    assert rpc("song.get_overview")["scale"] is None


def test_undo_redo(rpc, fake_live):
    assert rpc("song.undo") == {"ok": True}
    assert fake_live.song.undo_count == 1
    assert rpc("song.redo") == {"ok": True}
    assert fake_live.song.redo_count == 1


def test_create_midi_track(rpc, fake_live):
    track = rpc("song.create_midi_track", name="Keys")
    assert TRACK_KEYS <= set(track)
    assert track["index"] == 6 and track["name"] == "Keys" and track["type"] == "midi"
    assert len(fake_live.song.tracks) == 7
    assert rpc("view.get_selection")["track"]["name"] == "Keys"
    assert len(track["sends"]) == 2


def test_create_midi_track_at_index(rpc):
    track = rpc("song.create_midi_track", index=1, name="Perc")
    assert track["index"] == 1
    assert rpc("track.get", track=2)["name"] == "Bass"


def test_create_audio_track(rpc):
    track = rpc("song.create_audio_track", name="Guitar")
    assert track["type"] == "audio" and track["can_be_armed"] is True and track["index"] == 6


def test_create_return_track(rpc):
    track = rpc("song.create_return_track", name="C-Chorus")
    assert track["track_type"] == "return" and track["type"] == "return" and track["index"] == 2
    assert track["name"] == "C-Chorus"
    sends = rpc("track.get", track=0)["sends"]
    assert len(sends) == 3 and sends[2]["name"] == "C-Chorus"


def test_create_track_bad_index(rpc):
    assert rpc.err("song.create_midi_track", index=99)["code"] == -32602
    assert rpc.err("song.create_midi_track", index=-2)["code"] == -32602


def test_delete_track_requires_confirm(rpc, fake_live):
    error = rpc.err("song.delete_track", track=1)
    assert error["code"] == -32002
    assert error["data"] == {"method": "song.delete_track", "target": "Bass (track 1)"}
    assert len(fake_live.song.tracks) == 6
    assert rpc.err("song.delete_track", track=1, confirm="yes")["code"] == -32002


def test_delete_track(rpc, fake_live):
    result = rpc("song.delete_track", track=1, confirm=True)
    assert result["deleted"] == "Bass" and result["track_count"] == 5
    assert [t.name for t in fake_live.song.tracks] == ["Drums", "Pad", "Vox", "Synths", "Lead"]


def test_delete_return_track(rpc):
    result = rpc("song.delete_track", track=0, track_type="return", confirm=True)
    assert result["deleted"] == "A-Reverb" and result["track_count"] == 1
    assert len(rpc("track.get", track=0)["sends"]) == 1


def test_delete_master_rejected(rpc):
    assert rpc.err("song.delete_track", track_type="master", confirm=True)["code"] == -32001


def test_track_not_found_has_count(rpc):
    error = rpc.err("track.get", track=9)
    assert error["code"] == -32000
    assert error["data"] == {"kind": "track", "index": 9, "count": 6}
    assert "Track 9" in error["message"] and "6" in error["message"]
    error = rpc.err("track.get", track=2, track_type="return")
    assert error["data"] == {"kind": "return_track", "index": 2, "count": 2}
    assert rpc.err("track.get", track="one")["code"] == -32602
    assert rpc.err("track.get")["code"] == -32602


def test_create_scene(rpc, fake_live):
    scene = rpc("song.create_scene", name="Drop")
    assert set(scene) == SCENE_KEYS
    assert scene["index"] == 8 and scene["name"] == "Drop" and scene["is_empty"] is True
    assert len(fake_live.song.scenes) == 9
    assert all(len(t.clip_slots) == 9 for t in fake_live.song.tracks)


def test_create_scene_at_index_shifts_slots(rpc):
    scene = rpc("song.create_scene", index=0, name="Count-in")
    assert scene["index"] == 0
    assert rpc("song.get_overview")["scenes"][1]["name"] == "Intro"
    assert rpc("clip.get", track=0, slot=1)["name"] == "Drums 1"


def test_duplicate_scene(rpc):
    scene = rpc("song.duplicate_scene", scene=0)
    assert scene["index"] == 1 and scene["name"] == "Intro"
    copy = rpc("clip.get", track=0, slot=1)
    assert copy["name"] == "Drums 1" and copy["note_count"] == 10
    assert rpc("clip.get", track=0, slot=2)["name"] == "Drums 2"
    assert rpc.err("song.duplicate_scene", scene=50)["code"] == -32000


def test_delete_scene(rpc):
    error = rpc.err("song.delete_scene", scene=0)
    assert error["code"] == -32002 and error["data"]["target"] == "Intro (scene 0)"
    assert rpc("song.delete_scene", scene=0, confirm=True) == {"deleted": "Intro", "scene_count": 7}
    assert rpc("clip.get", track=0, slot=0)["name"] == "Drums 2"


def test_scene_not_found(rpc):
    error = rpc.err("song.delete_scene", scene=20, confirm=True)
    assert error["code"] == -32000 and error["data"] == {"kind": "scene", "index": 20, "count": 8}
