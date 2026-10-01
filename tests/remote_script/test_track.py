"""track.* handlers."""
from Live import _core


def test_track_get_shape(rpc):
    track = rpc("track.get", track=0)
    assert track["name"] == "Drums" and track["index"] == 0
    assert [c["slot"] for c in track["clips"]] == [0, 1]
    assert track["clips"][0]["track"] == 0 and track["clips"][0]["arrangement_index"] is None
    assert track["devices"][1]["name"] == "Compressor"
    rack = track["devices"][0]
    assert rack["chains"][0]["devices"][0]["path"] == "0/0/0"
    assert rack["chains"][0]["devices"][0]["name"] == "Kick 909"
    assert "parameters" not in rack


def test_track_get_without_children(rpc):
    track = rpc("track.get", track=0, include_clips=False, include_devices=False)
    assert "clips" not in track and "devices" not in track


def test_track_get_include_note_counts(rpc):
    track = rpc("track.get", track=0)
    assert [c["note_count"] for c in track["clips"]] == [None, None]
    track = rpc("track.get", track=0, include_note_counts=True)
    assert [c["note_count"] for c in track["clips"]] == [10, 8]
    assert rpc("track.get", track=3, include_note_counts=True)["clips"][0]["note_count"] is None  # audio
    assert rpc.err("track.get", track=0, include_note_counts="yes")["code"] == -32602
    # Single-clip results always carry the count.
    assert rpc("clip.get", track=0, slot=0)["note_count"] == 10


def test_track_get_with_params(rpc):
    track = rpc("track.get", track=1, include_params=True)
    assert track["devices"][0]["parameters"][0]["name"] == "Device On"


def test_track_get_return_and_master(rpc):
    ret = rpc("track.get", track=0, track_type="return")
    assert ret["type"] == "return" and ret["can_be_armed"] is False and ret["arm"] is False
    assert ret["clip_count"] == 0 and ret["clips"] == []
    assert ret["devices"][0]["name"] == "Reverb"
    master = rpc("track.get", track_type="master")
    assert master["type"] == "master" and master["index"] == 0
    assert master["devices"][0]["name"] == "Limiter"
    assert master["sends"] == []


def test_track_set_basic(rpc, fake_live):
    track = rpc("track.set", track=1, name="Bassline", color_index=20, mute=True, solo=True, arm=True)
    assert track["name"] == "Bassline" and track["color_index"] == 20
    assert track["color"] == "#%06X" % _core.PALETTE[20]
    assert track["mute"] is True and track["solo"] is True and track["arm"] is True
    assert fake_live.song.tracks[1].arm is True


def test_track_set_mixer(rpc):
    track = rpc("track.set", track=1, volume=0.5, pan=-0.5, sends=[{"index": 1, "value": 0.85}])
    assert track["volume"]["value"] == 0.5 and track["volume"]["display"].endswith("dB")
    assert track["pan"] == {"value": -0.5, "display": "25L"}
    assert track["sends"][1] == {"index": 1, "name": "B-Delay", "value": 0.85, "display": "0.0 dB"}
    assert track["sends"][0]["value"] == 0.0


def test_track_set_volume_zero_db(rpc):
    assert rpc("track.set", track=0, volume=0.85)["volume"]["display"] == "0.0 dB"
    assert rpc("track.set", track=0, volume=0.0)["volume"]["display"] == "-inf dB"


def test_track_set_arm_rejected(rpc):
    error = rpc.err("track.set", track=0, track_type="return", arm=True)
    assert error["code"] == -32001 and error["data"]["reason"] == "cannot_arm"
    error = rpc.err("track.set", track=4, arm=True)
    assert error["code"] == -32001 and error["data"]["reason"] == "cannot_arm"
    assert rpc.err("track.set", track_type="master", arm=True)["code"] == -32001


def test_track_set_fold(rpc, fake_live):
    track = rpc("track.set", track=4, fold=True)
    assert track["is_foldable"] is True
    assert fake_live.song.tracks[4].fold_state == 1
    rpc("track.set", track=4, fold=False)
    assert fake_live.song.tracks[4].fold_state == 0
    error = rpc.err("track.set", track=0, fold=True)
    assert error["code"] == -32001 and error["data"]["reason"] == "not_a_group"


def test_track_set_invalid(rpc):
    assert rpc.err("track.set", track=0, volume=1.5)["code"] == -32602
    assert rpc.err("track.set", track=0, pan=2)["code"] == -32602
    assert rpc.err("track.set", track=0, color_index=70)["code"] == -32602
    assert rpc.err("track.set", track=0, mute="yes")["code"] == -32602
    error = rpc.err("track.set", track=0, sends=[{"index": 5, "value": 0.5}])
    assert error["code"] == -32000 and error["data"] == {"kind": "send", "index": 5, "count": 2}
    assert rpc.err("track.set", track=0, sends=["x"])["code"] == -32602
    assert rpc.err("track.set", track=0, track_type="bus")["code"] == -32602


def test_track_set_validation_happens_before_mutation(rpc, fake_live):
    rpc.err("track.set", track=0, name="Changed?", sends=[{"index": 5, "value": 0.5}])
    assert fake_live.song.tracks[0].name == "Drums"


def test_track_set_color_none(rpc):
    track = rpc("track.set", track=0, color_index=None)
    assert track["color_index"] is None and track["color"] is None


def test_track_stop_clips(rpc, fake_live):
    rpc("clip.fire", track=0, slot=1)
    assert fake_live.song.tracks[0].playing_slot_index == 1
    assert rpc("track.stop_clips", track=0) == {"ok": True}
    assert fake_live.song.tracks[0].playing_slot_index == -1
