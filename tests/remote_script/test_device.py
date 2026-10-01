"""device.* handlers."""
DEVICE_KEYS = {"path", "name", "class_name", "class_display_name", "type", "is_active", "is_rack",
               "can_have_drum_pads", "chain_count", "parameter_count"}
PARAM_KEYS = {"index", "name", "original_name", "value", "min", "max", "default", "display", "is_quantized",
              "value_items", "is_enabled", "automation_state"}
OPERATOR = {"track": 1, "path": "0"}


def test_device_list_shape(rpc):
    result = rpc("device.list", track=0)
    assert set(result) == {"devices", "mixer"}
    devices = result["devices"]
    assert len(devices) == 2
    rack = devices[0]
    assert DEVICE_KEYS <= set(rack)
    assert rack["path"] == "0" and rack["name"] == "Drum Rack" and rack["class_name"] == "DrumGroupDevice"
    assert rack["type"] == "instrument" and rack["is_rack"] is True and rack["can_have_drum_pads"] is True
    assert rack["chain_count"] == 4 and rack["parameter_count"] == 9 and rack["is_active"] is True
    assert "parameters" not in rack
    assert [c["name"] for c in rack["chains"]] == ["Kick 909", "Snare 909", "Hat Closed 909", "Clap 909"]
    kick = rack["chains"][0]["devices"][0]
    assert kick["path"] == "0/0/0" and kick["name"] == "Kick 909" and kick["class_display_name"] == "Simpler"
    assert sorted(p["note"] for p in rack["drum_pads"]) == [36, 38, 39, 42]
    assert {"note": 36, "name": "Kick 909", "has_chain": True} in rack["drum_pads"]
    compressor = devices[1]
    assert compressor["path"] == "1" and compressor["type"] == "audio_effect" and compressor["is_rack"] is False
    assert "chains" not in compressor
    mixer = result["mixer"]
    assert mixer["path"] == "mixer"
    assert [p["name"] for p in mixer["parameters"]] == ["Volume", "Pan", "Send A", "Send B", "Track Activator"]
    assert mixer["parameters"][0]["display"] == "0.0 dB"
    assert mixer["parameters"][4]["is_quantized"] is True


def test_device_list_include_params(rpc):
    params = rpc("device.list", track=1, include_params=True)["devices"][0]["parameters"]
    assert set(params[0]) == PARAM_KEYS
    assert params[0]["name"] == "Device On" and params[0]["is_quantized"] is True
    assert params[0]["value_items"] == ["Off", "On"] and params[0]["default"] is None
    assert params[0]["value"] == 1.0 and params[0]["display"] == "On"
    freq = params[4]
    assert freq["name"] == "Filter Freq" and freq["index"] == 4 and freq["is_quantized"] is False
    assert freq["value_items"] is None and freq["default"] == 0.5
    assert freq["display"].endswith("Hz") and freq["automation_state"] == "none"


def test_device_list_depth(rpc):
    shallow = rpc("device.list", track=2, depth=0)["devices"]
    assert [d["name"] for d in shallow] == ["Arpeggiator", "Chord", "Pad Rack", "Auto Filter"]
    assert shallow[2]["is_rack"] is True and shallow[2]["chain_count"] == 2 and "chains" not in shallow[2]
    deep = rpc("device.list", track=2, depth=1)["devices"]
    assert deep[2]["chains"][1]["devices"][0]["path"] == "2/1/0"
    assert rpc.err("device.list", track=2, depth=99)["code"] == -32602


def test_device_list_return_and_master(rpc):
    assert rpc("device.list", track_type="master")["devices"][0]["name"] == "Limiter"
    assert rpc("device.list", track=1, track_type="return")["devices"][0]["name"] == "Delay"
    assert rpc("device.list", track_type="master")["mixer"]["parameters"][2]["name"] == "Track Activator"


def test_device_get(rpc):
    detail = rpc("device.get", track=2, path="2")
    assert detail["name"] == "Pad Rack" and detail["class_display_name"] == "Instrument Rack"
    assert detail["path"] == "2" and len(detail["parameters"]) == 9
    assert detail["parameters"][1]["name"] == "Cutoff" and detail["parameters"][1]["original_name"] == "Macro 1"
    assert len(detail["chains"]) == 2
    nested = detail["chains"][1]["devices"][0]
    assert nested["name"] == "Wavetable" and nested["path"] == "2/1/0"
    assert "drum_pads" not in detail


def test_device_get_nested_and_mixer(rpc):
    nested = rpc("device.get", track=2, path="2/1/0")
    assert nested["name"] == "Wavetable" and nested["path"] == "2/1/0" and len(nested["parameters"]) == 10
    plain = rpc("device.get", track=2, path="2/1/0", include_params=False)
    assert "parameters" not in plain
    mixer = rpc("device.get", track=0, path="mixer")
    assert mixer["path"] == "mixer" and mixer["parameters"][0]["name"] == "Volume"
    assert rpc("device.get", track=0, path="mixer", include_params=False).get("parameters") is None


def test_device_path_errors(rpc):
    error = rpc.err("device.get", track=0, path="5")
    assert error["code"] == -32000 and error["data"]["kind"] == "device" and error["data"]["count"] == 2
    error = rpc.err("device.get", track=0, path="0/9/0")
    assert error["code"] == -32000 and error["data"]["kind"] == "chain" and error["data"]["count"] == 4
    error = rpc.err("device.get", track=0, path="1/0/0")
    assert error["code"] == -32001 and error["data"]["reason"] == "not_a_rack"
    assert rpc.err("device.get", track=0, path="0/1")["code"] == -32602
    assert rpc.err("device.get", track=0, path="a")["code"] == -32602
    assert rpc.err("device.get", track=0, path="")["code"] == -32602
    assert rpc.err("device.get", track=0)["code"] == -32602
    error = rpc.err("device.get", track=0, path="0/0/3")
    assert error["data"]["kind"] == "device" and error["data"]["count"] == 1


def test_get_parameter_by_name_and_index(rpc):
    param = rpc("device.get_parameter", parameter="filter freq", **OPERATOR)
    assert param["name"] == "Filter Freq" and param["index"] == 4 and "ambiguous" not in param
    assert rpc("device.get_parameter", parameter=4, **OPERATOR) == param
    assert rpc("device.get_parameter", parameter=4.0, **OPERATOR) == param


def test_get_parameter_ambiguous_and_original_name(rpc):
    param = rpc("device.get_parameter", parameter="attack", **OPERATOR)
    assert param["ambiguous"] is True and param["original_name"] == "Ae Attack" and param["index"] == 7
    param = rpc("device.get_parameter", parameter="Be Attack", **OPERATOR)
    assert param["original_name"] == "Be Attack" and param["index"] == 8 and "ambiguous" not in param
    macro = rpc("device.get_parameter", track=2, path="2", parameter="macro 1")
    assert macro["name"] == "Cutoff"


def test_get_parameter_not_found(rpc):
    error = rpc.err("device.get_parameter", parameter="Cutoff", **OPERATOR)
    assert error["code"] == -32000
    assert error["data"]["kind"] == "parameter" and error["data"]["name"] == "Cutoff"
    assert "Filter Freq" in error["data"]["available"] and "Cutoff" in error["message"]
    error = rpc.err("device.get_parameter", parameter=99, **OPERATOR)
    assert error["data"] == {"kind": "parameter", "index": 99, "count": 12}
    assert rpc.err("device.get_parameter", parameter=True, **OPERATOR)["code"] == -32602
    assert rpc.err("device.get_parameter", **OPERATOR)["code"] == -32602


def test_set_parameter_by_value(rpc, fake_live):
    result = rpc("device.set_parameter", parameter="Filter Freq", value=0.25, **OPERATOR)
    assert set(result) == {"parameter", "previous", "clamped"}
    assert result["parameter"]["value"] == 0.25 and result["parameter"]["name"] == "Filter Freq"
    assert result["previous"]["value"] == 0.5 and result["previous"]["display"].endswith("Hz")
    assert result["clamped"] is False
    assert fake_live.song.tracks[1].devices[0].parameters[4].value == 0.25


def test_set_parameter_by_index(rpc):
    result = rpc("device.set_parameter", parameter=4, value=0.75, **OPERATOR)
    assert result["parameter"]["name"] == "Filter Freq" and result["parameter"]["value"] == 0.75


def test_set_parameter_clamped(rpc):
    result = rpc("device.set_parameter", parameter="Filter Freq", value=1.5, **OPERATOR)
    assert result["parameter"]["value"] == 1.0 and result["clamped"] is True
    result = rpc("device.set_parameter", parameter="Filter Freq", normalized=-1, **OPERATOR)
    assert result["parameter"]["value"] == 0.0 and result["clamped"] is True


def test_set_parameter_normalized(rpc):
    result = rpc("device.set_parameter", parameter="Transpose", normalized=0.75, **OPERATOR)
    assert result["parameter"]["value"] == 24.0 and result["parameter"]["display"] == "24 st"
    assert result["clamped"] is False


def test_set_parameter_display_quantized(rpc):
    result = rpc("device.set_parameter", parameter="Osc-A Wave", display="saw d", **OPERATOR)
    assert result["parameter"]["value"] == 1.0 and result["parameter"]["display"] == "Saw D"
    assert result["previous"] == {"value": 0.0, "display": "Sine"}
    error = rpc.err("device.set_parameter", parameter="Osc-A Wave", display="Triangle", **OPERATOR)
    assert error["code"] == -32602 and error["data"]["value_items"] == ["Sine", "Saw D", "Square D", "Noise White"]


def test_set_parameter_quantized_value_rules(rpc):
    error = rpc.err("device.set_parameter", parameter="Osc-A Wave", value=1.5, **OPERATOR)
    assert error["code"] == -32602 and "value_items" in error["data"]
    assert rpc("device.set_parameter", parameter="Osc-A Wave", value=2, **OPERATOR)["parameter"]["display"] == "Square D"
    result = rpc("device.set_parameter", parameter="Osc-A Wave", value=9, **OPERATOR)
    assert result["parameter"]["value"] == 3.0 and result["clamped"] is True
    assert rpc("device.set_parameter", parameter="Osc-A Wave", normalized=0.0, **OPERATOR)["parameter"]["display"] == "Sine"


def test_set_parameter_display_continuous(rpc):
    result = rpc("device.set_parameter", parameter="Transpose", display="12 st", **OPERATOR)
    assert result["parameter"]["value"] == 12.0
    result = rpc("device.set_parameter", track=0, path="mixer", parameter="Volume", display="-6.0 dB")
    assert result["parameter"]["display"] == "-6.0 dB" and result["parameter"]["value"] < 0.85
    result = rpc("device.set_parameter", track=0, path="mixer", parameter="Volume", display="-inf dB")
    assert result["parameter"]["value"] == 0.0
    error = rpc.err("device.set_parameter", parameter="Transpose", display="banana", **OPERATOR)
    assert error["code"] == -32602


def test_set_parameter_exactly_one_source(rpc):
    assert rpc.err("device.set_parameter", parameter="Filter Freq", value=0.5, normalized=0.5, **OPERATOR)["code"] == -32602
    assert rpc.err("device.set_parameter", parameter="Filter Freq", **OPERATOR)["code"] == -32602
    assert rpc.err("device.set_parameter", parameter="Filter Freq", value="loud", **OPERATOR)["code"] == -32602


def test_set_parameter_ambiguous_flag(rpc, fake_live):
    result = rpc("device.set_parameter", parameter="Attack", value=10.0, **OPERATOR)
    assert result["parameter"]["ambiguous"] is True and result["parameter"]["original_name"] == "Ae Attack"
    operator = fake_live.song.tracks[1].devices[0]
    assert operator.parameters[7].value == 10.0 and operator.parameters[8].value == 5.0


def test_set_parameter_mixer(rpc, fake_live):
    result = rpc("device.set_parameter", track=1, path="mixer", parameter="Volume", value=0.85)
    assert result["parameter"]["display"] == "0.0 dB" and result["parameter"]["name"] == "Volume"
    assert fake_live.song.tracks[1].mixer_device.volume.value == 0.85
    result = rpc("device.set_parameter", track=1, path="mixer", parameter="send a", value=0.5)
    assert result["parameter"]["name"] == "Send A" and result["parameter"]["display"].endswith("dB")
    assert rpc("track.get", track=1)["sends"][0]["value"] == 0.5
    result = rpc("device.set_parameter", track=1, path="mixer", parameter="Pan", value=-1)
    assert result["parameter"]["display"] == "50L"
    result = rpc("device.set_parameter", track=1, path="mixer", parameter="Track Activator", display="off")
    assert result["parameter"]["value"] == 0.0
    assert rpc("device.get_parameter", track=1, path="mixer", parameter=0)["name"] == "Volume"


def test_set_parameter_nested_path(rpc, fake_live):
    result = rpc("device.set_parameter", track=2, path="2/1/0", parameter="Filter 1 Freq", value=0.1)
    assert result["parameter"]["value"] == 0.1
    rack = fake_live.song.tracks[2].devices[2]
    assert rack.chains[1].devices[0].parameters[4].value == 0.1
    assert rack.chains[0].devices[0].parameters[4].value == 0.6


def test_set_parameters_partial_success(rpc):
    values = [{"parameter": "Filter Freq", "value": 0.3},
              {"parameter": "Nope", "value": 1},
              {"parameter": "Osc-A Wave", "display": "Square D"},
              "bad",
              {"parameter": "Filter Res", "value": 0.1, "normalized": 0.2}]
    result = rpc("device.set_parameters", values=values, **OPERATOR)
    assert [r["parameter"]["name"] for r in result["results"]] == ["Filter Freq", "Osc-A Wave"]
    assert len(result["errors"]) == 3
    assert result["errors"][0]["parameter"] == "Nope" and result["errors"][0]["code"] == -32000
    assert result["errors"][0]["index"] == 1 and "Nope" in result["errors"][0]["message"]
    assert result["errors"][1]["code"] == -32602 and result["errors"][1]["index"] == 3
    assert result["errors"][2]["code"] == -32602 and result["errors"][2]["parameter"] == "Filter Res"
    assert rpc.err("device.set_parameters", **OPERATOR)["code"] == -32602


def test_set_enabled(rpc, fake_live):
    result = rpc("device.set_enabled", track=0, path="1", enabled=False)
    assert result["is_active"] is False and result["path"] == "1"
    assert fake_live.song.tracks[0].devices[1].parameters[0].value == 0.0
    assert rpc("device.get", track=0, path="1")["is_active"] is False
    assert rpc("device.set_enabled", track=0, path="1", enabled=True)["is_active"] is True
    assert rpc("device.set_enabled", track=2, path="2/0/0", enabled=False)["is_active"] is False
    rpc("device.set_enabled", track=2, path="2", enabled=False)
    assert rpc("device.get", track=2, path="2/1/0")["is_active"] is False
    assert rpc.err("device.set_enabled", track=0, path="1")["code"] == -32602
    assert rpc.err("device.set_enabled", track=0, path="mixer", enabled=False)["code"] == -32001


def test_device_delete(rpc, fake_live):
    error = rpc.err("device.delete", track=0, path="1")
    assert error["code"] == -32002 and "Compressor" in error["data"]["target"]
    assert error["data"]["method"] == "device.delete"
    assert len(fake_live.song.tracks[0].devices) == 2
    assert rpc("device.delete", track=0, path="1", confirm=True) == {"deleted": "Compressor", "path": "1"}
    assert len(fake_live.song.tracks[0].devices) == 1


def test_device_delete_nested(rpc, fake_live):
    result = rpc("device.delete", track=2, path="2/0/0", confirm=True)
    assert result["deleted"] == "Wavetable"
    rack = fake_live.song.tracks[2].devices[2]
    assert rack.chains[0].devices == () and len(rack.chains[1].devices) == 1


def test_device_delete_errors(rpc):
    assert rpc.err("device.delete", track=0, path="mixer", confirm=True)["code"] == -32001
    assert rpc.err("device.delete", track=0, path="7", confirm=True)["code"] == -32000
    assert rpc("device.delete", track_type="master", path="0", confirm=True)["deleted"] == "Limiter"
