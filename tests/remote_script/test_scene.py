"""scene.* handlers."""


def test_scene_set(rpc):
    scene = rpc("scene.set", scene=1, name="Verse A", color_index=3, tempo=128.0)
    assert scene["index"] == 1 and scene["name"] == "Verse A"
    assert scene["color_index"] == 3 and scene["color"].startswith("#")
    assert scene["tempo"] == 128.0
    scene = rpc("scene.set", scene=1, tempo=None)
    assert scene["tempo"] is None and scene["name"] == "Verse A"
    scene = rpc("scene.set", scene=1, color_index=None)
    assert scene["color_index"] is None and scene["color"] is None


def test_scene_set_invalid(rpc):
    assert rpc.err("scene.set", scene=1, tempo=5)["code"] == -32602
    assert rpc.err("scene.set", scene=1, color_index=99)["code"] == -32602
    assert rpc.err("scene.set", scene=99, name="x")["code"] == -32000
    assert rpc.err("scene.set", name="x")["code"] == -32602


def test_scene_fire(rpc, fake_live):
    scene = rpc("scene.fire", scene=0)
    assert scene["index"] == 0 and scene["name"] == "Intro"
    playing = [t.playing_slot_index for t in fake_live.song.tracks]
    assert playing == [0, 0, 0, 0, -1, -1]
    assert rpc("view.get_selection")["scene"]["index"] == 0
    assert rpc("clip.get", track=1, slot=0)["is_playing"] is True


def test_scene_fire_second(rpc, fake_live):
    rpc("scene.fire", scene=1)
    playing = [t.playing_slot_index for t in fake_live.song.tracks]
    assert playing == [1, 1, -1, -1, -1, -1]


def test_scene_not_found(rpc):
    error = rpc.err("scene.fire", scene=8)
    assert error["code"] == -32000 and error["data"] == {"kind": "scene", "index": 8, "count": 8}
