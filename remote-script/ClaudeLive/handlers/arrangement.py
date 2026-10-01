"""arrangement.* handlers."""
from .. import errors, lom

CUE_EPSILON = 1.0e-3
PLAYING_MESSAGE = "Stop playback first: creating or deleting a locator moves the playhead."


def _arrangement_clips(track, track_index, include_note_counts=False):
    return [lom.clip_summary(clip, track_index, None, i, include_note_count=include_note_counts)
            for i, clip in enumerate(lom.as_list(lom.safe_get(track, "arrangement_clips")))]


def _locators(song):
    return [lom.cue_point(cue, i) for i, cue in enumerate(lom.as_list(lom.safe_get(song, "cue_points")))]


def get_overview(ctx, params):
    song = ctx.song()
    include_clips = lom.get_bool(params, "include_clips", True)
    include_note_counts = lom.get_bool(params, "include_note_counts", False)
    tracks = []
    for i, track in enumerate(lom.as_list(song.tracks)):
        entry = {"index": i, "name": lom.safe_get(track, "name", "")}
        if include_clips:
            entry["clips"] = _arrangement_clips(track, i, include_note_counts)
        else:
            entry["clip_count"] = len(lom.as_list(lom.safe_get(track, "arrangement_clips")))
        tracks.append(entry)
    return {
        "song_length": lom._num(lom.safe_get(song, "song_length")),
        "loop": {"enabled": bool(lom.safe_get(song, "loop", False)),
                 "start": lom._num(lom.safe_get(song, "loop_start")),
                 "length": lom._num(lom.safe_get(song, "loop_length"))},
        "locators": _locators(song),
        "tracks": tracks,
    }


def get_clips(ctx, params):
    song = ctx.song()
    ref = lom.track_from_params(song, params)
    include_note_counts = lom.get_bool(params, "include_note_counts", False)
    return {"clips": _arrangement_clips(ref.track, ref.index, include_note_counts)}


def add_clip_from_slot(ctx, params):
    song = ctx.song()
    ref = lom.track_from_params(song, params)
    if ref.track_type != "track":
        raise errors.invalid_state("no_clip_slots", "%s has no clip slots" % lom.track_label(
            ref.track, ref.index, ref.track_type))
    slot_index = lom.get_int(params, "slot", minimum=0)
    slot = lom.resolve_slot(ref.track, slot_index)
    time_value = lom.get_float(params, "time", minimum=0.0)
    delete_source = lom.get_bool(params, "delete_source", False)
    if not lom.safe_get(slot, "has_clip", False):
        raise errors.invalid_state("slot_empty", "Slot %d on %s is empty" % (
            slot_index, lom.track_label(ref.track, ref.index, ref.track_type)), track=ref.index, slot=slot_index)
    clip = slot.clip
    if delete_source:
        # Deleting the session clip afterwards is destructive (PROTOCOL.md section 7).
        lom.require_confirm(params, "arrangement.add_clip_from_slot",
                            "the source clip '%s' (track %s, slot %d), deleted after copying it to the arrangement" % (
                                lom.safe_get(clip, "name", ""), ref.index, slot_index))
    duplicate = lom.safe_get(ref.track, "duplicate_clip_to_arrangement")
    if duplicate is None:
        raise errors.unsupported("Track.duplicate_clip_to_arrangement (Live 11+)", ctx.version["string"])
    before = lom.as_list(lom.safe_get(ref.track, "arrangement_clips"))
    new_clip = lom.live_call(duplicate, clip, time_value)
    after = lom.as_list(lom.safe_get(ref.track, "arrangement_clips"))
    if new_clip is None:
        for candidate in after:
            if lom.index_of(before, candidate) is None:
                new_clip = candidate
                break
    if new_clip is None:
        for candidate in after:
            start = lom.safe_get(candidate, "start_time")
            if start is not None and abs(float(start) - time_value) < CUE_EPSILON:
                new_clip = candidate
    if new_clip is None:
        raise errors.LiveRpcError(errors.LIVE_ERROR, "Live did not report the new arrangement clip",
                                  {"exception": "RuntimeError", "detail": "no new clip in track.arrangement_clips"})
    arrangement_index = lom.index_of(after, new_clip)
    if delete_source:
        lom.live_call(slot.delete_clip)
    return lom.clip_summary(new_clip, ref.index, None, arrangement_index)


def _cue_at(song, time_value):
    for i, cue in enumerate(lom.as_list(lom.safe_get(song, "cue_points"))):
        cue_time = lom.safe_get(cue, "time")
        if cue_time is not None and abs(float(cue_time) - time_value) < CUE_EPSILON:
            return cue, i
    return None, None


def _require_stopped(song):
    """Live only offers "toggle a cue at the playhead", so the script has to move the
    playhead. While playing that relocates playback (and the toggle may land at a
    quantised time), so refuse (PROTOCOL.md section 7)."""
    if bool(lom.safe_get(song, "is_playing", False)):
        raise errors.invalid_state("transport_running", PLAYING_MESSAGE)


def set_locator(ctx, params):
    song = ctx.song()
    time_value = lom.get_float(params, "time", minimum=0.0)
    name = lom.get_str(params, "name", None)
    cue, index = _cue_at(song, time_value)
    if cue is None:
        _require_stopped(song)
        previous = lom.safe_get(song, "current_song_time", 0.0)
        lom.live_set(song, "current_song_time", time_value)
        try:
            lom.live_call(song.set_or_delete_cue)
        finally:
            try:
                song.current_song_time = previous
            except Exception:
                pass
        cue, index = _cue_at(song, time_value)
        if cue is None:
            raise errors.LiveRpcError(errors.LIVE_ERROR, "Live did not create a locator at %s" % time_value,
                                      {"exception": "RuntimeError", "detail": "set_or_delete_cue added no cue point"})
    if name is not None:
        lom.live_set(cue, "name", name)
    return lom.cue_point(cue, index)


def delete_locator(ctx, params):
    song = ctx.song()
    index = lom.get_int(params, "index", minimum=0)
    cues = lom.as_list(lom.safe_get(song, "cue_points"))
    if index >= len(cues):
        raise errors.not_found("cue_point", index, len(cues))
    cue = cues[index]
    name = lom.safe_get(cue, "name", "")
    cue_time = float(lom.safe_get(cue, "time", 0.0))
    count_before = len(cues)
    _require_stopped(song)
    previous = lom.safe_get(song, "current_song_time", 0.0)
    try:
        # Selecting the cue (playhead on its time) makes set_or_delete_cue delete it.
        lom.live_set(song, "current_song_time", cue_time)
        lom.live_call(song.set_or_delete_cue)
        if len(lom.as_list(lom.safe_get(song, "cue_points"))) >= count_before:
            jump = lom.safe_get(cue, "jump")
            if jump is not None:
                lom.live_call(jump)
                lom.live_call(song.set_or_delete_cue)
    finally:
        try:
            song.current_song_time = previous
        except Exception:
            pass
    if len(lom.as_list(lom.safe_get(song, "cue_points"))) >= count_before:
        raise errors.LiveRpcError(errors.LIVE_ERROR, "Live did not delete locator '%s' at %s" % (name, cue_time),
                                  {"exception": "RuntimeError", "detail": "set_or_delete_cue removed no cue point"})
    return {"deleted": name, "time": cue_time}


METHODS = {
    "arrangement.get_overview": get_overview,
    "arrangement.get_clips": get_clips,
    "arrangement.add_clip_from_slot": add_clip_from_slot,
    "arrangement.set_locator": set_locator,
    "arrangement.delete_locator": delete_locator,
}
