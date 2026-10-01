"""browser.* handlers."""
import Live

ITEM_KEYS = {"name", "uri", "category", "path", "is_loadable", "is_folder", "is_device"}
SATURATOR = "query:AudioFx#Saturator"


def test_search_ordering_exact_prefix_substring(rpc):
    result = rpc("browser.search", query="reverb")
    assert set(result) >= {"items", "truncated", "nodes_visited"}
    names = [item["name"] for item in result["items"]]
    assert names == ["Reverb", "Reverb Tail", "Hybrid Reverb"]
    assert result["truncated"] is False and result["nodes_visited"] > 10
    assert result["total_matches"] == 3
    reverb = result["items"][0]
    assert set(reverb) == ITEM_KEYS
    assert reverb == {"name": "Reverb", "uri": "query:AudioFx#Reverb", "category": "audio_effects",
                      "path": ["Audio Effects", "Reverb"], "is_loadable": True, "is_folder": False,
                      "is_device": True}
    assert result["items"][1]["category"] == "sounds"
    assert result["items"][1]["path"] == ["Sounds", "Pad", "Reverb Tail"]


def test_search_case_insensitive_and_limit(rpc):
    result = rpc("browser.search", query="A", limit=2)
    assert len(result["items"]) == 2 and result["total_matches"] > 2
    assert rpc("browser.search", query="WAVETABLE")["items"][0]["name"] == "Wavetable"


def test_search_categories(rpc):
    result = rpc("browser.search", query="kit", categories=["drums"])
    assert [i["name"] for i in result["items"]] == ["808 Core Kit"]
    assert result["items"][0]["path"] == ["Drums", "Drum Kits", "808 Core Kit"]
    result = rpc("browser.search", query="kit", categories=["instruments", "drums"])
    assert [i["name"] for i in result["items"]] == ["808 Core Kit", "909 Core Kit", "808 Core Kit"]


def test_search_default_categories_and_broken_nodes(rpc):
    assert rpc("browser.search", query="my bass")["items"] == []
    result = rpc("browser.search", query="my bass", categories=["user_library"])
    assert [i["name"] for i in result["items"]] == ["My Bass.adv"]
    assert result["truncated"] is False  # the folder that raises on .children is skipped, not fatal


def test_search_loadable_only(rpc):
    assert rpc("browser.search", query="drum hits", categories=["drums"])["items"] == []
    result = rpc("browser.search", query="drum hits", categories=["drums"], loadable_only=False)
    assert len(result["items"]) == 1 and result["items"][0]["is_folder"] is True


def test_search_truncation(rpc):
    result = rpc("browser.search", query="reverb", max_nodes=3)
    assert result["truncated"] is True and result["nodes_visited"] == 3
    result = rpc("browser.search", query="reverb", max_nodes=100000)
    assert result["truncated"] is False and [i["name"] for i in result["items"]][0] == "Reverb"


def test_search_resumes_from_cache(rpc, control_surface):
    first = rpc("browser.search", query="reverb", max_nodes=3)
    assert first["truncated"] is True
    cache = control_surface.ctx.state["browser_index"]
    assert cache["instruments"].complete is False
    second = rpc("browser.search", query="reverb")
    assert second["truncated"] is False and len(second["items"]) == 3
    assert cache["audio_effects"].complete is True
    third = rpc("browser.search", query="compressor")
    assert third["items"][0]["name"] == "Compressor"
    assert control_surface.ctx.state["browser_index"]["audio_effects"] is cache["audio_effects"]


def test_search_time_budget(rpc, control_surface):
    control_surface.settings["browser_time_budget_ms"] = 0.000001
    result = rpc("browser.search", query="reverb")
    assert result["truncated"] is True


def test_search_invalid(rpc):
    assert rpc.err("browser.search", query="")["code"] == -32602
    assert rpc.err("browser.search")["code"] == -32602
    error = rpc.err("browser.search", query="x", categories=["nope"])
    assert error["code"] == -32602 and "instruments" in error["data"]["available"]
    assert rpc.err("browser.search", query="x", categories=[])["code"] == -32602
    assert rpc.err("browser.search", query="x", limit=0)["code"] == -32602


def test_list_roots(rpc):
    result = rpc("browser.list")
    names = [i["name"] for i in result["items"]]
    assert "Instruments" in names and "Audio Effects" in names and "User Library" in names
    assert all(i["is_folder"] for i in result["items"])
    assert result["truncated"] is False


def test_list_category(rpc):
    result = rpc("browser.list", category="instruments")
    assert [i["name"] for i in result["items"]] == ["Analog", "Drift", "Drum Rack", "Instrument Rack", "Operator",
                                                     "Wavetable"]
    assert result["items"][0]["path"] == ["Instruments", "Analog"]
    assert result["truncated"] is False and result["count"] == 6
    limited = rpc("browser.list", category="instruments", limit=2)
    assert len(limited["items"]) == 2 and limited["truncated"] is True


def test_list_uri(rpc):
    result = rpc("browser.list", uri="query:Synths#Operator")
    assert [i["name"] for i in result["items"]] == ["Deep Bass", "FM Pluck"]
    assert result["items"][0]["path"] == ["Instruments", "Operator", "Deep Bass"]
    assert result["items"][0]["is_loadable"] is True and result["items"][0]["is_device"] is False
    error = rpc.err("browser.list", uri="query:Nope")
    assert error["code"] == -32000 and error["data"] == {"kind": "browser_item", "uri": "query:Nope"}


def test_list_invalid(rpc):
    assert rpc.err("browser.list", category="foo")["code"] == -32602
    assert rpc.err("browser.list", limit=0)["code"] == -32602


def test_load_appends_device(rpc, fake_live):
    result = rpc("browser.load", uri=SATURATOR, track=1)
    assert set(result) >= {"loaded", "track", "devices", "method"}
    assert result["loaded"]["name"] == "Saturator" and result["loaded"]["path"] == "1"
    assert result["method"] == "load_item"
    assert result["track"]["index"] == 1 and result["track"]["device_count"] == 2
    assert [d["name"] for d in result["devices"]] == ["Operator", "Saturator"]
    assert result["item"]["uri"] == SATURATOR
    assert fake_live.song.view.selected_track is fake_live.song.tracks[1]


def test_load_after_device_path(rpc, fake_live):
    result = rpc("browser.load", uri=SATURATOR, track=2, after_device_path="1")
    assert [d["name"] for d in result["devices"]] == ["Arpeggiator", "Chord", "Saturator", "Pad Rack", "Auto Filter"]
    assert result["loaded"]["path"] == "2"
    track = fake_live.song.tracks[2]
    assert track.view.device_insert_mode == Live.Track.DeviceInsertMode.default


def test_load_after_last_device(rpc):
    result = rpc("browser.load", uri=SATURATOR, track=0, after_device_path="1")
    assert [d["name"] for d in result["devices"]] == ["Drum Rack", "Compressor", "Saturator"]


def test_load_uses_selected_track(rpc, fake_live):
    fake_live.song.view.selected_track = fake_live.song.tracks[3]
    result = rpc("browser.load", uri="query:AudioFx#EQ%20Eight")
    assert result["track"]["name"] == "Vox" and result["loaded"]["name"] == "EQ Eight"


def test_load_preset_and_kit(rpc):
    result = rpc("browser.load", uri="query:Sounds#Bass:Deep%20Bass.adg", track=5)
    assert result["loaded"]["name"] == "Operator" and result["loaded"]["type"] == "instrument"
    result = rpc("browser.load", uri="query:Synths#Drum%20Rack:808%20Core%20Kit.adg", track=5)
    assert result["loaded"]["name"] == "808 Core Kit" and result["loaded"]["can_have_drum_pads"] is True


def test_load_sample_returns_null(rpc):
    result = rpc("browser.load", uri="query:Drums#Drum%20Hits:Kick%20909.aif", track=3)
    assert result["loaded"] is None and len(result["devices"]) == 2


def test_load_return_track(rpc):
    result = rpc("browser.load", uri="query:AudioFx#Utility", track=0, track_type="return")
    assert result["track"]["track_type"] == "return" and result["loaded"]["name"] == "Utility"


def test_load_errors(rpc, fake_live):
    error = rpc.err("browser.load", uri="query:Nope", track=1)
    assert error["code"] == -32000 and error["data"]["kind"] == "browser_item"
    error = rpc.err("browser.load", uri="query:Synths", track=1)
    assert error["code"] == -32001 and error["data"]["reason"] == "not_loadable"
    assert rpc.err("browser.load", uri=SATURATOR, track=1, after_device_path="mixer")["code"] == -32602
    assert rpc.err("browser.load", uri=SATURATOR, track=9)["code"] == -32000
    assert rpc.err("browser.load", uri=SATURATOR, track=1, after_device_path="5")["code"] == -32000
    assert rpc.err("browser.load", track=1)["code"] == -32602
    assert len(fake_live.song.tracks[1].devices) == 1
