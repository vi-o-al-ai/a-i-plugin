"""automation.* handlers: clip envelopes via automation_envelope / insert_step / value_at_time."""
import math

import Live

from .. import errors, lom

# Every resulting step is one undoable insert_step call on the main thread, and every
# sample one value_at_time call; 2000 keeps a single request inside the tick budget class.
MAX_POINTS = 2000
MAX_SAMPLES = 2000
MIN_RESOLUTION = 1.0e-3
MODES = ("steps", "ramp")
DEFAULT_MODE = "ramp"


def _target(ctx, params, require_parameter=True):
    """(ClipRef, DeviceRef or None, ParamRef or None)."""
    ref = lom.resolve_clip(ctx.song(), params)
    device_path = lom.get_str(params, "device_path", None)
    if device_path is None:
        if require_parameter:
            raise errors.invalid_params("Missing required parameter 'device_path'", parameter="device_path")
        return ref, None, None
    dref = lom.resolve_device_path(ref.track, device_path)
    if "parameter" not in params:
        if require_parameter:
            raise errors.invalid_params("Missing required parameter 'parameter'", parameter="parameter")
        return ref, dref, None
    pref = lom.resolve_parameter(dref.device, params["parameter"])
    return ref, dref, pref


def _clip_end(clip):
    candidates = []
    for attr in ("loop_end", "end_marker", "length"):
        value = lom.safe_get(clip, attr)
        if lom.is_number(value):
            candidates.append(float(value))
    return max(candidates) if candidates else 0.0


def _envelope(clip, param):
    fn = lom.safe_get(clip, "automation_envelope")
    if fn is None:
        return None
    return lom.live_call(fn, param)


def get(ctx, params):
    ref, _dref, pref = _target(ctx, params)
    clip = ref.clip
    from_time = lom.get_float(params, "from_time", 0.0, minimum=0.0)
    default_span = max(_clip_end(clip) - from_time, 0.0)
    time_span = lom.get_float(params, "time_span", default_span, minimum=0.0)
    resolution = lom.get_float(params, "resolution", 0.25, minimum=MIN_RESOLUTION)
    parameter = lom.parameter_dict(pref.param, pref.index, pref.name, pref.original_name)
    envelope = _envelope(clip, pref.param)
    if envelope is None:
        return {"exists": False, "points": [], "parameter": parameter}
    # Sample [from_time, from_time + time_span) so the clip end itself is not read.
    count = int(math.ceil(time_span / resolution - 1.0e-9)) if time_span > 0 else 1
    count = max(1, count)
    if count > MAX_SAMPLES:
        raise errors.too_large(MAX_SAMPLES, count, "sample points (raise 'resolution' or shrink 'time_span')")
    points = []
    for i in range(count):
        t = from_time + i * resolution
        value = lom.live_call(envelope.value_at_time, t)
        points.append({"time": round(t, 9), "value": lom._num(value)})
    return {"exists": True, "points": points, "parameter": parameter}


def _parse_points(params, low, high):
    raw = lom.get_list(params, "points")
    if not raw:
        raise errors.invalid_params("points must contain at least one {\"time\", \"value\"}", parameter="points")
    if len(raw) > MAX_POINTS:
        raise errors.too_large(MAX_POINTS, len(raw), "points")
    points = []
    for i, item in enumerate(raw):
        if not isinstance(item, dict):
            raise errors.invalid_params("points[%d] must be an object" % i, parameter="points")
        t = lom.get_float(item, "time", minimum=0.0)
        v = lom.get_float(item, "value")
        v, _clamped = lom.clamp(v, low, high)
        points.append((t, v))
    points.sort(key=lambda p: p[0])
    # Later duplicates at the same time win.
    deduped = []
    for t, v in points:
        if deduped and abs(deduped[-1][0] - t) < 1.0e-9:
            deduped[-1] = (t, v)
        else:
            deduped.append((t, v))
    return deduped


def _re_enable(param):
    state_cls = getattr(getattr(Live, "DeviceParameter", None), "AutomationState", None)
    overridden = getattr(state_cls, "overridden", None) if state_cls is not None else None
    if overridden is None:
        return
    try:
        if param.automation_state == overridden:
            param.re_enable_automation()
    except AssertionError:
        raise
    except Exception:
        pass


def set_automation(ctx, params):
    ref, _dref, pref = _target(ctx, params)
    clip = ref.clip
    param = pref.param
    mode = lom.get_choice(params, "mode", MODES, DEFAULT_MODE)
    resolution = lom.get_float(params, "resolution", 0.0625, minimum=MIN_RESOLUTION)
    low = float(lom.safe_get(param, "min", 0.0))
    high = float(lom.safe_get(param, "max", 1.0))
    if low > high:
        low, high = high, low
    points = _parse_points(params, low, high)
    quantized = bool(lom.safe_get(param, "is_quantized", False))
    if quantized:
        points = [(t, float(round(v))) for t, v in points]

    # Expand into steps and validate the size *before* touching the clip, so a rejected
    # request leaves no empty envelope behind.
    end = _clip_end(clip)
    last_time = points[-1][0]
    if end <= last_time:
        end = last_time + resolution
    steps = []  # (time, length, value)
    if mode == "steps" or quantized:
        for i, (t, v) in enumerate(points):
            next_time = points[i + 1][0] if i + 1 < len(points) else end
            length = next_time - t
            if length <= 0:
                continue
            steps.append((t, length, v))
    else:
        for i, (t, v) in enumerate(points):
            if i + 1 >= len(points):
                steps.append((t, end - t, v))
                break
            next_time, next_value = points[i + 1]
            span = next_time - t
            if span <= 0:
                continue
            count = max(1, int(round(span / resolution)))
            step_length = span / float(count)
            for k in range(count):
                start = t + k * step_length
                fraction = (k * step_length) / span
                value = v + (next_value - v) * fraction
                steps.append((start, step_length, value))
    if len(steps) > MAX_POINTS:
        raise errors.too_large(MAX_POINTS, len(steps), "automation steps (raise 'resolution')")

    envelope = _envelope(clip, param)
    if envelope is None:
        create = lom.safe_get(clip, "create_automation_envelope")
        if create is None:
            raise errors.unsupported("Clip.create_automation_envelope", ctx.version["string"])
        envelope = lom.live_call(create, param)
        if envelope is None:
            raise errors.invalid_state("no_envelope", "Live could not create an automation envelope for '%s' on this clip"
                                       % pref.name)
    inserted = 0
    for t, length, v in steps:
        lom.live_call(envelope.insert_step, t, length, v)
        inserted += 1
    _re_enable(param)
    # Quantized parameters are always written as steps (a ramp between discrete values
    # makes no sense), and the result says so.
    return {"inserted": inserted, "exists": True, "mode": "steps" if quantized else mode}


def clear(ctx, params):
    ref, dref, pref = _target(ctx, params, require_parameter=False)
    clip = ref.clip
    if pref is not None:
        fn = lom.safe_get(clip, "clear_envelope")
        if fn is None:
            raise errors.unsupported("Clip.clear_envelope", ctx.version["string"])
        lom.live_call(fn, pref.param)
        return {"cleared": pref.name}
    if dref is not None:
        raise errors.invalid_params("Give 'parameter' together with 'device_path', or neither to clear all envelopes",
                                    parameter="parameter")
    name = lom.safe_get(clip, "name", "")
    where = "slot %s" % ref.slot_index if ref.slot_index is not None else "arrangement_index %s" % ref.arrangement_index
    lom.require_confirm(params, "automation.clear", "all envelopes of clip '%s' (track %s, %s)" % (name, ref.track_index, where))
    fn = lom.safe_get(clip, "clear_all_envelopes")
    if fn is None:
        raise errors.unsupported("Clip.clear_all_envelopes", ctx.version["string"])
    lom.live_call(fn)
    return {"cleared": "all"}


METHODS = {
    "automation.get": get,
    "automation.set": set_automation,
    "automation.clear": clear,
}
