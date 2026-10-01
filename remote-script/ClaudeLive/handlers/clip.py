"""clip.* handlers."""
import Live

from .. import errors, lom

# Public launch-quantization names (PROTOCOL.md section 7, clip.set) mapped to the
# member spellings Live has used, in the order they are tried. Ableton's own enum
# historically carries misspellings (q_sixtenth, q_thirtytwoth); the public names
# are the correct spellings and the script resolves them to whatever exists.
LAUNCH_QUANTIZATION_CANDIDATES = (
    ("q_global", ("q_global",)),
    ("q_none", ("q_none",)),
    ("q_8_bars", ("q_8_bars",)),
    ("q_4_bars", ("q_4_bars",)),
    ("q_2_bars", ("q_2_bars",)),
    ("q_bar", ("q_bar",)),
    ("q_half", ("q_half",)),
    ("q_half_triplet", ("q_half_triplet",)),
    ("q_quarter", ("q_quarter",)),
    ("q_quarter_triplet", ("q_quarter_triplet",)),
    ("q_eight", ("q_eight", "q_eighth")),
    ("q_eight_triplet", ("q_eight_triplet", "q_eighth_triplet")),
    ("q_sixteenth", ("q_sixteenth", "q_sixtenth")),
    ("q_sixteenth_triplet", ("q_sixteenth_triplet", "q_sixtenth_triplet")),
    ("q_thirtysecond", ("q_thirtysecond", "q_thirtytwoth")),
)
LAUNCH_QUANTIZATIONS = tuple(name for name, _candidates in LAUNCH_QUANTIZATION_CANDIDATES)
_LAUNCH_QUANTIZATION_MAP = dict(LAUNCH_QUANTIZATION_CANDIDATES)
# Accept the historical spellings as input too, so a client that read the enum back
# from Live can send the same name.
_LAUNCH_QUANTIZATION_ALIASES = {}
for _name, _candidates in LAUNCH_QUANTIZATION_CANDIDATES:
    for _candidate in _candidates:
        _LAUNCH_QUANTIZATION_ALIASES[_candidate] = _name


def _session_slot(song, params):
    """(TrackRef, slot_index, slot) for a track + slot address."""
    ref = lom.track_from_params(song, params)
    if ref.track_type != "track":
        raise errors.invalid_state("no_clip_slots", "%s has no clip slots" % lom.track_label(
            ref.track, ref.index, ref.track_type), track_type=ref.track_type)
    slot_index = lom.get_int(params, "slot", minimum=0)
    slot = lom.resolve_slot(ref.track, slot_index)
    return ref, slot_index, slot


def create(ctx, params):
    song = ctx.song()
    ref, slot_index, slot = _session_slot(song, params)
    length = lom.get_float(params, "length", exclusive_minimum=0.0)
    name = lom.get_str(params, "name", None)
    label = lom.track_label(ref.track, ref.index, ref.track_type)
    if not lom.safe_get(ref.track, "has_midi_input", False):
        raise errors.invalid_state("track_not_midi", "%s is not a MIDI track; clips can only be created on MIDI tracks"
                                   % label, track=ref.index)
    if lom.safe_get(slot, "has_clip", False):
        raise errors.invalid_state("slot_occupied", "Slot %d on %s already has a clip ('%s')" % (
            slot_index, label, lom.safe_get(slot.clip, "name", "")), track=ref.index, slot=slot_index)
    lom.live_call(slot.create_clip, length)
    clip = lom.safe_get(slot, "clip")
    if clip is None:
        raise errors.LiveRpcError(errors.LIVE_ERROR, "Live did not create a clip in slot %d" % slot_index,
                                  {"exception": "RuntimeError", "detail": "slot.clip is None after create_clip"})
    if name is not None:
        lom.live_set(clip, "name", name)
    return lom.clip_summary(clip, ref.index, slot_index, None)


def get(ctx, params):
    ref = lom.resolve_clip(ctx.song(), params)
    return lom.clip_summary_for(ref)


def _launch_quantization(value):
    """Resolve a public launch-quantization name to the enum member Live exposes."""
    enum_cls = getattr(Live.Clip, "ClipLaunchQuantization", None)
    if enum_cls is None:
        raise errors.unsupported("Live.Clip.ClipLaunchQuantization", "this Live build")
    key = value.strip().lower().replace(" ", "_").replace("-", "_")
    if not key.startswith("q_"):
        key = "q_" + key
    public = _LAUNCH_QUANTIZATION_ALIASES.get(key)
    if public is None:
        raise errors.invalid_params("launch_quantization must be one of %s (got %r)" % (
            ", ".join(LAUNCH_QUANTIZATIONS), value), parameter="launch_quantization",
            available=list(LAUNCH_QUANTIZATIONS))
    for candidate in _LAUNCH_QUANTIZATION_MAP[public]:
        member = getattr(enum_cls, candidate, None)
        if member is not None:
            return member
    raise errors.unsupported(
        "Live.Clip.ClipLaunchQuantization.%s" % public, "this Live build",
        "This Live build has no launch quantization named %s (tried %s)" % (
            public, ", ".join(_LAUNCH_QUANTIZATION_MAP[public])))


def _apply_pair(clip, end_attr, end_value, start_attr, start_value):
    """Apply an (end, start) pair in the documented order (end first, then start).

    Live rejects start >= end at every step, so when both are given and the new
    end would not clear the *current* start (e.g. moving a loop earlier), the start
    is written first instead. Either order ends in the same requested state.
    """
    if end_value is not None and start_value is not None:
        current_start = lom.safe_get(clip, start_attr)
        if current_start is not None and end_value <= float(current_start):
            lom.live_set(clip, start_attr, start_value)
            lom.live_set(clip, end_attr, end_value)
            return
    if end_value is not None:
        lom.live_set(clip, end_attr, end_value)
    if start_value is not None:
        lom.live_set(clip, start_attr, start_value)


def set_clip(ctx, params):
    song = ctx.song()
    ref = lom.resolve_clip(song, params)
    clip = ref.clip
    name = lom.get_str(params, "name", None)
    color_index = lom.get_color_index(params)
    loop_start = lom.get_float(params, "loop_start", None, minimum=0.0)
    loop_end = lom.get_float(params, "loop_end", None, exclusive_minimum=0.0)
    looping = lom.get_bool(params, "looping", None)
    start_marker = lom.get_float(params, "start_marker", None, minimum=0.0)
    end_marker = lom.get_float(params, "end_marker", None, exclusive_minimum=0.0)
    launch_quantization = lom.get_str(params, "launch_quantization", None)
    if loop_start is not None and loop_end is not None and loop_start >= loop_end:
        raise errors.invalid_params("loop_start (%s) must be less than loop_end (%s)" % (loop_start, loop_end),
                                    parameter="loop_start")
    if start_marker is not None and end_marker is not None and start_marker >= end_marker:
        raise errors.invalid_params("start_marker (%s) must be less than end_marker (%s)" % (start_marker, end_marker),
                                    parameter="start_marker")
    # On an unlooped clip the LOM defines loop_start/loop_end as "clip start/end", i.e.
    # they alias start_marker/end_marker: writing both pairs would silently let the
    # marker writes overwrite the loop writes. Reject that up front (PROTOCOL.md, clip.set).
    has_loop_pair = loop_start is not None or loop_end is not None
    has_marker_pair = start_marker is not None or end_marker is not None
    if has_loop_pair and has_marker_pair:
        effective_looping = looping if looping is not None else bool(lom.safe_get(clip, "looping", False))
        if not effective_looping:
            raise errors.invalid_params(
                "On an unlooped clip Live aliases loop_start/loop_end to start_marker/end_marker, so set either "
                "the loop_* pair or the *_marker pair, not both (looping is false for this clip)",
                parameter="loop_start", reason="loop_marker_alias")
    quant_value = _launch_quantization(launch_quantization) if launch_quantization is not None else None

    if name is not None:
        lom.live_set(clip, "name", name)
    if color_index is not lom.MISSING:
        lom.live_set(clip, "color_index", color_index)
    if quant_value is not None:
        lom.live_set(clip, "launch_quantization", quant_value)
    if looping is not None:
        lom.live_set(clip, "looping", looping)
    _apply_pair(clip, "loop_end", loop_end, "loop_start", loop_start)
    _apply_pair(clip, "end_marker", end_marker, "start_marker", start_marker)
    return lom.clip_summary_for(ref)


def fire(ctx, params):
    song = ctx.song()
    ref, slot_index, slot = _session_slot(song, params)
    lom.live_call(slot.fire)
    if lom.safe_get(slot, "has_clip", False):
        return lom.clip_summary(slot.clip, ref.index, slot_index, None)
    return {"fired_empty_slot": True, "track": ref.index, "slot": slot_index}


def stop(ctx, params):
    song = ctx.song()
    if params.get("slot") is None:
        ref = lom.track_from_params(song, params)
        lom.live_call(ref.track.stop_all_clips)
        return {"ok": True}
    _ref, _slot_index, slot = _session_slot(song, params)
    lom.live_call(slot.stop)
    return {"ok": True}


def duplicate(ctx, params):
    song = ctx.song()
    ref, slot_index, slot = _session_slot(song, params)
    if not lom.safe_get(slot, "has_clip", False):
        raise errors.invalid_state("slot_empty", "Slot %d on %s is empty" % (
            slot_index, lom.track_label(ref.track, ref.index, ref.track_type)), track=ref.index, slot=slot_index)
    target_track_index = lom.get_int(params, "target_track", ref.index, minimum=0)
    target_slot_index = lom.get_int(params, "target_slot", minimum=0)
    target_track = lom.resolve_track(song, target_track_index, "track")
    target_slot = lom.resolve_slot(target_track, target_slot_index)
    target_label = lom.track_label(target_track, target_track_index, "track")
    if lom.safe_get(target_slot, "has_clip", False):
        raise errors.invalid_state("slot_occupied", "Target slot %d on %s already has a clip ('%s')" % (
            target_slot_index, target_label, lom.safe_get(target_slot.clip, "name", "")),
            track=target_track_index, slot=target_slot_index)
    source_is_midi = bool(lom.safe_get(slot.clip, "is_midi_clip", False))
    target_is_midi = bool(lom.safe_get(target_track, "has_midi_input", False))
    if source_is_midi != target_is_midi:
        raise errors.invalid_state("track_type_mismatch", "Cannot copy a %s clip onto %s (%s track)" % (
            "MIDI" if source_is_midi else "audio", target_label, "MIDI" if target_is_midi else "audio"))
    lom.live_call(slot.duplicate_clip_to, target_slot)
    clip = lom.safe_get(target_slot, "clip")
    if clip is None:
        raise errors.LiveRpcError(errors.LIVE_ERROR, "Live did not place a clip in the target slot",
                                  {"exception": "RuntimeError", "detail": "target slot empty after duplicate_clip_to"})
    return lom.clip_summary(clip, target_track_index, target_slot_index, None)


def duplicate_loop(ctx, params):
    song = ctx.song()
    ref = lom.resolve_clip(song, params, allow_arrangement=False)
    lom.live_call(ref.clip.duplicate_loop)
    return lom.clip_summary_for(ref)


def delete(ctx, params):
    song = ctx.song()
    ref = lom.resolve_clip(song, params)
    name = lom.safe_get(ref.clip, "name", "")
    if ref.slot_index is not None:
        target = "clip '%s' (track %s, slot %d)" % (name, ref.track_index, ref.slot_index)
    else:
        target = "arrangement clip '%s' (track %s, arrangement_index %d)" % (name, ref.track_index, ref.arrangement_index)
    lom.require_confirm(params, "clip.delete", target)
    if ref.slot is not None:
        lom.live_call(ref.slot.delete_clip)
    else:
        delete_clip = lom.safe_get(ref.track, "delete_clip")
        if delete_clip is None:
            raise errors.unsupported("Track.delete_clip (Live 11+)", ctx.version["string"])
        lom.live_call(delete_clip, ref.clip)
    return {"deleted": name}


METHODS = {
    "clip.create": create,
    "clip.get": get,
    "clip.set": set_clip,
    "clip.fire": fire,
    "clip.stop": stop,
    "clip.duplicate": duplicate,
    "clip.duplicate_loop": duplicate_loop,
    "clip.delete": delete,
}
