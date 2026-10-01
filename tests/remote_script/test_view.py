"""view.* handlers."""
SELECTION_KEYS = {"track", "scene", "clip_slot", "detail_clip", "device", "parameter"}


def test_get_selection_shape(rpc):
    selection = rpc("view.get_selection")
    assert set(selection) == SELECTION_KEYS
    assert selection["track"] == {"index": 1, "track_type": "track", "name": "Bass"}
    assert selection["scene"] == {"index": 0, "name": "Intro"}
    assert selection["clip_slot"] == {"track": 1, "slot": 0, "has_clip": True, "clip_name": "Bass 1"}
    assert selection["detail_clip"] is None
    assert selection["device"] == {"path": "0", "name": "Operator"}
    assert selection["parameter"] is None


def test_select_track_and_scene(rpc):
    selection = rpc("view.select", track=0, scene=2)
    assert selection["track"]["name"] == "Drums"
    assert selection["scene"] == {"index": 2, "name": "Chorus 1"}
    assert selection["clip_slot"] == {"track": 0, "slot": 2, "has_clip": False, "clip_name": None}
    assert selection["device"] == {"path": "1", "name": "Compressor"}


def test_select_slot_selects_track_and_scene(rpc, fake_live):
    selection = rpc("view.select", track=2, slot=0, show_clip_detail=True)
    assert selection["track"]["name"] == "Pad"
    assert selection["scene"]["index"] == 0
    assert selection["clip_slot"] == {"track": 2, "slot": 0, "has_clip": True, "clip_name": "Pad 1"}
    assert selection["detail_clip"] == {"track": 2, "slot": 0, "name": "Pad 1"}
    assert fake_live.app.view.is_view_visible("Detail/Clip") is True


def test_select_device(rpc, fake_live):
    selection = rpc("view.select", track=2, device_path="2/1/0", show_device_detail=True)
    assert selection["device"] == {"path": "2/1/0", "name": "Wavetable"}
    assert "Detail/DeviceChain" in fake_live.app.view.shown
    assert fake_live.song.view.appointed_device is fake_live.song.tracks[2].devices[2].chains[1].devices[0]


def test_select_return_and_master(rpc):
    selection = rpc("view.select", track=1, track_type="return")
    assert selection["track"] == {"index": 1, "track_type": "return", "name": "B-Delay"}
    assert selection["clip_slot"] is None
    selection = rpc("view.select", track_type="master")
    assert selection["track"] == {"index": 0, "track_type": "master", "name": "Master"}
    assert selection["device"] == {"path": "0", "name": "Limiter"}


def test_select_validation(rpc):
    assert rpc.err("view.select", slot=0)["code"] == -32602
    assert rpc.err("view.select", device_path="0")["code"] == -32602
    assert rpc.err("view.select", track=0, track_type="return", slot=0)["code"] == -32001
    assert rpc.err("view.select", track=0, device_path="mixer")["code"] == -32602
    assert rpc.err("view.select", track=0, slot=99)["data"] == {"kind": "slot", "index": 99, "count": 8}
    assert rpc.err("view.select", scene=99)["code"] == -32000


def test_show_view(rpc, fake_live):
    assert rpc("view.show_view", view="Arranger") == {"view": "Arranger", "visible": True}
    assert fake_live.app.view.focused_document_view == "Arranger"
    assert rpc("view.show_view", view="Session")["visible"] is True
    error = rpc.err("view.show_view", view="Mixer")
    assert error["code"] == -32602 and "Detail/Clip" in error["data"]["available"]
    assert rpc.err("view.show_view")["code"] == -32602


def test_selected_parameter_reports_owner(rpc, fake_live):
    bass = fake_live.song.tracks[1]
    fake_live.song.view.selected_parameter = bass.devices[0].parameters[4]
    assert rpc("view.get_selection")["parameter"] == {"name": "Filter Freq", "device_path": "0"}
    fake_live.song.view.selected_parameter = bass.mixer_device.volume
    assert rpc("view.get_selection")["parameter"] == {"name": "Volume", "device_path": "mixer"}


def test_detail_clip_arrangement(rpc, fake_live):
    fake_live.song.view.detail_clip = fake_live.song.tracks[0].arrangement_clips[1]
    detail = rpc("view.get_selection")["detail_clip"]
    assert detail == {"track": 0, "slot": None, "name": "Drums 2", "arrangement_index": 1}
