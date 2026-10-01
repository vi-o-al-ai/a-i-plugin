"""Error codes and the LiveRpcError exception shared by every handler.

Codes follow docs/PROTOCOL.md section 3. Handlers raise LiveRpcError (via the
helpers below); the dispatcher turns it into a JSON-RPC error object.
"""

# Standard JSON-RPC 2.0 codes
PARSE_ERROR = -32700
INVALID_REQUEST = -32600
METHOD_NOT_FOUND = -32601
INVALID_PARAMS = -32602
INTERNAL_ERROR = -32603

# Application codes
NOT_FOUND = -32000
INVALID_STATE = -32001
CONFIRM_REQUIRED = -32002
UNSUPPORTED = -32003
LIVE_ERROR = -32004
TOO_LARGE = -32005
TIMEOUT = -32006

CODE_NAMES = {
    PARSE_ERROR: "PARSE_ERROR",
    INVALID_REQUEST: "INVALID_REQUEST",
    METHOD_NOT_FOUND: "METHOD_NOT_FOUND",
    INVALID_PARAMS: "INVALID_PARAMS",
    INTERNAL_ERROR: "INTERNAL_ERROR",
    NOT_FOUND: "NOT_FOUND",
    INVALID_STATE: "INVALID_STATE",
    CONFIRM_REQUIRED: "CONFIRM_REQUIRED",
    UNSUPPORTED: "UNSUPPORTED",
    LIVE_ERROR: "LIVE_ERROR",
    TOO_LARGE: "TOO_LARGE",
    TIMEOUT: "TIMEOUT",
}


class LiveRpcError(Exception):
    """An error that maps 1:1 onto a JSON-RPC error object."""

    def __init__(self, code, message, data=None):
        Exception.__init__(self, message)
        self.code = code
        self.message = message
        self.data = data

    def to_dict(self):
        obj = {"code": self.code, "message": self.message}
        if self.data is not None:
            obj["data"] = self.data
        return obj

    def __repr__(self):
        return "LiveRpcError(%r, %r, %r)" % (self.code, self.message, self.data)


class FrameError(object):
    """Marker queued by the socket thread for a line that could not become a request.

    The socket thread never touches the LOM and never builds responses; it
    only reports *why* a line was unusable so the main thread can answer.
    """

    __slots__ = ("code", "message")

    def __init__(self, code, message):
        self.code = code
        self.message = message

    def __repr__(self):
        return "FrameError(%r, %r)" % (self.code, self.message)


_KIND_LABELS = {
    "track": "Track",
    "return_track": "Return track",
    "scene": "Scene",
    "slot": "Clip slot",
    "clip": "Clip",
    "arrangement_clip": "Arrangement clip",
    "device": "Device",
    "chain": "Chain",
    "parameter": "Parameter",
    "cue_point": "Locator",
    "browser_item": "Browser item",
    "send": "Send",
    "drum_pad": "Drum pad",
}


def _label(kind):
    return _KIND_LABELS.get(kind, kind.replace("_", " ").capitalize())


def not_found(kind, index=None, count=None, **extra):
    """NOT_FOUND (-32000) with {"kind", "index", "count"} or {"kind", "name", "available"}."""
    message = extra.pop("message", None)
    data = {"kind": kind}
    if index is not None:
        data["index"] = index
    if count is not None:
        data["count"] = count
    data.update(extra)
    if message is None:
        label = _label(kind)
        if index is not None and count is not None:
            if count == 0:
                message = "%s %s does not exist (there are no %ss here)" % (label, index, kind.replace("_", " "))
            else:
                message = "%s %s does not exist (valid indexes are 0-%d, count %d)" % (label, index, count - 1, count)
        elif "name" in extra:
            message = "%s '%s' does not exist" % (label, extra["name"])
            available = extra.get("available")
            if available:
                shown = list(available)[:40]
                suffix = ", ..." if len(available) > 40 else ""
                message += " (available: %s%s)" % (", ".join(str(a) for a in shown), suffix)
        elif "uri" in extra:
            message = "%s with uri '%s' does not exist" % (label, extra["uri"])
        else:
            message = "%s does not exist" % label
    return LiveRpcError(NOT_FOUND, message, data)


def invalid_state(reason, message, **extra):
    """INVALID_STATE (-32001): the object exists but the operation does not apply."""
    data = {"reason": reason}
    data.update(extra)
    return LiveRpcError(INVALID_STATE, message, data)


def confirm_required(method, target):
    """CONFIRM_REQUIRED (-32002): destructive call without "confirm": true."""
    message = '%s is destructive and would affect %s; call again with "confirm": true to proceed' % (method, target)
    return LiveRpcError(CONFIRM_REQUIRED, message, {"method": method, "target": target})


def unsupported(needs, have, message=None):
    """UNSUPPORTED (-32003): the running Live lacks the API."""
    if message is None:
        message = "This operation needs %s but the running Live is %s" % (needs, have)
    return LiveRpcError(UNSUPPORTED, message, {"needs": needs, "have": have})


def invalid_params(message, **data):
    """INVALID_PARAMS (-32602)."""
    return LiveRpcError(INVALID_PARAMS, message, data or None)


def too_large(limit, got, what="items"):
    """TOO_LARGE (-32005)."""
    message = "Request has %d %s; the limit per request is %d" % (got, what, limit)
    return LiveRpcError(TOO_LARGE, message, {"limit": limit, "got": got})


def live_error(exc):
    """LIVE_ERROR (-32004): the LOM raised."""
    detail = str(exc)
    name = type(exc).__name__
    message = "Live raised %s: %s" % (name, detail) if detail else "Live raised %s" % name
    return LiveRpcError(LIVE_ERROR, message, {"exception": name, "detail": detail})


def internal_error(exc):
    """INTERNAL_ERROR (-32603): a bug in the script."""
    detail = str(exc)
    name = type(exc).__name__
    message = "Internal error in ClaudeLive: %s: %s" % (name, detail)
    return LiveRpcError(INTERNAL_ERROR, message, {"exception": name, "detail": detail})


def is_live_exception(exc):
    """True when an exception most likely came from the LOM rather than from our code.

    Live's boost.python bindings raise RuntimeError for almost every refused
    operation, and its own exception classes live in the Live.* modules.
    """
    if isinstance(exc, LiveRpcError):
        return False
    module = getattr(type(exc), "__module__", "") or ""
    if module == "Live" or module.startswith("Live."):
        return True
    return isinstance(exc, RuntimeError) and not isinstance(exc, (RecursionError, NotImplementedError))
