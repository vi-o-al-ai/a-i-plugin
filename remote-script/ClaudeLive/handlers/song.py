"""song.* handlers: overview, transport, scale, undo, track and scene management."""
from .. import errors, lom

SCALE_NAMES = (
    "Major", "Minor", "Dorian", "Mixolydian", "Lydian", "Phrygian", "Locrian", "Whole Tone",
    "Half-whole Dim.", "Whole-half Dim.", "Minor Blues", "Minor Pentatonic", "Major Pentatonic",
    "Harmonic Minor", "Harmonic Major", "Dorian #4", "Phrygian Dominant", "Melodic Minor",
    "Lydian Augmented", "Lydian Dominant", "Super Locrian", "Bhairav", "Hungarian Minor",
    "8-Tone Spanish", "Hirajoshi", "In-Sen", "Iwato", "Kumoi", "Pelog Selisir", "Pelog Tembung",
    "Messaien 3", "Messaien 4", "Messaien 5", "Messaien 6", "Messaien 7",
)

TEMPO_MIN = 20.0
TEMPO_MAX = 999.0
SIGNATURE_DENOMINATORS = (1, 2, 4, 8, 16)


def _track_with_children(ctx, song, track, index, track_type, include_clips, include_devices, include_params,
                         include_note_counts=False):
    summary = lom.track_summary(song, track, index, track_type)
    if include_clips:
        clips = []
        for si, slot in enumerate(lom.as_list(lom.safe_get(track, "clip_slots"))):
            if lom.safe_get(slot, "has_clip", False):
                clips.append(lom.clip_summary(slot.clip, index, si, None, include_note_count=include_note_counts))
        summary["clips"] = clips
    if include_devices:
        summary["devices"] = lom.device_entries(track, include_params, depth=1)
    return summary


def get_overview(ctx, params):
    song = ctx.song()
    include_clips = lom.get_bool(params, "include_clips", True)
    include_devices = lom.get_bool(params, "include_devices", True)
    include_params = lom.get_bool(params, "include_params", False)
    include_returns = lom.get_bool(params, "include_returns", True)
    include_note_counts = lom.get_bool(params, "include_note_counts", False)

    tracks = [_track_with_children(ctx, song, t, i, "track", include_clips, include_devices, include_params,
                                   include_note_counts)
              for i, t in enumerate(lom.as_list(song.tracks))]
    returns = []
    if include_returns:
        returns = [_track_with_children(ctx, song, t, i, "return", False, include_devices, include_params)
                   for i, t in enumerate(lom.as_list(song.return_tracks))]
    master = _track_with_children(ctx, song, song.master_track, 0, "master", False, include_devices, include_params)
    scenes = [lom.scene_summary(song, s, i) for i, s in enumerate(lom.as_list(song.scenes))]
    return {
        "transport": lom.transport(song),
        "scale": lom.scale(song),
        "tracks": tracks,
        "return_tracks": returns,
        "master": master,
        "scenes": scenes,
        "selection": lom.selection(song),
        "live_version": ctx.version["string"],
    }


def get_transport(ctx, params):
    return lom.transport(ctx.song())


def set_transport(ctx, params):
    song = ctx.song()
    tempo = lom.get_float(params, "tempo", None, minimum=TEMPO_MIN, maximum=TEMPO_MAX)
    metronome = lom.get_bool(params, "metronome", None)
    loop_enabled = lom.get_bool(params, "loop_enabled", None)
    loop_start = lom.get_float(params, "loop_start", None, minimum=0.0)
    loop_length = lom.get_float(params, "loop_length", None, exclusive_minimum=0.0)
    record_mode = lom.get_bool(params, "record_mode", None)
    session_record = lom.get_bool(params, "session_record", None)
    position = lom.get_float(params, "position", None, minimum=0.0)
    numerator = lom.get_int(params, "signature_numerator", None, minimum=1, maximum=99)
    denominator = lom.get_int(params, "signature_denominator", None)
    if denominator is not None and denominator not in SIGNATURE_DENOMINATORS:
        raise errors.invalid_params("signature_denominator must be one of %s" % (SIGNATURE_DENOMINATORS,),
                                    parameter="signature_denominator", available=list(SIGNATURE_DENOMINATORS))

    if tempo is not None:
        lom.live_set(song, "tempo", tempo)
    if numerator is not None:
        lom.live_set(song, "signature_numerator", numerator)
    if denominator is not None:
        lom.live_set(song, "signature_denominator", denominator)
    if metronome is not None:
        lom.live_set(song, "metronome", metronome)
    if loop_start is not None:
        lom.live_set(song, "loop_start", loop_start)
    if loop_length is not None:
        lom.live_set(song, "loop_length", loop_length)
    if loop_enabled is not None:
        lom.live_set(song, "loop", loop_enabled)
    if record_mode is not None:
        lom.live_set(song, "record_mode", record_mode)
    if session_record is not None:
        lom.live_set(song, "session_record", session_record)
    if position is not None:
        lom.live_set(song, "current_song_time", position)
    return lom.transport(song)


def play(ctx, params):
    song = ctx.song()
    if lom.get_bool(params, "from_start", False):
        lom.live_set(song, "current_song_time", 0.0)
    lom.live_call(song.start_playing)
    return lom.transport(song)


def stop(ctx, params):
    song = ctx.song()
    lom.live_call(song.stop_playing)
    return lom.transport(song)


def continue_playing(ctx, params):
    song = ctx.song()
    lom.live_call(song.continue_playing)
    return lom.transport(song)


def stop_all_clips(ctx, params):
    song = ctx.song()
    lom.live_call(song.stop_all_clips)
    return {"ok": True}


def _require_scale(ctx, song):
    if not lom.scale_supported(song):
        raise errors.unsupported("Live 12 (song.scale_name / song.root_note)", ctx.version["string"],
                                 "Scale awareness needs Live 12; the running Live (%s) does not expose song.scale_name"
                                 % ctx.version["string"])


def get_scale(ctx, params):
    song = ctx.song()
    _require_scale(ctx, song)
    return lom.scale(song)


def _parse_root_note(value):
    if isinstance(value, bool):
        raise errors.invalid_params("root_note must be 0-11 or a note name like \"C\" or \"F#\"", parameter="root_note")
    if isinstance(value, (int, float)):
        if isinstance(value, float) and not value.is_integer():
            raise errors.invalid_params("root_note must be an integer 0-11", parameter="root_note")
        value = int(value)
        if value < 0 or value > 11:
            raise errors.invalid_params("root_note must be 0-11 (got %d)" % value, parameter="root_note")
        return value
    if isinstance(value, str):
        key = value.strip().upper().replace("♯", "#").replace("♭", "B")
        if key in lom.NOTE_NAME_ALIASES:
            return lom.NOTE_NAME_ALIASES[key]
        raise errors.invalid_params("Unknown note name %r (use C, C#, Db, D, ... B)" % value,
                                    parameter="root_note", available=list(lom.NOTE_NAMES))
    raise errors.invalid_params("root_note must be 0-11 or a note name", parameter="root_note")


def set_scale(ctx, params):
    song = ctx.song()
    _require_scale(ctx, song)
    root = params.get("root_note")
    scale_name = lom.get_str(params, "scale_name", None)
    if root is None and scale_name is None:
        raise errors.invalid_params("Give root_note and/or scale_name", parameter="scale_name")
    if scale_name is not None:
        wanted = scale_name.strip().lower()
        canonical = None
        for name in SCALE_NAMES:
            if name.lower() == wanted:
                canonical = name
                break
        if canonical is None:
            raise errors.invalid_params("Unknown scale name %r" % scale_name, parameter="scale_name",
                                        available=list(SCALE_NAMES))
        lom.live_set(song, "scale_name", canonical)
    if root is not None:
        lom.live_set(song, "root_note", _parse_root_note(root))
    return lom.scale(song)


def undo(ctx, params):
    lom.live_call(ctx.song().undo)
    return {"ok": True}


def redo(ctx, params):
    lom.live_call(ctx.song().redo)
    return {"ok": True}


def _new_track_summary(song, created, requested_index, name, track_type="track"):
    vector = lom.as_list(song.return_tracks if track_type == "return" else song.tracks)
    track = created
    if track is None or lom.index_of(vector, track) is None:
        if track_type == "return" or requested_index is None or requested_index < 0 or requested_index >= len(vector):
            track = vector[-1]
        else:
            track = vector[requested_index]
    index = lom.index_of(vector, track)
    if name is not None:
        lom.live_set(track, "name", name)
    return lom.track_summary(song, track, index, track_type)


def create_midi_track(ctx, params):
    song = ctx.song()
    index = lom.get_int(params, "index", -1, minimum=-1)
    name = lom.get_str(params, "name", None)
    count = len(lom.as_list(song.tracks))
    if index > count:
        raise errors.invalid_params("index must be between -1 and %d (got %d)" % (count, index), parameter="index")
    created = lom.live_call(song.create_midi_track, index)
    return _new_track_summary(song, created, index, name)


def create_audio_track(ctx, params):
    song = ctx.song()
    index = lom.get_int(params, "index", -1, minimum=-1)
    name = lom.get_str(params, "name", None)
    count = len(lom.as_list(song.tracks))
    if index > count:
        raise errors.invalid_params("index must be between -1 and %d (got %d)" % (count, index), parameter="index")
    created = lom.live_call(song.create_audio_track, index)
    return _new_track_summary(song, created, index, name)


def create_return_track(ctx, params):
    song = ctx.song()
    name = lom.get_str(params, "name", None)
    created = lom.live_call(song.create_return_track)
    return _new_track_summary(song, created, -1, name, "return")


def delete_track(ctx, params):
    song = ctx.song()
    ref = lom.track_from_params(song, params)
    label = lom.track_label(ref.track, ref.index, ref.track_type)
    if ref.track_type == "master":
        raise errors.invalid_state("master_track", "The master track cannot be deleted")
    lom.require_confirm(params, "song.delete_track", label)
    name = lom.safe_get(ref.track, "name", "")
    if ref.track_type == "return":
        lom.live_call(song.delete_return_track, ref.index)
        return {"deleted": name, "track_count": len(lom.as_list(song.return_tracks)), "track_type": "return"}
    lom.live_call(song.delete_track, ref.index)
    return {"deleted": name, "track_count": len(lom.as_list(song.tracks)), "track_type": "track"}


def create_scene(ctx, params):
    song = ctx.song()
    index = lom.get_int(params, "index", -1, minimum=-1)
    name = lom.get_str(params, "name", None)
    count = len(lom.as_list(song.scenes))
    if index > count:
        raise errors.invalid_params("index must be between -1 and %d (got %d)" % (count, index), parameter="index")
    created = lom.live_call(song.create_scene, index)
    scenes = lom.as_list(song.scenes)
    scene = created
    if scene is None or lom.index_of(scenes, scene) is None:
        scene = scenes[-1] if index < 0 or index >= len(scenes) else scenes[index]
    new_index = lom.index_of(scenes, scene)
    if name is not None:
        lom.live_set(scene, "name", name)
    return lom.scene_summary(song, scene, new_index)


def duplicate_scene(ctx, params):
    song = ctx.song()
    index = lom.get_int(params, "scene")
    lom.resolve_scene(song, index)
    before = len(lom.as_list(song.scenes))
    lom.live_call(song.duplicate_scene, index)
    scenes = lom.as_list(song.scenes)
    # Live selects the duplicate; fall back to index + 1.
    selected = lom.safe_get(song.view, "selected_scene")
    new_index = lom.index_of(scenes, selected) if selected is not None else None
    if new_index is None or len(scenes) == before:
        new_index = min(index + 1, len(scenes) - 1)
    return lom.scene_summary(song, scenes[new_index], new_index)


def delete_scene(ctx, params):
    song = ctx.song()
    index = lom.get_int(params, "scene")
    scene = lom.resolve_scene(song, index)
    name = lom.safe_get(scene, "name", "")
    lom.require_confirm(params, "song.delete_scene", "%s (scene %d)" % (name, index))
    if len(lom.as_list(song.scenes)) <= 1:
        raise errors.invalid_state("last_scene", "The last remaining scene cannot be deleted")
    lom.live_call(song.delete_scene, index)
    return {"deleted": name, "scene_count": len(lom.as_list(song.scenes))}


METHODS = {
    "song.get_overview": get_overview,
    "song.get_transport": get_transport,
    "song.set_transport": set_transport,
    "song.play": play,
    "song.stop": stop,
    "song.continue": continue_playing,
    "song.stop_all_clips": stop_all_clips,
    "song.get_scale": get_scale,
    "song.set_scale": set_scale,
    "song.undo": undo,
    "song.redo": redo,
    "song.create_midi_track": create_midi_track,
    "song.create_audio_track": create_audio_track,
    "song.create_return_track": create_return_track,
    "song.delete_track": delete_track,
    "song.create_scene": create_scene,
    "song.duplicate_scene": duplicate_scene,
    "song.delete_scene": delete_scene,
}
