"""automation.* handlers."""
import pytest

FREQ = {"track": 1, "slot": 0, "device_path": "0", "parameter": "Filter Freq"}


def _values(rpc, resolution, **address):
    params = dict(FREQ)
    params.update(address)
    return [p["value"] for p in rpc("automation.get", resolution=resolution, **params)["points"]]


def test_get_without_envelope(rpc):
    result = rpc("automation.get", **FREQ)
    assert set(result) == {"exists", "points", "parameter"}
    assert result["exists"] is False and result["points"] == []
    assert result["parameter"]["name"] == "Filter Freq" and result["parameter"]["index"] == 4


def test_set_steps_then_get_roundtrip(rpc):
    result = rpc("automation.set", points=[{"time": 0, "value": 0.2}, {"time": 2, "value": 0.8}], mode="steps",
                 **FREQ)
    assert result == {"inserted": 2, "exists": True, "mode": "steps"}
    got = rpc("automation.get", resolution=1.0, **FREQ)
    assert got["exists"] is True
    assert got["points"] == [{"time": 0.0, "value": 0.2}, {"time": 1.0, "value": 0.2},
                             {"time": 2.0, "value": 0.8}, {"time": 3.0, "value": 0.8}]


def test_set_defaults_to_ramp_and_sorts_points(rpc):
    result = rpc("automation.set", points=[{"time": 2, "value": 0.8}, {"time": 0, "value": 0.2}], **FREQ)
    assert result["mode"] == "ramp" and result["exists"] is True
    assert result["inserted"] == 33  # 32 steps of 0.0625 over the 2-beat ramp + the final hold
    assert _values(rpc, 1.0) == pytest.approx([0.2, 0.5, 0.8, 0.8])


def test_set_result_reports_mode(rpc):
    assert rpc("automation.set", points=[{"time": 0, "value": 0.2}], mode="steps", **FREQ)["mode"] == "steps"
    assert rpc("automation.set", points=[{"time": 0, "value": 0.2}], mode="ramp", **FREQ)["mode"] == "ramp"


def test_set_too_many_steps(rpc):
    points = [{"time": i * 0.01, "value": 0.5} for i in range(2001)]
    error = rpc.err("automation.set", points=points, mode="steps", **FREQ)
    assert error["code"] == -32005 and error["data"] == {"limit": 2000, "got": 2001}
    # A ramp that expands into too many steps is rejected before anything is inserted.
    error = rpc.err("automation.set", points=[{"time": 0, "value": 0}, {"time": 4, "value": 1}], mode="ramp",
                    resolution=0.001, **FREQ)
    assert error["code"] == -32005 and error["data"]["limit"] == 2000 and error["data"]["got"] > 2000
    assert rpc("automation.get", **FREQ)["exists"] is False


def test_set_ramp_produces_intermediate_values(rpc):
    result = rpc("automation.set", points=[{"time": 0, "value": 0.0}, {"time": 2, "value": 1.0}], mode="ramp",
                 resolution=0.5, **FREQ)
    assert result["inserted"] == 5 and result["mode"] == "ramp"
    assert _values(rpc, 0.5) == pytest.approx([0.0, 0.25, 0.5, 0.75, 1.0, 1.0, 1.0, 1.0])


def test_get_window(rpc):
    rpc("automation.set", points=[{"time": 0, "value": 0.0}, {"time": 2, "value": 1.0}], mode="ramp",
        resolution=0.5, **FREQ)
    got = rpc("automation.get", from_time=1.0, time_span=1.0, resolution=0.5, **FREQ)
    assert [p["time"] for p in got["points"]] == [1.0, 1.5]
    assert [p["value"] for p in got["points"]] == pytest.approx([0.5, 0.75])


def test_set_clamps_values(rpc):
    rpc("automation.set", points=[{"time": 0, "value": 5.0}, {"time": 2, "value": -3.0}], **FREQ)
    assert _values(rpc, 2.0) == [1.0, 0.0]


def test_set_quantized_parameter_rounds_and_steps(rpc):
    params = dict(FREQ, parameter="Osc-A Wave")
    result = rpc("automation.set", points=[{"time": 0, "value": 1.4}, {"time": 2, "value": 2.6}], mode="ramp",
                 **params)
    assert result["mode"] == "steps"
    got = rpc("automation.get", resolution=2.0, **params)
    assert [p["value"] for p in got["points"]] == [1.0, 3.0]


def test_set_last_point_holds_to_clip_end(rpc):
    rpc("automation.set", points=[{"time": 3.0, "value": 0.9}], **FREQ)
    assert _values(rpc, 1.0)[3] == 0.9
    rpc("automation.set", points=[{"time": 6.0, "value": 0.1}], **FREQ)  # beyond the clip end still works
    assert rpc("automation.get", from_time=6.0, time_span=0.0625, **FREQ)["points"][0]["value"] == 0.1


def test_set_invalid(rpc):
    assert rpc.err("automation.set", points=[], **FREQ)["code"] == -32602
    assert rpc.err("automation.set", points=[{"time": -1, "value": 0}], **FREQ)["code"] == -32602
    assert rpc.err("automation.set", points=[{"time": 0}], **FREQ)["code"] == -32602
    assert rpc.err("automation.set", points=[{"time": 0, "value": 0}], mode="curve", **FREQ)["code"] == -32602
    assert rpc.err("automation.set", points="x", **FREQ)["code"] == -32602
    assert rpc.err("automation.set", track=1, slot=0, parameter="Filter Freq",
                   points=[{"time": 0, "value": 0}])["code"] == -32602
    assert rpc.err("automation.set", track=1, slot=0, device_path="0",
                   points=[{"time": 0, "value": 0}])["code"] == -32602
    error = rpc.err("automation.set", points=[{"time": 0, "value": 0}], **dict(FREQ, parameter="Nope"))
    assert error["code"] == -32000 and error["data"]["kind"] == "parameter"
    assert rpc.err("automation.set", points=[{"time": 0, "value": 0}], **dict(FREQ, device_path="9"))["code"] == -32000
    assert rpc.err("automation.set", points=[{"time": 0, "value": 0}], **dict(FREQ, slot=3))["code"] == -32001
    assert rpc("automation.get", **FREQ)["exists"] is False


def test_mixer_automation(rpc, fake_live):
    params = dict(track=1, slot=0, device_path="mixer", parameter="Volume")
    result = rpc("automation.set", points=[{"time": 0, "value": 0.5}], **params)
    assert result["exists"] is True and result["inserted"] == 1
    got = rpc("automation.get", resolution=2.0, **params)
    assert [p["value"] for p in got["points"]] == [0.5, 0.5]
    assert got["parameter"]["name"] == "Volume"
    volume = fake_live.song.tracks[1].mixer_device.volume
    assert fake_live.song.tracks[1].clip_slots[0].clip.automation_envelope(volume) is not None


def test_clear_parameter(rpc):
    rpc("automation.set", points=[{"time": 0, "value": 0.2}], **FREQ)
    assert rpc("automation.clear", **FREQ) == {"cleared": "Filter Freq"}
    assert rpc("automation.get", **FREQ)["exists"] is False
    assert rpc("automation.clear", **FREQ) == {"cleared": "Filter Freq"}  # idempotent


def test_clear_all_requires_confirm(rpc):
    rpc("automation.set", points=[{"time": 0, "value": 0.2}], **FREQ)
    rpc("automation.set", points=[{"time": 0, "value": 0.5}], **dict(FREQ, device_path="mixer", parameter="Volume"))
    error = rpc.err("automation.clear", track=1, slot=0)
    assert error["code"] == -32002 and error["data"]["method"] == "automation.clear"
    assert "Bass 1" in error["data"]["target"]
    assert rpc("automation.get", **FREQ)["exists"] is True
    assert rpc("automation.clear", track=1, slot=0, confirm=True) == {"cleared": "all"}
    assert rpc("automation.get", **FREQ)["exists"] is False
    assert rpc("automation.get", **dict(FREQ, device_path="mixer", parameter="Volume"))["exists"] is False


def test_clear_device_path_without_parameter_is_invalid(rpc):
    assert rpc.err("automation.clear", track=1, slot=0, device_path="0", confirm=True)["code"] == -32602


def test_arrangement_clip_envelopes(rpc):
    params = dict(track=0, arrangement_index=0, device_path="1", parameter="Threshold")
    assert rpc("automation.get", **params)["exists"] is False
    error = rpc.err("automation.set", points=[{"time": 0, "value": 0.5}], **params)
    assert error["code"] == -32004 and error["data"]["exception"] == "RuntimeError"


def test_get_too_many_points(rpc):
    rpc("automation.set", points=[{"time": 0, "value": 0.2}], **FREQ)
    error = rpc.err("automation.get", resolution=0.001, time_span=100.0, **FREQ)
    assert error["code"] == -32005 and error["data"]["limit"] == 2000
    assert len(rpc("automation.get", resolution=0.01, time_span=20.0, **FREQ)["points"]) == 2000
    assert rpc.err("automation.get", resolution=0, **FREQ)["code"] == -32602
