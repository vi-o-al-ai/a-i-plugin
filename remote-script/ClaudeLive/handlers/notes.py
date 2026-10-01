"""notes.* handlers built on the Live 11+ note API:
get_notes_extended / add_new_notes / remove_notes_* / get_notes_by_id + apply_note_modifications.
"""
import math

import Live

from .. import errors, lom

MAX_NOTES = 1000
VELOCITY_DEFAULT = 100.0
RELEASE_VELOCITY_DEFAULT = 64.0
MIN_DURATION = 1.0e-4

# JSON field -> Live attribute
FIELD_TO_ATTR = {
    "pitch": "pitch",
    "start": "start_time",
    "duration": "duration",
    "velocity": "velocity",
    "mute": "mute",
    "probability": "probability",
    "velocity_deviation": "velocity_deviation",
    "release_velocity": "release_velocity",
}
REQUIRED_FIELDS = ("pitch", "start", "duration")
REDUCED_SPEC_KEYS = ("pitch", "start_time", "duration", "velocity", "mute")


def _midi_clip(ctx, params):
    ref = lom.resolve_clip(ctx.song(), params)
    if not lom.safe_get(ref.clip, "is_midi_clip", False):
        where = "slot %s" % ref.slot_index if ref.slot_index is not None else "arrangement_index %s" % ref.arrangement_index
        raise errors.invalid_state("not_midi", "Clip '%s' (track %s, %s) is an audio clip; notes need a MIDI clip" % (
            lom.safe_get(ref.clip, "name", ""), ref.track_index, where), track=ref.track_index)
    return ref


def _range(params, default_from_time, default_time_span):
    from_time = lom.get_float(params, "from_time", default_from_time)
    time_span = lom.get_float(params, "time_span", default_time_span, exclusive_minimum=0.0)
    from_pitch = lom.get_int(params, "from_pitch", 0, minimum=0, maximum=127)
    pitch_span = lom.get_int(params, "pitch_span", 128, minimum=1, maximum=128)
    if from_pitch + pitch_span > 128:
        pitch_span = 128 - from_pitch
    return from_pitch, pitch_span, from_time, time_span


def _number(spec, key, label, minimum=None, maximum=None, exclusive_minimum=None):
    value = spec[key]
    if not lom.is_number(value):
        raise errors.invalid_params("%s.%s must be a finite number (got %r)" % (label, key, value), field=key)
    value = float(value)
    if minimum is not None and value < minimum:
        raise errors.invalid_params("%s.%s must be >= %s (got %s)" % (label, key, minimum, value), field=key)
    if exclusive_minimum is not None and value <= exclusive_minimum:
        raise errors.invalid_params("%s.%s must be > %s (got %s)" % (label, key, exclusive_minimum, value), field=key)
    if maximum is not None and value > maximum:
        raise errors.invalid_params("%s.%s must be <= %s (got %s)" % (label, key, maximum, value), field=key)
    return value


def validate_note_fields(spec, label, partial=False):
    """Validate a NoteSpec (or a partial change) and return {live_attr: value}."""
    if not isinstance(spec, dict):
        raise errors.invalid_params("%s must be an object" % label)
    out = {}
    if "pitch" in spec or not partial:
        if "pitch" not in spec:
            raise errors.invalid_params("%s.pitch is required" % label, field="pitch")
        pitch = spec["pitch"]
        if isinstance(pitch, float) and pitch.is_integer():
            pitch = int(pitch)
        if isinstance(pitch, bool) or not isinstance(pitch, int) or pitch < 0 or pitch > 127:
            raise errors.invalid_params("%s.pitch must be an integer 0-127 (got %r)" % (label, spec["pitch"]), field="pitch")
        out["pitch"] = pitch
    if "start" in spec or not partial:
        if "start" not in spec:
            raise errors.invalid_params("%s.start is required" % label, field="start")
        out["start_time"] = _number(spec, "start", label, minimum=0.0)
    if "duration" in spec or not partial:
        if "duration" not in spec:
            raise errors.invalid_params("%s.duration is required" % label, field="duration")
        out["duration"] = _number(spec, "duration", label, exclusive_minimum=0.0)
    if "velocity" in spec:
        velocity = _number(spec, "velocity", label, minimum=0.0, maximum=127.0)
        out["velocity"] = max(1.0, velocity)
    elif not partial:
        out["velocity"] = VELOCITY_DEFAULT
    if "mute" in spec:
        if not isinstance(spec["mute"], bool):
            raise errors.invalid_params("%s.mute must be true or false" % label, field="mute")
        out["mute"] = spec["mute"]
    elif not partial:
        out["mute"] = False
    if "probability" in spec:
        out["probability"] = _number(spec, "probability", label, minimum=0.0, maximum=1.0)
    elif not partial:
        out["probability"] = 1.0
    if "velocity_deviation" in spec:
        out["velocity_deviation"] = _number(spec, "velocity_deviation", label, minimum=-127.0, maximum=127.0)
    elif not partial:
        out["velocity_deviation"] = 0.0
    if "release_velocity" in spec:
        out["release_velocity"] = _number(spec, "release_velocity", label, minimum=0.0, maximum=127.0)
    elif not partial:
        out["release_velocity"] = RELEASE_VELOCITY_DEFAULT
    return out


def _make_spec(fields):
    spec_cls = getattr(Live.Clip, "MidiNoteSpecification", None)
    if spec_cls is None:
        raise errors.unsupported("Live.Clip.MidiNoteSpecification (Live 11+)", "this Live build")
    try:
        return spec_cls(**fields)
    except TypeError:
        reduced = dict((k, v) for k, v in fields.items() if k in REDUCED_SPEC_KEYS)
        return spec_cls(**reduced)


def _specs_from_params(params):
    notes = lom.get_list(params, "notes")
    if len(notes) > MAX_NOTES:
        raise errors.too_large(MAX_NOTES, len(notes), "notes")
    specs = []
    for i, spec in enumerate(notes):
        fields = validate_note_fields(spec, "notes[%d]" % i)
        specs.append(_make_spec(fields))
    return specs


def _deselect(clip):
    fn = lom.safe_get(clip, "deselect_all_notes")
    if fn is not None:
        try:
            fn()
        except AssertionError:
            raise
        except Exception:
            pass


def _count(clip):
    return len(lom.as_list(lom.all_notes(clip)))


def get(ctx, params):
    ref = _midi_clip(ctx, params)
    clip = ref.clip
    loop_end = lom.safe_get(clip, "loop_end")
    default_span = float(loop_end) if lom.is_number(loop_end) and loop_end > 0 else lom.NOTE_ALL_TIME_SPAN
    from_pitch, pitch_span, from_time, time_span = _range(params, 0.0, default_span)
    notes = lom.live_call(clip.get_notes_extended, from_pitch, pitch_span, from_time, time_span)
    dicts = [lom.note_dict(n) for n in lom.as_list(notes)]
    dicts.sort(key=lambda n: (n["start"] if n["start"] is not None else 0.0, n["pitch"] if n["pitch"] is not None else 0))
    return {"notes": dicts, "count": len(dicts), "clip_length": lom._num(lom.safe_get(clip, "length"))}


def add(ctx, params):
    ref = _midi_clip(ctx, params)
    specs = _specs_from_params(params)
    if specs:
        lom.live_call(ref.clip.add_new_notes, tuple(specs))
        _deselect(ref.clip)
    return {"added": len(specs), "note_count": _count(ref.clip)}


def replace(ctx, params):
    ref = _midi_clip(ctx, params)
    specs = _specs_from_params(params)
    clip = ref.clip
    removed = _count(clip)
    if removed:
        lom.live_call(clip.remove_notes_extended, lom.NOTE_ALL_FROM_PITCH, lom.NOTE_ALL_PITCH_SPAN,
                      lom.NOTE_ALL_FROM_TIME, lom.NOTE_ALL_TIME_SPAN)
    if specs:
        lom.live_call(clip.add_new_notes, tuple(specs))
        _deselect(clip)
    return {"removed": removed, "added": len(specs), "note_count": _count(clip)}


def _note_ids(params, key="note_ids"):
    ids = lom.get_list(params, key, None)
    if ids is None:
        return None
    out = []
    for i, value in enumerate(ids):
        if isinstance(value, float) and value.is_integer():
            value = int(value)
        if isinstance(value, bool) or not isinstance(value, int) or value < 0:
            raise errors.invalid_params("%s[%d] must be a non-negative integer note id (got %r)" % (key, i, value),
                                        parameter=key)
        out.append(value)
    return out


def remove(ctx, params):
    ref = _midi_clip(ctx, params)
    clip = ref.clip
    ids = _note_ids(params)
    before = _count(clip)
    if ids is not None:
        if ids:
            lom.live_call(clip.remove_notes_by_id, tuple(ids))
    else:
        from_pitch, pitch_span, from_time, time_span = _range(params, lom.NOTE_ALL_FROM_TIME, lom.NOTE_ALL_TIME_SPAN)
        lom.live_call(clip.remove_notes_extended, from_pitch, pitch_span, from_time, time_span)
    after = _count(clip)
    return {"removed": max(0, before - after), "note_count": after}


def modify(ctx, params):
    ref = _midi_clip(ctx, params)
    clip = ref.clip
    changes = lom.get_list(params, "changes")
    if len(changes) > MAX_NOTES:
        raise errors.too_large(MAX_NOTES, len(changes), "changes")
    parsed = []
    for i, change in enumerate(changes):
        label = "changes[%d]" % i
        if not isinstance(change, dict):
            raise errors.invalid_params("%s must be an object" % label)
        note_id = change.get("id")
        if isinstance(note_id, float) and note_id.is_integer():
            note_id = int(note_id)
        if isinstance(note_id, bool) or not isinstance(note_id, int):
            raise errors.invalid_params("%s.id must be an integer note id" % label, field="id")
        parsed.append((note_id, validate_note_fields(change, label, partial=True)))
    if not parsed:
        return {"modified": 0, "missing_ids": []}
    ids = tuple(sorted(set(note_id for note_id, _f in parsed)))
    vector = lom.live_call(clip.get_notes_by_id, ids)
    by_id = {}
    for note in lom.as_list(vector):
        by_id[lom._int_or(lom.safe_get(note, "note_id"), -1)] = note
    modified = 0
    missing = []
    for note_id, fields in parsed:
        note = by_id.get(note_id)
        if note is None:
            if note_id not in missing:
                missing.append(note_id)
            continue
        for attr, value in fields.items():
            lom.live_set(note, attr, value)
        modified += 1
    if modified:
        lom.live_call(clip.apply_note_modifications, vector)
    return {"modified": modified, "missing_ids": missing}


def _snap(time_value, grid, swing):
    step = int(math.floor(time_value / grid + 0.5))
    target = step * grid
    if swing > 0.0 and step % 2 == 1:
        target += swing * grid / 2.0
    return target


def quantize(ctx, params):
    ref = _midi_clip(ctx, params)
    clip = ref.clip
    grid = lom.get_float(params, "grid", 0.25, exclusive_minimum=0.0)
    amount = lom.get_float(params, "amount", 1.0, minimum=0.0, maximum=1.0)
    swing = lom.get_float(params, "swing", 0.0, minimum=0.0, maximum=1.0)
    quantize_ends = lom.get_bool(params, "quantize_ends", False)
    vector = lom.live_call(lom.all_notes, clip)
    modified = 0
    for note in lom.as_list(vector):
        start = float(lom.safe_get(note, "start_time", 0.0))
        duration = float(lom.safe_get(note, "duration", 0.0))
        new_start = start + (_snap(start, grid, swing) - start) * amount
        new_start = max(0.0, new_start)
        new_duration = duration
        if quantize_ends:
            end = start + duration
            new_end = end + (_snap(end, grid, swing) - end) * amount
            new_duration = max(MIN_DURATION, new_end - new_start)
        changed = False
        if abs(new_start - start) > 1.0e-9:
            lom.live_set(note, "start_time", new_start)
            changed = True
        if abs(new_duration - duration) > 1.0e-9:
            lom.live_set(note, "duration", new_duration)
            changed = True
        if changed:
            modified += 1
    if modified:
        lom.live_call(clip.apply_note_modifications, vector)
    return {"modified": modified}


def transpose(ctx, params):
    ref = _midi_clip(ctx, params)
    clip = ref.clip
    semitones = lom.get_int(params, "semitones", minimum=-127, maximum=127)
    from_pitch, pitch_span, from_time, time_span = _range(params, lom.NOTE_ALL_FROM_TIME, lom.NOTE_ALL_TIME_SPAN)
    vector = lom.live_call(clip.get_notes_extended, from_pitch, pitch_span, from_time, time_span)
    modified = 0
    if semitones != 0:
        for note in lom.as_list(vector):
            pitch = int(lom.safe_get(note, "pitch", 0))
            new_pitch, _clamped = lom.clamp(pitch + semitones, 0, 127)
            if new_pitch != pitch:
                lom.live_set(note, "pitch", new_pitch)
                modified += 1
    if modified:
        lom.live_call(clip.apply_note_modifications, vector)
    return {"modified": modified}


METHODS = {
    "notes.get": get,
    "notes.add": add,
    "notes.replace": replace,
    "notes.remove": remove,
    "notes.modify": modify,
    "notes.quantize": quantize,
    "notes.transpose": transpose,
}
