"""JSON-RPC 2.0 validation, routing and response building. Main thread only."""
import json
import traceback

from . import errors
from .errors import LiveRpcError, FrameError


def error_response(request_id, code, message, data=None):
    err = {"code": code, "message": message}
    if data is not None:
        err["data"] = data
    return {"jsonrpc": "2.0", "id": request_id, "error": err}


def result_response(request_id, result):
    return {"jsonrpc": "2.0", "id": request_id, "result": result}


def valid_id(value):
    if isinstance(value, bool):
        return False
    return isinstance(value, (int, str))


_valid_id = valid_id


def request_id_of(payload):
    """The echoable id of a parsed request, or None (also for FrameErrors / garbage)."""
    if isinstance(payload, dict):
        request_id = payload.get("id")
        if valid_id(request_id):
            return request_id
    return None


class Dispatcher(object):
    """Turns a parsed request (or a FrameError marker) into a response dict, or None."""

    def __init__(self, ctx, methods, logger):
        self.ctx = ctx
        self.methods = methods
        self.logger = logger
        self.handled = 0

    def handle(self, payload):
        """Return a response dict, or None for notifications (which v1 ignores)."""
        if isinstance(payload, FrameError):
            return error_response(None, payload.code, payload.message)

        if not isinstance(payload, dict):
            if isinstance(payload, list):
                return error_response(None, errors.INVALID_REQUEST, "Batch requests are not supported")
            return error_response(None, errors.INVALID_REQUEST, "Request must be a JSON object")

        has_id = "id" in payload
        request_id = payload.get("id")
        if has_id and not valid_id(request_id):
            return error_response(None, errors.INVALID_REQUEST, "Request id must be an integer or a string")

        if payload.get("jsonrpc") != "2.0":
            return error_response(request_id, errors.INVALID_REQUEST, 'Request must have "jsonrpc": "2.0"')

        method = payload.get("method")
        if not isinstance(method, str) or not method:
            return error_response(request_id, errors.INVALID_REQUEST, 'Request must have a string "method"')

        if not has_id:
            # Notification: reserved for a future event stream; v1 ignores them.
            self.logger.debug("ignoring notification %s", method)
            return None

        params = payload.get("params", {})
        if params is None:
            params = {}
        if not isinstance(params, dict):
            return error_response(request_id, errors.INVALID_PARAMS, "params must be a JSON object with named parameters")

        handler = self.methods.get(method)
        if handler is None:
            return error_response(request_id, errors.METHOD_NOT_FOUND,
                                  "Method '%s' does not exist" % method,
                                  {"method": method})

        self.handled += 1
        try:
            result = handler(self.ctx, params)
        except LiveRpcError as exc:
            self.logger.info("%s -> %s %s", method, errors.CODE_NAMES.get(exc.code, exc.code), exc.message)
            return {"jsonrpc": "2.0", "id": request_id, "error": exc.to_dict()}
        except Exception as exc:
            # AssertionError included: the client must get *some* answer rather
            # than waiting for its timeout (PROTOCOL.md section 4.5).
            if errors.is_live_exception(exc):
                self.logger.warning("%s: Live raised %s: %s", method, type(exc).__name__, exc)
                return {"jsonrpc": "2.0", "id": request_id, "error": errors.live_error(exc).to_dict()}
            self.logger.error("internal error in %s:\n%s", method, traceback.format_exc())
            return {"jsonrpc": "2.0", "id": request_id, "error": errors.internal_error(exc).to_dict()}

        if result is None:
            result = {"ok": True}
        elif not isinstance(result, dict):
            self.logger.error("handler %s returned non-object result %r", method, type(result).__name__)
            return error_response(request_id, errors.INTERNAL_ERROR,
                                  "Handler for %s returned a non-object result" % method)
        return result_response(request_id, result)

    def encode(self, response):
        """Encode a response dict as one newline-terminated UTF-8 line. Never raises."""
        request_id = response.get("id") if isinstance(response, dict) else None
        try:
            text = json.dumps(response, ensure_ascii=False, allow_nan=False, default=_json_default)
            # json.dumps never emits raw newlines, but be defensive about strings from Live.
            text = text.replace("\r", "\\r").replace("\n", "\\n")
            # Strings coming out of Live may hold lone surrogates; never let encode() raise.
            return (text + "\n").encode("utf-8", "replace")
        except (TypeError, ValueError) as exc:
            self.logger.error("response not serialisable: %s", exc)
            fallback = error_response(request_id, errors.INTERNAL_ERROR,
                                      "Response could not be serialised: %s" % exc)
            return (json.dumps(fallback, ensure_ascii=True) + "\n").encode("utf-8", "replace")


def _json_default(value):
    if isinstance(value, float):
        return str(value)
    try:
        return int(value)
    except (TypeError, ValueError):
        return str(value)
