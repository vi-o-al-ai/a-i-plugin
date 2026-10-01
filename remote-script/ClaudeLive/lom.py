"""Live Object Model helpers: parameter validation, addressing (PROTOCOL.md section 5)
and result fragments (section 6). Everything here runs on Live's main thread.
"""
import collections
import math

import Live

from . import errors
from .errors import LiveRpcError

MISSING = object()

TRACK_TYPES = ("track", "return", "master")
NOTE_NAMES = ("C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B")
NOTE_NAME_ALIASES = {
    "C": 0, "C#": 1, "DB": 1, "D": 2, "D#": 3, "EB": 3, "E": 4, "FB": 4, "E#": 5, "F": 5, "F#": 6, "GB": 6,
    "G": 7, "G#": 8, "AB": 8, "A": 9, "A#": 10, "BB": 10, "B": 11, "CB": 11, "B#": 0,
}

# "All notes" window for get_notes_extended / remove_notes_extended.
NOTE_ALL_FROM_PITCH = 0
NOTE_ALL_PITCH_SPAN = 128
NOTE_ALL_FROM_TIME = -8192.0
NOTE_ALL_TIME_SPAN = 1.0e6

MAX_COLOR_INDEX = 69


# --------------------------------------------------------------------------
# Parameter helpers
# --------------------------------------------------------------------------

def is_number(value):
    if isinstance(value, bool):
        return False
    if isinstance(value, int):
        return True
    if isinstance(value, float):
        return not (math.isnan(value) or math.isinf(value))
    return False


def _missing(key):
    return errors.invalid_params("Missing required parameter '%s'" % key, parameter=key)


def get_int(params, key, default=MISSING, minimum=None, maximum=None):
    value = params.get(key, MISSING)
    if value is MISSING or value is None:
        if default is MISSING:
            raise _missing(key)
        return default
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise errors.invalid_params("Parameter '%s' must be an integer (got %s)" % (key, type(value).__name__),
                                    parameter=key)
    if isinstance(value, float):
        if not value.is_integer():
            raise errors.invalid_params("Parameter '%s' must be an integer (got %r)" % (key, value), parameter=key)
        value = int(value)
    if minimum is not None and value < minimum:
        raise errors.invalid_params("Parameter '%s' must be >= %s (got %s)" % (key, minimum, value),
                                    parameter=key, minimum=minimum)
    if maximum is not None and value > maximum:
        raise errors.invalid_params("Parameter '%s' must be <= %s (got %s)" % (key, maximum, value),
                                    parameter=key, maximum=maximum)
    return value


def get_float(params, key, default=MISSING, minimum=None, maximum=None, exclusive_minimum=None):
    value = params.get(key, MISSING)
    if value is MISSING or value is None:
        if default is MISSING:
            raise _missing(key)
        return default
    if not is_number(value):
        raise errors.invalid_params("Parameter '%s' must be a finite number (got %r)" % (key, value), parameter=key)
    value = float(value)
    if minimum is not None and value < minimum:
        raise errors.invalid_params("Parameter '%s' must be >= %s (got %s)" % (key, minimum, value),
                                    parameter=key, minimum=minimum)
    if exclusive_minimum is not None and value <= exclusive_minimum:
        raise errors.invalid_params("Parameter '%s' must be > %s (got %s)" % (key, exclusive_minimum, value),
                                    parameter=key)
    if maximum is not None and value > maximum:
        raise errors.invalid_params("Parameter '%s' must be <= %s (got %s)" % (key, maximum, value),
                                    parameter=key, maximum=maximum)
    return value


def get_bool(params, key, default=MISSING):
    value = params.get(key, MISSING)
    if value is MISSING or value is None:
        if default is MISSING:
            raise _missing(key)
        return default
    if not isinstance(value, bool):
        raise errors.invalid_params("Parameter '%s' must be true or false (got %r)" % (key, value), parameter=key)
    return value


def get_str(params, key, default=MISSING, allow_empty=True):
    value = params.get(key, MISSING)
    if value is MISSING or value is None:
        if default is MISSING:
            raise _missing(key)
        return default
    if not isinstance(value, str):
        raise errors.invalid_params("Parameter '%s' must be a string (got %s)" % (key, type(value).__name__),
                                    parameter=key)
    if not allow_empty and not value.strip():
        raise errors.invalid_params("Parameter '%s' must not be empty" % key, parameter=key)
    return value


def get_list(params, key, default=MISSING):
    value = params.get(key, MISSING)
    if value is MISSING or value is None:
        if default is MISSING:
            raise _missing(key)
        return default
    if not isinstance(value, list):
        raise errors.invalid_params("Parameter '%s' must be an array (got %s)" % (key, type(value).__name__),
                                    parameter=key)
    return value


def get_choice(params, key, choices, default=MISSING):
    value = get_str(params, key, default)
    if value is default and default is not MISSING:
        return value
    if value not in choices:
        raise errors.invalid_params("Parameter '%s' must be one of %s (got %r)" % (key, ", ".join(choices), value),
                                    parameter=key, available=list(choices))
    return value


def get_color_index(params, key="color_index"):
    """0-69 or None (explicit null clears the colour). MISSING if absent."""
    if key not in params:
        return MISSING
    value = params[key]
    if value is None:
        return None
    return get_int(params, key, minimum=0, maximum=MAX_COLOR_INDEX)


def require_confirm(params, method, target):
    if params.get("confirm") is not True:
        raise errors.confirm_required(method, target)


def clamp(value, low, high):
    """Return (clamped_value, was_clamped)."""
    if low is not None and high is not None and low > high:
        low, high = high, low
    if low is not None and value < low:
        return low, True
    if high is not None and value > high:
        return high, True
    return value, False


# --------------------------------------------------------------------------
# Safe LOM access
# --------------------------------------------------------------------------

def safe_get(obj, name, default=None):
    """getattr that swallows the RuntimeErrors Live raises for N/A properties."""
    try:
        return getattr(obj, name)
    except AssertionError:
        raise
    except Exception:
        return default


def has_attr(obj, name):
    """hasattr() for LOM objects: a boost property that raises RuntimeError
    ("not available on this track") counts as absent instead of propagating."""
    return safe_get(obj, name, MISSING) is not MISSING


def live_call(fn, *args, **kwargs):
    """Call a LOM function, converting its exceptions into LIVE_ERROR."""
    try:
        return fn(*args, **kwargs)
    except (LiveRpcError, AssertionError):
        raise
    except Exception as exc:
        raise errors.live_error(exc)


def live_set(obj, name, value):
    """setattr on a LOM object, converting its exceptions into LIVE_ERROR."""
    try:
        setattr(obj, name, value)
    except (LiveRpcError, AssertionError):
        raise
    except Exception as exc:
        raise errors.live_error(exc)


def as_list(vector):
    """Materialise a Live vector (or None) into a Python list."""
    if vector is None:
        return []
    try:
        return list(vector)
    except AssertionError:
        raise
    except Exception:
        return []


def index_of(sequence, obj):
    """Index of a LOM object in a vector, by identity/equality; None if absent."""
    for i, candidate in enumerate(sequence):
        if candidate is obj or candidate == obj:
            return i
    return None


def enum_name(value, enum_cls, names, default="unknown"):
    """Map a boost enum value to one of `names` by comparing with enum_cls.<name>."""
    if value is None:
        return default
    if enum_cls is not None:
        for name in names:
            member = getattr(enum_cls, name, None)
            if member is not None:
                try:
                    if member == value:
                        return name
                except Exception:
                    pass
    text = str(value)
    tail = text.rsplit(".", 1)[-1]
    if tail in names:
        return tail
    try:
        as_int = int(value)
        if 0 <= as_int < len(names):
            return names[as_int]
    except Exception:
        pass
    return default


# --------------------------------------------------------------------------
# Version
# --------------------------------------------------------------------------

def live_version(app):
    major = safe_get_call(app, "get_major_version", 0)
    minor = safe_get_call(app, "get_minor_version", 0)
    bugfix = safe_get_call(app, "get_bugfix_version", 0)
    text = safe_get_call(app, "get_version_string", None)
    if not isinstance(text, str) or not text:
        text = "%s.%s.%s" % (major, minor, bugfix)
    return {"major": _int_or(major, 0), "minor": _int_or(minor, 0), "bugfix": _int_or(bugfix, 0), "string": text}


def safe_get_call(obj, name, default=None):
    fn = safe_get(obj, name)
    if fn is None:
        return default
    try:
        return fn()
    except AssertionError:
        raise
    except Exception:
        return default


def _int_or(value, default):
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


# --------------------------------------------------------------------------
# Colours
# --------------------------------------------------------------------------

def color_hex(value):
    if value is None:
        return None
    try:
        return "#%06X" % (int(value) & 0xFFFFFF)
    except (TypeError, ValueError):
        return None


def color_fields(obj):
    return {"color_index": safe_get(obj, "color_index"), "color": color_hex(safe_get(obj, "color"))}


def value_display(param, value=None):
    """Display string via DeviceParameter.str_for_value (never raises)."""
    if param is None:
        return None
    if value is None:
        value = safe_get(param, "value")
    try:
        return str(param.str_for_value(value))
    except AssertionError:
        raise
    except Exception:
        return str(value)


def value_and_display(param):
    if param is None:
        return {"value": None, "display": None}
    value = safe_get(param, "value")
    return {"value": _num(value), "display": value_display(param, value)}


def _num(value):
    if isinstance(value, bool) or value is None:
        return value
    try:
        f = float(value)
    except (TypeError, ValueError):
        return value
    if f.is_integer() and isinstance(value, int):
        return int(value)
    return f


# --------------------------------------------------------------------------
# Tracks
# --------------------------------------------------------------------------

TrackRef = collections.namedtuple("TrackRef", "track index track_type")


def track_type_of(song, track):
    """'midi' | 'audio' | 'group' | 'return' | 'master'."""
    master = safe_get(song, "master_track")
    if master is not None and (track is master or track == master):
        return "master"
    if index_of(as_list(safe_get(song, "return_tracks")), track) is not None:
        return "return"
    if safe_get(track, "is_foldable", False):
        return "group"
    if safe_get(track, "has_midi_input", False):
        return "midi"
    return "audio"


def resolve_track(song, track, track_type="track"):
    """Return the Track for (index, track_type); NOT_FOUND / INVALID_PARAMS otherwise."""
    if track_type not in TRACK_TYPES:
        raise errors.invalid_params("track_type must be one of %s (got %r)" % (", ".join(TRACK_TYPES), track_type),
                                    parameter="track_type", available=list(TRACK_TYPES))
    if track_type == "master":
        return song.master_track
    if track is None:
        raise _missing("track")
    if isinstance(track, bool) or not isinstance(track, int):
        raise errors.invalid_params("Parameter 'track' must be an integer (got %r)" % (track,), parameter="track")
    vector = as_list(song.return_tracks if track_type == "return" else song.tracks)
    kind = "return_track" if track_type == "return" else "track"
    if track < 0 or track >= len(vector):
        raise errors.not_found(kind, track, len(vector))
    return vector[track]


def track_from_params(song, params, default_type="track"):
    """Resolve the (track, track_type) pair in params into a TrackRef."""
    track_type = get_choice(params, "track_type", TRACK_TYPES, default_type)
    index = None
    if track_type != "master":
        index = get_int(params, "track")
    track = resolve_track(song, index, track_type)
    if track_type == "master":
        index = 0
    return TrackRef(track, index, track_type)


def track_index_of(song, track):
    """(index, track_type) for any Track object, or (None, None)."""
    if track is None:
        return None, None
    idx = index_of(as_list(song.tracks), track)
    if idx is not None:
        return idx, "track"
    idx = index_of(as_list(song.return_tracks), track)
    if idx is not None:
        return idx, "return"
    master = safe_get(song, "master_track")
    if master is not None and (track is master or track == master):
        return 0, "master"
    return None, None


def track_label(track, index, track_type):
    name = safe_get(track, "name", "?")
    if track_type == "master":
        return "%s (master)" % name
    if track_type == "return":
        return "%s (return %s)" % (name, index)
    return "%s (track %s)" % (name, index)


def track_summary(song, track, index, track_type):
    kind = track_type_of(song, track)
    mixer = safe_get(track, "mixer_device")
    volume = safe_get(mixer, "volume") if mixer is not None else None
    panning = safe_get(mixer, "panning") if mixer is not None else None
    sends = as_list(safe_get(mixer, "sends")) if mixer is not None else []
    return_names = [safe_get(r, "name", "") for r in as_list(safe_get(song, "return_tracks"))]
    send_list = []
    for i, send in enumerate(sends):
        entry = {"index": i, "name": return_names[i] if i < len(return_names) else safe_get(send, "name", "")}
        entry.update(value_and_display(send))
        send_list.append(entry)

    can_be_armed = bool(safe_get(track, "can_be_armed", False))
    arm = bool(safe_get(track, "arm", False)) if can_be_armed else False
    group_track = safe_get(track, "group_track")
    group_index = index_of(as_list(song.tracks), group_track) if group_track is not None else None
    slots = as_list(safe_get(track, "clip_slots"))
    clip_count = 0
    for slot in slots:
        if safe_get(slot, "has_clip", False):
            clip_count += 1

    summary = {
        "index": index,
        "track_type": track_type,
        "name": safe_get(track, "name", ""),
        "type": kind,
        "mute": bool(safe_get(track, "mute", False)),
        "solo": bool(safe_get(track, "solo", False)),
        "arm": arm,
        "can_be_armed": can_be_armed,
        "is_foldable": bool(safe_get(track, "is_foldable", False)),
        "is_grouped": bool(safe_get(track, "is_grouped", False)),
        "group_track_index": group_index,
        "volume": value_and_display(volume),
        "pan": value_and_display(panning),
        "sends": send_list,
        "playing_slot_index": _int_or(safe_get(track, "playing_slot_index", -1), -1),
        "fired_slot_index": _int_or(safe_get(track, "fired_slot_index", -1), -1),
        "clip_count": clip_count,
        "device_count": len(as_list(safe_get(track, "devices"))),
    }
    summary.update(color_fields(track))
    return summary


# --------------------------------------------------------------------------
# Slots and clips
# --------------------------------------------------------------------------

ClipRef = collections.namedtuple("ClipRef", "clip track track_index track_type slot_index arrangement_index slot")


def resolve_slot(track, slot_index):
    if isinstance(slot_index, bool) or not isinstance(slot_index, int):
        raise errors.invalid_params("Parameter 'slot' must be an integer (got %r)" % (slot_index,), parameter="slot")
    slots = as_list(safe_get(track, "clip_slots"))
    if slot_index < 0 or slot_index >= len(slots):
        raise errors.not_found("slot", slot_index, len(slots))
    return slots[slot_index]


def resolve_scene(song, scene_index):
    if isinstance(scene_index, bool) or not isinstance(scene_index, int):
        raise errors.invalid_params("Parameter 'scene' must be an integer (got %r)" % (scene_index,),
                                    parameter="scene")
    scenes = as_list(song.scenes)
    if scene_index < 0 or scene_index >= len(scenes):
        raise errors.not_found("scene", scene_index, len(scenes))
    return scenes[scene_index]


def resolve_clip(song, params, allow_arrangement=True):
    """Resolve a clip address (track + slot | arrangement_index) into a ClipRef."""
    has_slot = params.get("slot") is not None
    has_arr = params.get("arrangement_index") is not None
    if has_slot == has_arr:
        raise errors.invalid_params("Exactly one of 'slot' or 'arrangement_index' must be given to address a clip",
                                    parameter="slot")
    ref = track_from_params(song, params)
    if has_slot:
        slot_index = get_int(params, "slot", minimum=0)
        slot = resolve_slot(ref.track, slot_index)
        if not safe_get(slot, "has_clip", False):
            raise errors.invalid_state(
                "slot_empty", "Slot %d on %s is empty" % (slot_index, track_label(ref.track, ref.index, ref.track_type)),
                track=ref.index, slot=slot_index)
        return ClipRef(slot.clip, ref.track, ref.index, ref.track_type, slot_index, None, slot)
    if not allow_arrangement:
        raise errors.invalid_params("This method only accepts session clips (use 'slot')", parameter="arrangement_index")
    arr_index = get_int(params, "arrangement_index", minimum=0)
    clips = as_list(safe_get(ref.track, "arrangement_clips"))
    if arr_index >= len(clips):
        raise errors.not_found("arrangement_clip", arr_index, len(clips))
    return ClipRef(clips[arr_index], ref.track, ref.index, ref.track_type, None, arr_index, None)


def all_notes(clip):
    return clip.get_notes_extended(NOTE_ALL_FROM_PITCH, NOTE_ALL_PITCH_SPAN, NOTE_ALL_FROM_TIME, NOTE_ALL_TIME_SPAN)


def note_count(clip):
    if not safe_get(clip, "is_midi_clip", False):
        return None
    try:
        return len(all_notes(clip))
    except AssertionError:
        raise
    except Exception:
        return None


def clip_summary(clip, track_index, slot=None, arrangement_index=None, include_note_count=True):
    """ClipSummary (PROTOCOL.md section 6). Counting notes materialises every note of
    the clip, so list-style methods pass include_note_count=False unless the client
    asked for `include_note_counts`; note_count is then null."""
    is_midi = bool(safe_get(clip, "is_midi_clip", False))
    is_arr = bool(safe_get(clip, "is_arrangement_clip", arrangement_index is not None))
    summary = {
        "track": track_index,
        "slot": slot,
        "arrangement_index": arrangement_index,
        "name": safe_get(clip, "name", ""),
        "is_midi": is_midi,
        "is_audio": bool(safe_get(clip, "is_audio_clip", not is_midi)),
        "is_arrangement_clip": is_arr,
        "length": _num(safe_get(clip, "length")),
        "loop_start": _num(safe_get(clip, "loop_start")),
        "loop_end": _num(safe_get(clip, "loop_end")),
        "looping": bool(safe_get(clip, "looping", False)),
        "start_marker": _num(safe_get(clip, "start_marker")),
        "end_marker": _num(safe_get(clip, "end_marker")),
        "start_time": _num(safe_get(clip, "start_time")) if is_arr else None,
        "end_time": _num(safe_get(clip, "end_time")) if is_arr else None,
        "is_playing": bool(safe_get(clip, "is_playing", False)),
        "is_recording": bool(safe_get(clip, "is_recording", False)),
        "is_triggered": bool(safe_get(clip, "is_triggered", False)),
        "signature_numerator": safe_get(clip, "signature_numerator"),
        "signature_denominator": safe_get(clip, "signature_denominator"),
        "note_count": note_count(clip) if (is_midi and include_note_count) else None,
    }
    summary.update(color_fields(clip))
    return summary


def clip_summary_for(ref):
    return clip_summary(ref.clip, ref.track_index, ref.slot_index, ref.arrangement_index)


def note_dict(note):
    return {
        "id": _int_or(safe_get(note, "note_id"), None),
        "pitch": _int_or(safe_get(note, "pitch"), None),
        "start": _num(safe_get(note, "start_time")),
        "duration": _num(safe_get(note, "duration")),
        "velocity": _num(safe_get(note, "velocity")),
        "mute": bool(safe_get(note, "mute", False)),
        "probability": _num(safe_get(note, "probability", 1.0)),
        "velocity_deviation": _num(safe_get(note, "velocity_deviation", 0.0)),
        "release_velocity": _num(safe_get(note, "release_velocity", 64)),
    }


# --------------------------------------------------------------------------
# Devices
# --------------------------------------------------------------------------

DeviceRef = collections.namedtuple("DeviceRef", "device path container index is_mixer")
ParamRef = collections.namedtuple("ParamRef", "param index name original_name ambiguous")

MIXER_PATH = "mixer"
_SEND_LETTERS = "ABCDEFGHIJKL"


class MixerPseudoDevice(object):
    """The track mixer presented as a device with parameters
    Volume, Pan, Send A.., Track Activator (PROTOCOL.md section 5)."""

    def __init__(self, track):
        self.track = track
        self.mixer = safe_get(track, "mixer_device")
        self.name = "Mixer"
        self.class_name = "MixerDevice"
        self.class_display_name = "Mixer"
        self.is_mixer = True
        self.entries = []
        if self.mixer is None:
            return
        volume = safe_get(self.mixer, "volume")
        if volume is not None:
            self.entries.append(("Volume", safe_get(volume, "original_name", "Volume"), volume))
        panning = safe_get(self.mixer, "panning")
        if panning is not None:
            self.entries.append(("Pan", safe_get(panning, "original_name", "Pan"), panning))
        for i, send in enumerate(as_list(safe_get(self.mixer, "sends"))):
            letter = _SEND_LETTERS[i] if i < len(_SEND_LETTERS) else str(i)
            self.entries.append(("Send %s" % letter, safe_get(send, "original_name", "Send %s" % letter), send))
        activator = safe_get(self.mixer, "track_activator")
        if activator is not None:
            self.entries.append(("Track Activator", safe_get(activator, "original_name", "Track Activator"), activator))

    @property
    def parameters(self):
        return [entry[2] for entry in self.entries]

    def parameter_dicts(self):
        return [parameter_dict(param, i, name, original) for i, (name, original, param) in enumerate(self.entries)]

    def detail(self):
        return {
            "path": MIXER_PATH,
            "name": self.name,
            "class_name": self.class_name,
            "class_display_name": self.class_display_name,
            "type": "mixer",
            "is_active": True,
            "is_rack": False,
            "can_have_drum_pads": False,
            "chain_count": 0,
            "parameter_count": len(self.entries),
            "parameters": self.parameter_dicts(),
        }


def parameter_entries(device):
    """[(name, original_name, param)] for a device or a MixerPseudoDevice."""
    if isinstance(device, MixerPseudoDevice):
        return list(device.entries)
    entries = []
    for param in as_list(safe_get(device, "parameters")):
        name = str(safe_get(param, "name", ""))
        entries.append((name, str(safe_get(param, "original_name", name)), param))
    return entries


def parse_device_path(path):
    if not isinstance(path, str) or not path.strip():
        raise errors.invalid_params("Device path must be a string like \"0\", \"0/1/2\" or \"mixer\" (got %r)" % (path,),
                                    parameter="path")
    path = path.strip()
    if path == MIXER_PATH:
        return None
    parts = path.split("/")
    indexes = []
    for part in parts:
        part = part.strip()
        # isdecimal(), not isdigit(): "²".isdigit() is True but int("²") raises.
        if not part.isdecimal():
            raise errors.invalid_params("Device path %r must contain only non-negative integers separated by '/'" % path,
                                        parameter="path")
        indexes.append(int(part))
    if len(indexes) % 2 == 0:
        raise errors.invalid_params(
            "Device path %r must alternate device/chain indexes and end on a device (odd element count)" % path,
            parameter="path")
    return indexes


def resolve_device_path(track, path):
    """Resolve a device path on a track into a DeviceRef (container is track or Chain)."""
    indexes = parse_device_path(path)
    if indexes is None:
        return DeviceRef(MixerPseudoDevice(track), MIXER_PATH, track, None, True)
    normalized = "/".join(str(i) for i in indexes)
    devices = as_list(safe_get(track, "devices"))
    if indexes[0] >= len(devices):
        raise errors.not_found("device", indexes[0], len(devices), path=normalized)
    device = devices[indexes[0]]
    container = track
    position = indexes[0]
    walked = str(indexes[0])
    i = 1
    while i < len(indexes):
        chain_index, device_index = indexes[i], indexes[i + 1]
        if not safe_get(device, "can_have_chains", False):
            raise errors.invalid_state("not_a_rack", "Device at path %r (%s) is not a rack, so it has no chains" % (
                walked, safe_get(device, "name", "?")), path=walked)
        chains = as_list(safe_get(device, "chains"))
        if chain_index >= len(chains):
            raise errors.not_found("chain", chain_index, len(chains), path=walked)
        chain = chains[chain_index]
        chain_devices = as_list(safe_get(chain, "devices"))
        if device_index >= len(chain_devices):
            raise errors.not_found("device", device_index, len(chain_devices), path="%s/%d" % (walked, chain_index))
        device = chain_devices[device_index]
        container = chain
        position = device_index
        walked = "%s/%d/%d" % (walked, chain_index, device_index)
        i += 2
    return DeviceRef(device, normalized, container, position, False)


def resolve_parameter(device, parameter):
    """Resolve an int index or a (case-insensitive) name / original_name into a ParamRef."""
    entries = parameter_entries(device)
    if isinstance(parameter, bool) or parameter is None:
        raise errors.invalid_params("Parameter 'parameter' must be an index or a name (got %r)" % (parameter,),
                                    parameter="parameter")
    if isinstance(parameter, float) and parameter.is_integer():
        parameter = int(parameter)
    if isinstance(parameter, int):
        if parameter < 0 or parameter >= len(entries):
            raise errors.not_found("parameter", parameter, len(entries))
        name, original, param = entries[parameter]
        return ParamRef(param, parameter, name, original, False)
    if not isinstance(parameter, str):
        raise errors.invalid_params("Parameter 'parameter' must be an index or a name (got %s)" % type(parameter).__name__,
                                    parameter="parameter")
    wanted = parameter.strip().lower()
    matches = [i for i, (name, _o, _p) in enumerate(entries) if name.strip().lower() == wanted]
    if not matches:
        matches = [i for i, (_n, original, _p) in enumerate(entries) if original.strip().lower() == wanted]
    if not matches:
        raise errors.not_found("parameter", name=parameter, available=[name for name, _o, _p in entries])
    index = matches[0]
    name, original, param = entries[index]
    return ParamRef(param, index, name, original, len(matches) > 1)


def automation_state_name(param):
    state = safe_get(param, "automation_state")
    enum_cls = getattr(getattr(Live, "DeviceParameter", None), "AutomationState", None)
    return enum_name(state, enum_cls, ("none", "playing", "overridden"), "none")


def parameter_dict(param, index, name=None, original_name=None):
    if name is None:
        name = str(safe_get(param, "name", ""))
    if original_name is None:
        original_name = str(safe_get(param, "original_name", name))
    value = safe_get(param, "value")
    quantized = bool(safe_get(param, "is_quantized", False))
    items = None
    default = None
    if quantized:
        items = [str(item) for item in as_list(safe_get(param, "value_items"))]
    else:
        default = _num(safe_get(param, "default_value"))
    return {
        "index": index,
        "name": name,
        "original_name": original_name,
        "value": _num(value),
        "min": _num(safe_get(param, "min")),
        "max": _num(safe_get(param, "max")),
        "default": default,
        "display": value_display(param, value),
        "is_quantized": quantized,
        "value_items": items,
        "is_enabled": bool(safe_get(param, "is_enabled", True)),
        "automation_state": automation_state_name(param),
    }


def device_type_name(device):
    enum_cls = getattr(getattr(Live, "Device", None), "DeviceType", None)
    return enum_name(safe_get(device, "type"), enum_cls, ("audio_effect", "instrument", "midi_effect"), "unknown")


def device_summary(device, path):
    is_rack = bool(safe_get(device, "can_have_chains", False))
    chain_count = len(as_list(safe_get(device, "chains"))) if is_rack else 0
    return {
        "path": path,
        "name": safe_get(device, "name", ""),
        "class_name": safe_get(device, "class_name", ""),
        "class_display_name": safe_get(device, "class_display_name", safe_get(device, "name", "")),
        "type": device_type_name(device),
        "is_active": bool(safe_get(device, "is_active", False)),
        "is_rack": is_rack,
        "can_have_drum_pads": bool(safe_get(device, "can_have_drum_pads", False)),
        "chain_count": chain_count,
        "parameter_count": len(as_list(safe_get(device, "parameters"))),
    }


def device_parameters(device):
    return [parameter_dict(param, i, name, original) for i, (name, original, param) in enumerate(parameter_entries(device))]


def device_detail(device, path, include_params=True, depth=2):
    """DeviceSummary + parameters (+ chains/drum_pads for racks, recursing `depth` levels)."""
    detail = device_summary(device, path)
    if include_params:
        detail["parameters"] = device_parameters(device)
    if detail["is_rack"]:
        chains_out = []
        for ci, chain in enumerate(as_list(safe_get(device, "chains"))):
            chain_devices = []
            for di, child in enumerate(as_list(safe_get(chain, "devices"))):
                child_path = "%s/%d/%d" % (path, ci, di)
                chain_devices.append(device_entry(child, child_path, include_params, depth - 1))
            chains_out.append({"index": ci, "name": safe_get(chain, "name", ""), "devices": chain_devices})
        detail["chains"] = chains_out
        if detail["can_have_drum_pads"]:
            pads = []
            for pad in as_list(safe_get(device, "drum_pads")):
                pad_chains = as_list(safe_get(pad, "chains"))
                if not pad_chains:
                    continue
                pads.append({"note": _int_or(safe_get(pad, "note"), None),
                             "name": safe_get(pad, "name", ""),
                             "has_chain": True})
            detail["drum_pads"] = pads
    return detail


def device_entry(device, path, include_params=False, depth=2):
    """Summary for plain devices; detail (chains) for racks while depth > 0."""
    if safe_get(device, "can_have_chains", False) and depth > 0:
        return device_detail(device, path, include_params, depth)
    entry = device_summary(device, path)
    if include_params:
        entry["parameters"] = device_parameters(device)
    return entry


def device_entries(track, include_params=False, depth=2):
    return [device_entry(device, str(i), include_params, depth)
            for i, device in enumerate(as_list(safe_get(track, "devices")))]


def device_path_of(track, device, max_depth=8):
    """Find the path of a device object on a track (recursing into racks)."""
    if device is None:
        return None

    def walk(devices, prefix, depth):
        for i, candidate in enumerate(devices):
            path = "%s%d" % (prefix, i)
            if candidate is device or candidate == device:
                return path
            if depth > 0 and safe_get(candidate, "can_have_chains", False):
                for ci, chain in enumerate(as_list(safe_get(candidate, "chains"))):
                    found = walk(as_list(safe_get(chain, "devices")), "%s/%d/" % (path, ci), depth - 1)
                    if found is not None:
                        return found
        return None

    return walk(as_list(safe_get(track, "devices")), "", max_depth)


def find_parameter_owner(track, param, max_depth=8):
    """Path of the device (or 'mixer') owning a DeviceParameter on this track, or None."""
    if param is None:
        return None
    for _name, _original, candidate in MixerPseudoDevice(track).entries:
        if candidate is param or candidate == param:
            return MIXER_PATH

    def walk(devices, prefix, depth):
        for i, device in enumerate(devices):
            path = "%s%d" % (prefix, i)
            for candidate in as_list(safe_get(device, "parameters")):
                if candidate is param or candidate == param:
                    return path
            if depth > 0 and safe_get(device, "can_have_chains", False):
                for ci, chain in enumerate(as_list(safe_get(device, "chains"))):
                    found = walk(as_list(safe_get(chain, "devices")), "%s/%d/" % (path, ci), depth - 1)
                    if found is not None:
                        return found
        return None

    return walk(as_list(safe_get(track, "devices")), "", max_depth)


# --------------------------------------------------------------------------
# Scenes, selection, transport, scale, cue points
# --------------------------------------------------------------------------

def scene_tempo(scene):
    enabled = safe_get(scene, "tempo_enabled", None)
    tempo = safe_get(scene, "tempo", None)
    if enabled is False or tempo is None:
        return None
    try:
        tempo = float(tempo)
    except (TypeError, ValueError):
        return None
    if tempo < 0:
        return None
    return tempo


def scene_summary(song, scene, index):
    summary = {
        "index": index,
        "name": safe_get(scene, "name", ""),
        "is_triggered": bool(safe_get(scene, "is_triggered", False)),
        "tempo": scene_tempo(scene),
        "is_empty": bool(safe_get(scene, "is_empty", False)),
    }
    summary.update(color_fields(scene))
    return summary


def locate_clip(song, clip):
    """(track_index, slot_index, arrangement_index) for a clip object, or (None, None, None)."""
    if clip is None:
        return None, None, None
    for ti, track in enumerate(as_list(song.tracks)):
        for si, slot in enumerate(as_list(safe_get(track, "clip_slots"))):
            candidate = safe_get(slot, "clip")
            if candidate is not None and (candidate is clip or candidate == clip):
                return ti, si, None
        for ai, candidate in enumerate(as_list(safe_get(track, "arrangement_clips"))):
            if candidate is clip or candidate == clip:
                return ti, None, ai
    return None, None, None


def selection(song):
    view = song.view
    sel_track = safe_get(view, "selected_track")
    t_index, t_type = track_index_of(song, sel_track)
    track_info = None
    if sel_track is not None and t_type is not None:
        track_info = {"index": t_index, "track_type": t_type, "name": safe_get(sel_track, "name", "")}

    sel_scene = safe_get(view, "selected_scene")
    scene_info = None
    if sel_scene is not None:
        s_index = index_of(as_list(song.scenes), sel_scene)
        scene_info = {"index": s_index, "name": safe_get(sel_scene, "name", "")}

    slot_info = None
    slot = safe_get(view, "highlighted_clip_slot")
    if slot is not None and sel_track is not None and t_type == "track":
        s_index = index_of(as_list(safe_get(sel_track, "clip_slots")), slot)
        has_clip = bool(safe_get(slot, "has_clip", False))
        clip = safe_get(slot, "clip") if has_clip else None
        slot_info = {"track": t_index, "slot": s_index, "has_clip": has_clip,
                     "clip_name": safe_get(clip, "name", None) if clip is not None else None}

    detail_info = None
    detail_clip = safe_get(view, "detail_clip")
    if detail_clip is not None:
        ti, si, ai = locate_clip(song, detail_clip)
        detail_info = {"track": ti, "slot": si, "name": safe_get(detail_clip, "name", "")}
        if ai is not None:
            detail_info["arrangement_index"] = ai

    device_info = None
    device = None
    if sel_track is not None:
        track_view = safe_get(sel_track, "view")
        device = safe_get(track_view, "selected_device") if track_view is not None else None
        if device is not None:
            device_info = {"path": device_path_of(sel_track, device), "name": safe_get(device, "name", "")}

    param_info = None
    param = safe_get(view, "selected_parameter")
    if param is not None:
        owner = find_parameter_owner(sel_track, param) if sel_track is not None else None
        param_info = {"name": safe_get(param, "name", ""), "device_path": owner}

    return {"track": track_info, "scene": scene_info, "clip_slot": slot_info,
            "detail_clip": detail_info, "device": device_info, "parameter": param_info}


def transport(song):
    return {
        "tempo": _num(safe_get(song, "tempo")),
        "signature_numerator": safe_get(song, "signature_numerator"),
        "signature_denominator": safe_get(song, "signature_denominator"),
        "is_playing": bool(safe_get(song, "is_playing", False)),
        "position": _num(safe_get(song, "current_song_time")),
        "loop": {"enabled": bool(safe_get(song, "loop", False)),
                 "start": _num(safe_get(song, "loop_start")),
                 "length": _num(safe_get(song, "loop_length"))},
        "metronome": bool(safe_get(song, "metronome", False)),
        "record_mode": bool(safe_get(song, "record_mode", False)),
        "session_record": bool(safe_get(song, "session_record", False)),
        "song_length": _num(safe_get(song, "song_length")),
    }


def scale_supported(song):
    return has_attr(song, "scale_name") and has_attr(song, "root_note")


def scale(song):
    if not scale_supported(song):
        return None
    root = _int_or(safe_get(song, "root_note", 0), 0)
    return {
        "root_note": root,
        "root_name": NOTE_NAMES[root % 12],
        "scale_name": safe_get(song, "scale_name", ""),
        "scale_intervals": [int(i) for i in as_list(safe_get(song, "scale_intervals"))],
    }


def cue_point(cue, index):
    return {"index": index, "name": safe_get(cue, "name", ""), "time": _num(safe_get(cue, "time"))}
