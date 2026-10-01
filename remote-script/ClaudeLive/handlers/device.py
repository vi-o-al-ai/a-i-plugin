"""device.* handlers."""
import re

from .. import errors, lom
from ..errors import LiveRpcError

MAX_DEPTH = 8
_NUMBER_RE = re.compile(r"[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?")


def _device_ref(ctx, params):
    song = ctx.song()
    tref = lom.track_from_params(song, params)
    path = params.get("path")
    if path is None:
        path = params.get("device_path")
    dref = lom.resolve_device_path(tref.track, path)
    return song, tref, dref


def list_devices(ctx, params):
    song = ctx.song()
    tref = lom.track_from_params(song, params)
    include_params = lom.get_bool(params, "include_params", False)
    depth = lom.get_int(params, "depth", 2, minimum=0, maximum=MAX_DEPTH)
    mixer = lom.MixerPseudoDevice(tref.track)
    return {
        "devices": lom.device_entries(tref.track, include_params, depth),
        "mixer": {"path": lom.MIXER_PATH, "parameters": mixer.parameter_dicts()},
    }


def get(ctx, params):
    _song, _tref, dref = _device_ref(ctx, params)
    include_params = lom.get_bool(params, "include_params", True)
    depth = lom.get_int(params, "depth", 2, minimum=0, maximum=MAX_DEPTH)
    if dref.is_mixer:
        detail = dref.device.detail()
        if not include_params:
            detail.pop("parameters", None)
        return detail
    return lom.device_detail(dref.device, dref.path, include_params, depth)


def _param_ref(dref, params, key="parameter"):
    if key not in params:
        raise errors.invalid_params("Missing required parameter '%s'" % key, parameter=key)
    return lom.resolve_parameter(dref.device, params[key])


def _param_result(pref):
    result = lom.parameter_dict(pref.param, pref.index, pref.name, pref.original_name)
    if pref.ambiguous:
        result["ambiguous"] = True
    return result


def get_parameter(ctx, params):
    _song, _tref, dref = _device_ref(ctx, params)
    pref = _param_ref(dref, params)
    return _param_result(pref)


def _display_number(text):
    if text is None:
        return None
    lowered = text.strip().lower().replace(",", ".")
    if "inf" in lowered:
        return float("-inf") if "-" in lowered else float("inf")
    match = _NUMBER_RE.search(lowered)
    if not match:
        return None
    try:
        return float(match.group(0))
    except ValueError:
        return None


def _value_for_display(param, wanted, low, high):
    """Find a continuous value whose str_for_value matches `wanted`.

    Tries an exact (case-insensitive) match over a coarse sweep first, then uses
    the numeric part of the display strings and bisects, assuming the display is
    monotonic in the value (true for every native Live parameter).
    """
    wanted_norm = " ".join(wanted.strip().lower().split())

    def display(value):
        return " ".join(lom.value_display(param, value).strip().lower().split())

    steps = 64
    span = high - low
    samples = [low + span * i / float(steps) for i in range(steps + 1)]
    numeric = []
    for value in samples:
        text = display(value)
        if text == wanted_norm:
            return value
        number = _display_number(text)
        if number is not None:
            numeric.append((value, number))
    target = _display_number(wanted_norm)
    if target is None or len(numeric) < 2:
        return None
    finite = [(v, n) for v, n in numeric if n not in (float("inf"), float("-inf"))]
    if target in (float("inf"), float("-inf")):
        candidates = [v for v, n in numeric if n == target]
        return candidates[0] if candidates else None
    if len(finite) < 2:
        return None
    increasing = finite[-1][1] >= finite[0][1]
    best_index = min(range(len(finite)), key=lambda i: abs(finite[i][1] - target))
    lo_value = finite[max(0, best_index - 1)][0]
    hi_value = finite[min(len(finite) - 1, best_index + 1)][0]
    best_value = finite[best_index][0]
    best_delta = abs(finite[best_index][1] - target)
    for _ in range(48):
        mid = (lo_value + hi_value) / 2.0
        number = _display_number(display(mid))
        if number is None:
            break
        delta = abs(number - target)
        if delta < best_delta:
            best_delta, best_value = delta, mid
        if display(mid) == wanted_norm:
            return mid
        if (number < target) == increasing:
            lo_value = mid
        else:
            hi_value = mid
        if hi_value - lo_value < 1.0e-9:
            break
    tolerance = max(0.05, abs(target) * 0.01)
    if best_delta <= tolerance:
        return best_value
    return None


def _target_value(pref, params):
    """Return (value, clamped) for exactly one of value / normalized / display."""
    given = [key for key in ("value", "normalized", "display") if params.get(key) is not None]
    if len(given) != 1:
        raise errors.invalid_params("Give exactly one of 'value', 'normalized' or 'display' (got %s)" % (
            ", ".join(given) if given else "none"), parameter="value")
    param = pref.param
    low = float(lom.safe_get(param, "min", 0.0))
    high = float(lom.safe_get(param, "max", 1.0))
    if low > high:
        low, high = high, low
    quantized = bool(lom.safe_get(param, "is_quantized", False))
    items = [str(i) for i in lom.as_list(lom.safe_get(param, "value_items"))] if quantized else None
    key = given[0]
    clamped = False
    if key == "value":
        value = lom.get_float(params, "value")
        if quantized and abs(value - round(value)) > 1.0e-6:
            raise errors.invalid_params(
                "Parameter '%s' is quantized; value must be one of the allowed steps %s..%s (or use 'display')" % (
                    pref.name, int(low), int(high)), parameter="value", value_items=items)
        value, clamped = lom.clamp(value, low, high)
        if quantized:
            value = float(round(value))
    elif key == "normalized":
        normalized = lom.get_float(params, "normalized")
        normalized, clamped = lom.clamp(normalized, 0.0, 1.0)
        value = low + normalized * (high - low)
        if quantized:
            value = float(round(value))
    else:
        display = lom.get_str(params, "display")
        wanted = display.strip().lower()
        if quantized:
            index = None
            for i, item in enumerate(items):
                if item.strip().lower() == wanted:
                    index = i
                    break
            if index is None:
                raise errors.invalid_params("display %r does not match any value of parameter '%s' (allowed: %s)" % (
                    display, pref.name, ", ".join(items)), parameter="display", value_items=items)
            value = low + index
        else:
            value = _value_for_display(param, display, low, high)
            if value is None:
                raise errors.invalid_params(
                    "Could not find a value of '%s' whose display matches %r (range %s to %s)" % (
                        pref.name, display, lom.value_display(param, low), lom.value_display(param, high)),
                    parameter="display")
    return value, clamped


def _apply(pref, params):
    previous = lom.value_and_display(pref.param)
    value, clamped = _target_value(pref, params)
    lom.live_set(pref.param, "value", value)
    return {"parameter": _param_result(pref), "previous": previous, "clamped": clamped}


def set_parameter(ctx, params):
    _song, _tref, dref = _device_ref(ctx, params)
    pref = _param_ref(dref, params)
    return _apply(pref, params)


def set_parameters(ctx, params):
    _song, _tref, dref = _device_ref(ctx, params)
    values = lom.get_list(params, "values")
    results = []
    failures = []
    for i, item in enumerate(values):
        if not isinstance(item, dict):
            failures.append({"parameter": None, "index": i, "code": errors.INVALID_PARAMS,
                             "message": "values[%d] must be an object" % i})
            continue
        try:
            pref = _param_ref(dref, item)
            results.append(_apply(pref, item))
        except LiveRpcError as exc:
            failures.append({"parameter": item.get("parameter"), "index": i, "code": exc.code, "message": exc.message})
    return {"results": results, "errors": failures}


def _device_on_parameter(device):
    parameters = lom.as_list(lom.safe_get(device, "parameters"))
    if parameters:
        first_name = str(lom.safe_get(parameters[0], "name", ""))
        if first_name.startswith("Device On"):
            return parameters[0]
    for param in parameters:
        name = str(lom.safe_get(param, "name", ""))
        original = str(lom.safe_get(param, "original_name", ""))
        if name.startswith("Device On") or original.startswith("Device On"):
            return param
    return None


def set_enabled(ctx, params):
    _song, _tref, dref = _device_ref(ctx, params)
    enabled = lom.get_bool(params, "enabled")
    if dref.is_mixer:
        raise errors.invalid_state("mixer", "The mixer cannot be switched off; use the Track Activator parameter")
    param = _device_on_parameter(dref.device)
    if param is None:
        raise errors.invalid_state("no_device_on_parameter", "Device '%s' has no 'Device On' parameter" % (
            lom.safe_get(dref.device, "name", "?")), path=dref.path)
    high = lom.safe_get(param, "max", 1.0)
    low = lom.safe_get(param, "min", 0.0)
    lom.live_set(param, "value", high if enabled else low)
    return {"is_active": bool(lom.safe_get(dref.device, "is_active", enabled)), "path": dref.path}


def delete(ctx, params):
    _song, tref, dref = _device_ref(ctx, params)
    if dref.is_mixer:
        raise errors.invalid_state("mixer", "The mixer device cannot be deleted")
    name = lom.safe_get(dref.device, "name", "")
    lom.require_confirm(params, "device.delete", "%s (%s, path %s)" % (
        name, lom.track_label(tref.track, tref.index, tref.track_type), dref.path))
    container = dref.container
    delete_fn = lom.safe_get(container, "delete_device")
    if delete_fn is None:
        raise errors.unsupported("Track.delete_device / Chain.delete_device", ctx.version["string"])
    lom.live_call(delete_fn, dref.index)
    return {"deleted": name, "path": dref.path}


METHODS = {
    "device.list": list_devices,
    "device.get": get,
    "device.get_parameter": get_parameter,
    "device.set_parameter": set_parameter,
    "device.set_parameters": set_parameters,
    "device.set_enabled": set_enabled,
    "device.delete": delete,
}
