"""JSON-RPC validation, routing and error mapping in the dispatcher."""
import json
import logging

import pytest

from ClaudeLive import errors
from ClaudeLive.dispatcher import Dispatcher
from ClaudeLive.errors import LiveRpcError, FrameError


def _ok(ctx, params):
    return {"echo": params}


def _raises_rpc(ctx, params):
    raise errors.not_found("track", 9, 4)


def _raises_bug(ctx, params):
    raise KeyError("boom")


def _raises_live(ctx, params):
    raise RuntimeError("Master and Return Tracks have no 'Arm' state!")


def _returns_none(ctx, params):
    return None


def _returns_scalar(ctx, params):
    return 42


@pytest.fixture
def dispatcher():
    methods = {"t.ok": _ok, "t.rpc": _raises_rpc, "t.bug": _raises_bug, "t.live": _raises_live,
               "t.none": _returns_none, "t.scalar": _returns_scalar}
    return Dispatcher(ctx=object(), methods=methods, logger=logging.getLogger("test"))


def test_success_echoes_int_id(dispatcher):
    response = dispatcher.handle({"jsonrpc": "2.0", "id": 7, "method": "t.ok", "params": {"a": 1}})
    assert response == {"jsonrpc": "2.0", "id": 7, "result": {"echo": {"a": 1}}}


def test_success_echoes_string_id(dispatcher):
    response = dispatcher.handle({"jsonrpc": "2.0", "id": "abc", "method": "t.ok"})
    assert response["id"] == "abc"
    assert response["result"] == {"echo": {}}


def test_missing_params_defaults_to_empty_object(dispatcher):
    response = dispatcher.handle({"jsonrpc": "2.0", "id": 1, "method": "t.ok", "params": None})
    assert response["result"] == {"echo": {}}


def test_wrong_jsonrpc_version(dispatcher):
    response = dispatcher.handle({"jsonrpc": "1.0", "id": 1, "method": "t.ok"})
    assert response["error"]["code"] == -32600
    assert response["id"] == 1


def test_missing_jsonrpc(dispatcher):
    response = dispatcher.handle({"id": 1, "method": "t.ok"})
    assert response["error"]["code"] == -32600


def test_missing_method(dispatcher):
    response = dispatcher.handle({"jsonrpc": "2.0", "id": 2})
    assert response["error"]["code"] == -32600
    assert response["id"] == 2


def test_non_string_method(dispatcher):
    response = dispatcher.handle({"jsonrpc": "2.0", "id": 2, "method": 5})
    assert response["error"]["code"] == -32600


def test_unknown_method(dispatcher):
    response = dispatcher.handle({"jsonrpc": "2.0", "id": 3, "method": "nope.nothing"})
    assert response["error"]["code"] == -32601
    assert "nope.nothing" in response["error"]["message"]
    assert response["error"]["data"]["method"] == "nope.nothing"


def test_params_must_be_object(dispatcher):
    response = dispatcher.handle({"jsonrpc": "2.0", "id": 4, "method": "t.ok", "params": [1, 2]})
    assert response["error"]["code"] == -32602


def test_notification_is_ignored(dispatcher):
    assert dispatcher.handle({"jsonrpc": "2.0", "method": "t.ok"}) is None
    assert dispatcher.handle({"jsonrpc": "2.0", "method": "nope.nothing"}) is None
    assert dispatcher.handled == 0


def test_invalid_id_types(dispatcher):
    response = dispatcher.handle({"jsonrpc": "2.0", "id": True, "method": "t.ok"})
    assert response["error"]["code"] == -32600
    assert response["id"] is None
    response = dispatcher.handle({"jsonrpc": "2.0", "id": {"x": 1}, "method": "t.ok"})
    assert response["error"]["code"] == -32600


def test_non_object_payloads(dispatcher):
    response = dispatcher.handle([{"jsonrpc": "2.0", "id": 1, "method": "t.ok"}])
    assert response["error"]["code"] == -32600
    assert "Batch" in response["error"]["message"]
    assert response["id"] is None
    response = dispatcher.handle("just a string")
    assert response["error"]["code"] == -32600
    response = dispatcher.handle(42)
    assert response["error"]["code"] == -32600


def test_frame_errors(dispatcher):
    response = dispatcher.handle(FrameError(errors.PARSE_ERROR, "Parse error: bad json"))
    assert response == {"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": "Parse error: bad json"}}
    response = dispatcher.handle(FrameError(errors.INVALID_REQUEST, "Line too long"))
    assert response["error"]["code"] == -32600


def test_live_rpc_error_passthrough(dispatcher):
    response = dispatcher.handle({"jsonrpc": "2.0", "id": 5, "method": "t.rpc"})
    assert response["error"]["code"] == -32000
    assert response["error"]["data"] == {"kind": "track", "index": 9, "count": 4}
    assert "Track 9 does not exist" in response["error"]["message"]


def test_unexpected_exception_is_internal_error(dispatcher):
    response = dispatcher.handle({"jsonrpc": "2.0", "id": 6, "method": "t.bug"})
    assert response["error"]["code"] == -32603
    assert response["error"]["data"]["exception"] == "KeyError"
    assert "boom" in response["error"]["data"]["detail"]


def test_runtime_error_maps_to_live_error(dispatcher):
    response = dispatcher.handle({"jsonrpc": "2.0", "id": 6, "method": "t.live"})
    assert response["error"]["code"] == -32004
    assert response["error"]["data"]["exception"] == "RuntimeError"
    assert "Arm" in response["error"]["data"]["detail"]


def test_none_result_becomes_ok(dispatcher):
    response = dispatcher.handle({"jsonrpc": "2.0", "id": 8, "method": "t.none"})
    assert response["result"] == {"ok": True}


def test_scalar_result_is_internal_error(dispatcher):
    response = dispatcher.handle({"jsonrpc": "2.0", "id": 9, "method": "t.scalar"})
    assert response["error"]["code"] == -32603


def test_encode_is_single_line_utf8(dispatcher):
    response = {"jsonrpc": "2.0", "id": 1, "result": {"name": "Päd\nline", "x": 1.5}}
    line = dispatcher.encode(response)
    assert line.endswith(b"\n")
    assert line.count(b"\n") == 1
    decoded = json.loads(line.decode("utf-8"))
    assert decoded["result"]["name"] == "Päd\\nline" or decoded["result"]["name"] == "Päd\nline"
    assert decoded["result"]["x"] == 1.5


def test_encode_handles_nan(dispatcher):
    line = dispatcher.encode({"jsonrpc": "2.0", "id": 1, "result": {"x": float("nan")}})
    decoded = json.loads(line.decode("utf-8"))
    assert decoded["error"]["code"] == -32603
    assert decoded["id"] == 1


def test_live_rpc_error_to_dict():
    err = LiveRpcError(-32001, "msg", {"reason": "x"})
    assert err.to_dict() == {"code": -32001, "message": "msg", "data": {"reason": "x"}}
    assert LiveRpcError(-32603, "m").to_dict() == {"code": -32603, "message": "m"}


def test_error_helpers():
    err = errors.not_found("parameter", name="Cutoff", available=["A", "B"])
    assert err.data == {"kind": "parameter", "name": "Cutoff", "available": ["A", "B"]}
    assert "Cutoff" in err.message and "A, B" in err.message
    err = errors.confirm_required("song.delete_track", "Bass (track 2)")
    assert err.code == -32002
    assert err.data == {"method": "song.delete_track", "target": "Bass (track 2)"}
    err = errors.too_large(1000, 2400)
    assert err.data == {"limit": 1000, "got": 2400}
    err = errors.unsupported("Live 12", "11.3.4")
    assert err.data == {"needs": "Live 12", "have": "11.3.4"}
    err = errors.live_error(RuntimeError("bad"))
    assert err.data == {"exception": "RuntimeError", "detail": "bad"}
    assert errors.is_live_exception(RuntimeError("x"))
    assert not errors.is_live_exception(KeyError("x"))
    assert not errors.is_live_exception(err)
