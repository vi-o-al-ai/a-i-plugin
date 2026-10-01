"""track.* handlers."""
from .. import errors, lom


def _track_payload(song, ref, include_clips, include_devices, include_params):
    summary = lom.track_summary(song, ref.track, ref.index, ref.track_type)
    if include_clips:
        clips = []
        for si, slot in enumerate(lom.as_list(lom.safe_get(ref.track, "clip_slots"))):
            if lom.safe_get(slot, "has_clip", False):
                clips.append(lom.clip_summary(slot.clip, ref.index, si, None))
        summary["clips"] = clips
    if include_devices:
        summary["devices"] = lom.device_entries(ref.track, include_params, depth=1)
    return summary


def get(ctx, params):
    song = ctx.song()
    ref = lom.track_from_params(song, params)
    return _track_payload(song, ref,
                          lom.get_bool(params, "include_clips", True),
                          lom.get_bool(params, "include_devices", True),
                          lom.get_bool(params, "include_params", False))


def _set_mixer(param, value, key):
    if param is None:
        raise errors.invalid_state("no_mixer", "This track has no %s control" % key)
    low = lom.safe_get(param, "min", None)
    high = lom.safe_get(param, "max", None)
    value, _clamped = lom.clamp(value, low, high)
    lom.live_set(param, "value", value)


def set_track(ctx, params):
    song = ctx.song()
    ref = lom.track_from_params(song, params)
    track = ref.track
    label = lom.track_label(track, ref.index, ref.track_type)

    name = lom.get_str(params, "name", None)
    color_index = lom.get_color_index(params)
    mute = lom.get_bool(params, "mute", None)
    solo = lom.get_bool(params, "solo", None)
    arm = lom.get_bool(params, "arm", None)
    volume = lom.get_float(params, "volume", None, minimum=0.0, maximum=1.0)
    pan = lom.get_float(params, "pan", None, minimum=-1.0, maximum=1.0)
    sends = lom.get_list(params, "sends", None)
    fold = lom.get_bool(params, "fold", None)

    # Validate everything before touching the set.
    if arm is not None and not lom.safe_get(track, "can_be_armed", False):
        raise errors.invalid_state("cannot_arm", "%s cannot be armed" % label, track=ref.index,
                                   track_type=ref.track_type)
    if fold is not None and not lom.safe_get(track, "is_foldable", False):
        raise errors.invalid_state("not_a_group", "%s is not a group track, so it cannot be folded" % label,
                                   track=ref.index)
    mixer = lom.safe_get(track, "mixer_device")
    send_params = lom.as_list(lom.safe_get(mixer, "sends")) if mixer is not None else []
    send_updates = []
    if sends is not None:
        for i, item in enumerate(sends):
            if not isinstance(item, dict):
                raise errors.invalid_params("sends[%d] must be an object {\"index\", \"value\"}" % i, parameter="sends")
            send_index = lom.get_int(item, "index", minimum=0)
            send_value = lom.get_float(item, "value", minimum=0.0, maximum=1.0)
            if send_index >= len(send_params):
                raise errors.not_found("send", send_index, len(send_params))
            send_updates.append((send_params[send_index], send_value))

    if name is not None:
        lom.live_set(track, "name", name)
    if color_index is not lom.MISSING:
        lom.live_set(track, "color_index", color_index)
    if mute is not None:
        lom.live_set(track, "mute", mute)
    if solo is not None:
        lom.live_set(track, "solo", solo)
    if arm is not None:
        lom.live_set(track, "arm", arm)
    if volume is not None:
        _set_mixer(lom.safe_get(mixer, "volume") if mixer is not None else None, volume, "volume")
    if pan is not None:
        _set_mixer(lom.safe_get(mixer, "panning") if mixer is not None else None, pan, "pan")
    for param, value in send_updates:
        _set_mixer(param, value, "send")
    if fold is not None:
        lom.live_set(track, "fold_state", 1 if fold else 0)
    return lom.track_summary(song, track, ref.index, ref.track_type)


def stop_clips(ctx, params):
    song = ctx.song()
    ref = lom.track_from_params(song, params)
    lom.live_call(ref.track.stop_all_clips)
    return {"ok": True}


METHODS = {
    "track.get": get,
    "track.set": set_track,
    "track.stop_clips": stop_clips,
}
