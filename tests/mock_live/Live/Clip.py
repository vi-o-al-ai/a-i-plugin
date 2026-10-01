"""Live.Clip: clips, the Live 11+ note API, and automation envelopes."""
from ._core import LomObject, make_enum, color_for_index, nearest_color_index, check_color_index, check_number

# Ableton's own member spellings, including the historical misspellings the real
# enum carries (q_sixtenth, q_thirtytwoth); the script maps the public names onto them.
ClipLaunchQuantization = make_enum("Live.Clip.ClipLaunchQuantization", (
    "q_global", "q_none", "q_8_bars", "q_4_bars", "q_2_bars", "q_bar", "q_half", "q_half_triplet", "q_quarter",
    "q_quarter_triplet", "q_eight", "q_eight_triplet", "q_sixtenth", "q_sixtenth_triplet", "q_thirtytwoth"))
LaunchMode = make_enum("Live.Clip.LaunchMode", ("trigger", "gate", "toggle", "repeat"))
GridQuantization = make_enum("Live.Clip.GridQuantization", (
    "no_grid", "g_thirtysecond", "g_sixteenth", "g_eighth", "g_quarter", "g_half", "g_bar", "g_2_bars",
    "g_4_bars", "g_8_bars"))
WarpMode = make_enum("Live.Clip.WarpMode", ("beats", "tones", "texture", "repitch", "complex", "rex", "complex_pro"))

NOTE_ATTRS = ("pitch", "start_time", "duration", "velocity", "mute", "probability", "velocity_deviation",
              "release_velocity")


class MidiNote(LomObject):
    """A note as returned by get_notes_extended; attributes (except note_id) are writable."""

    def __init__(self, note_id, pitch, start_time, duration, velocity=100.0, mute=False, probability=1.0,
                 velocity_deviation=0.0, release_velocity=64.0):
        self.note_id = int(note_id)
        self.pitch = int(pitch)
        self.start_time = float(start_time)
        self.duration = float(duration)
        self.velocity = float(velocity)
        self.mute = bool(mute)
        self.probability = float(probability)
        self.velocity_deviation = float(velocity_deviation)
        self.release_velocity = float(release_velocity)

    def _copy(self):
        return MidiNote(self.note_id, self.pitch, self.start_time, self.duration, self.velocity, self.mute,
                        self.probability, self.velocity_deviation, self.release_velocity)

    def __repr__(self):
        d = object.__getattribute__(self, "__dict__")
        return "<MidiNote id=%d pitch=%d start=%.3f dur=%.3f vel=%.0f>" % (
            d["note_id"], d["pitch"], d["start_time"], d["duration"], d["velocity"])


class MidiNoteSpecification(LomObject):
    """Keyword-only constructor; pitch/start_time/duration are required (TypeError otherwise)."""

    _REQUIRED = ("pitch", "start_time", "duration")
    _OPTIONAL = ("velocity", "mute", "probability", "velocity_deviation", "release_velocity")

    def __init__(self, **kwargs):
        for key in kwargs:
            if key not in self._REQUIRED and key not in self._OPTIONAL:
                raise TypeError("MidiNoteSpecification() got an unexpected keyword argument '%s'" % key)
        for key in self._REQUIRED:
            if key not in kwargs:
                raise TypeError("MidiNoteSpecification() missing required keyword argument '%s'" % key)
        self.pitch = int(kwargs["pitch"])
        self.start_time = float(kwargs["start_time"])
        self.duration = float(kwargs["duration"])
        self.velocity = float(kwargs.get("velocity", 100.0))
        self.mute = bool(kwargs.get("mute", False))
        self.probability = float(kwargs.get("probability", 1.0))
        self.velocity_deviation = float(kwargs.get("velocity_deviation", 0.0))
        self.release_velocity = float(kwargs.get("release_velocity", 64.0))


class MidiNoteVector(list):
    """list subclass standing in for Live.Clip.MidiNoteVector (supports append/extend)."""


class AutomationEnvelope(LomObject):
    """Step automation: insert_step(time, length, value); value_at_time is piecewise constant."""

    def __init__(self, parameter):
        self._parameter = parameter
        self._steps = []  # (start, end, value) in insertion order; later steps win

    def insert_step(self, time, length, value):
        time = check_number(time, "time")
        length = check_number(length, "length")
        value = check_number(value, "value")
        if length <= 0.0:
            raise RuntimeError("insert_step: length must be positive")
        low, high = self._parameter.min, self._parameter.max
        value = min(max(value, min(low, high)), max(low, high))
        self._steps.append((time, time + length, value))

    def value_at_time(self, time):
        time = check_number(time, "time")
        for start, end, value in reversed(self._steps):
            if start - 1e-9 <= time < end - 1e-9:
                return value
        return self._parameter.value

    def _shifted_copy(self, parameter, offset):
        copy = AutomationEnvelope(parameter)
        copy._steps = [(s, e, v) for s, e, v in self._steps] + [(s + offset, e + offset, v) for s, e, v in self._steps]
        return copy


class Clip(LomObject):

    class View(LomObject):
        def __init__(self, clip):
            self._clip = clip

        def show_loop(self):
            pass

    def __init__(self, name="", length=4.0, is_midi=True, track=None, slot=None, is_arrangement=False,
                 start_time=None, color_index=None):
        self._name = name
        self._is_midi = bool(is_midi)
        self._track = track
        self._slot = slot
        self._is_arrangement = bool(is_arrangement)
        self._start_time = float(start_time) if start_time is not None else None
        if color_index is None and track is not None:
            color_index = track._color_index
        self._color_index = color_index if color_index is not None else 0
        self._loop_start = 0.0
        self._loop_end = float(length)
        self._looping = True
        self._start_marker = 0.0
        self._end_marker = float(length)
        self._is_playing = False
        self._is_triggered = False
        self._is_recording = False
        self.signature_numerator = 4
        self.signature_denominator = 4
        self.launch_quantization = ClipLaunchQuantization.q_global
        self.launch_mode = LaunchMode.trigger
        self.legato = False
        self.velocity_amount = 0.0
        self.muted = False
        self._notes = []
        self._next_note_id = 1
        self._envelopes = {}
        self.playing_position = 0.0
        self.view = Clip.View(self)
        # audio-only
        self.file_path = "" if is_midi else "/samples/%s.wav" % (name or "sample")
        self.warping = True
        self.warp_mode = WarpMode.beats
        self.pitch_coarse = 0
        self.pitch_fine = 0
        self.gain = 1.0
        self.ram_mode = False

    # ---- basics ----
    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        self._name = str(value)

    @property
    def color(self):
        return color_for_index(self._color_index)

    @color.setter
    def color(self, value):
        self._color_index = nearest_color_index(value)

    @property
    def color_index(self):
        return self._color_index

    @color_index.setter
    def color_index(self, value):
        value = check_color_index(value)
        if value is None:
            raise RuntimeError("Clip color_index cannot be None")
        self._color_index = value

    @property
    def is_midi_clip(self):
        return self._is_midi

    @property
    def is_audio_clip(self):
        return not self._is_midi

    @property
    def is_arrangement_clip(self):
        return self._is_arrangement

    @property
    def is_session_clip(self):
        return not self._is_arrangement

    @property
    def length(self):
        if self._looping:
            return self._loop_end - self._loop_start
        return self._end_marker - self._start_marker

    # ---- loop / markers (Live rejects start >= end) ----
    @property
    def loop_start(self):
        return self._loop_start

    @loop_start.setter
    def loop_start(self, value):
        value = check_number(value, "loop_start")
        if value >= self._loop_end:
            raise RuntimeError("loop_start (%s) must be smaller than loop_end (%s)" % (value, self._loop_end))
        self._loop_start = value

    @property
    def loop_end(self):
        return self._loop_end

    @loop_end.setter
    def loop_end(self, value):
        value = check_number(value, "loop_end")
        if value <= self._loop_start:
            raise RuntimeError("loop_end (%s) must be larger than loop_start (%s)" % (value, self._loop_start))
        self._loop_end = value

    @property
    def looping(self):
        return self._looping

    @looping.setter
    def looping(self, value):
        self._looping = bool(value)

    @property
    def start_marker(self):
        return self._start_marker

    @start_marker.setter
    def start_marker(self, value):
        value = check_number(value, "start_marker")
        if value >= self._end_marker:
            raise RuntimeError("start_marker (%s) must be smaller than end_marker (%s)" % (value, self._end_marker))
        self._start_marker = value

    @property
    def end_marker(self):
        return self._end_marker

    @end_marker.setter
    def end_marker(self, value):
        value = check_number(value, "end_marker")
        if value <= self._start_marker:
            raise RuntimeError("end_marker (%s) must be larger than start_marker (%s)" % (value, self._start_marker))
        self._end_marker = value

    @property
    def position(self):
        return self._loop_start

    @position.setter
    def position(self, value):
        length = self._loop_end - self._loop_start
        self._loop_start = check_number(value, "position")
        self._loop_end = self._loop_start + length

    # ---- playback state ----
    @property
    def is_playing(self):
        return self._is_playing

    @is_playing.setter
    def is_playing(self, value):
        if value:
            self.fire()
        else:
            self.stop()

    @property
    def is_triggered(self):
        return self._is_triggered

    @property
    def is_recording(self):
        return self._is_recording

    @property
    def is_overdubbing(self):
        return False

    @property
    def start_time(self):
        if self._is_arrangement:
            return self._start_time
        return 0.0

    @property
    def end_time(self):
        if self._is_arrangement:
            return self._start_time + self.length
        return self.length

    @property
    def has_envelopes(self):
        return bool(self._envelopes)

    def fire(self):
        if self._slot is not None:
            self._slot.fire()
        else:
            self._is_playing = True

    def stop(self):
        if self._slot is not None:
            self._slot.stop()
        else:
            self._is_playing = False

    def set_fire_button_state(self, state):
        if state:
            self.fire()

    def move_playing_pos(self, beats):
        self.playing_position += float(beats)

    def crop(self):
        pass

    # ---- notes (Live 11+ API) ----
    def _require_midi(self):
        if not self._is_midi:
            raise RuntimeError("Note operations are only available on MIDI clips")

    def _in_window(self, note, from_pitch, pitch_span, from_time, time_span):
        return (from_pitch <= note.pitch < from_pitch + pitch_span and
                from_time <= note.start_time < from_time + time_span)

    def get_notes_extended(self, from_pitch, pitch_span, from_time, time_span):
        self._require_midi()
        from_pitch = int(from_pitch)
        pitch_span = int(pitch_span)
        from_time = check_number(from_time, "from_time")
        time_span = check_number(time_span, "time_span")
        vector = MidiNoteVector()
        for note in self._notes:
            if self._in_window(note, from_pitch, pitch_span, from_time, time_span):
                vector.append(note._copy())
        vector.sort(key=lambda n: (n.start_time, n.pitch))
        return vector

    def get_all_notes_extended(self):
        return self.get_notes_extended(0, 128, -1.0e9, 2.0e9)

    def get_selected_notes_extended(self):
        return MidiNoteVector()

    def add_new_notes(self, specifications):
        self._require_midi()
        try:
            specs = list(specifications)
        except TypeError:
            raise TypeError("add_new_notes expects an iterable of MidiNoteSpecification")
        for spec in specs:
            if not isinstance(spec, MidiNoteSpecification):
                raise TypeError("add_new_notes expects MidiNoteSpecification objects, got %s" % type(spec).__name__)
        for spec in specs:
            note = MidiNote(self._next_note_id, spec.pitch, spec.start_time, spec.duration, spec.velocity,
                            spec.mute, spec.probability, spec.velocity_deviation, spec.release_velocity)
            self._next_note_id += 1
            self._notes.append(note)

    def remove_notes_extended(self, from_pitch, pitch_span, from_time, time_span):
        self._require_midi()
        from_time = check_number(from_time, "from_time")
        time_span = check_number(time_span, "time_span")
        self._notes = [n for n in self._notes
                       if not self._in_window(n, int(from_pitch), int(pitch_span), from_time, time_span)]

    def remove_notes_by_id(self, note_ids):
        self._require_midi()
        ids = set(int(i) for i in note_ids)
        self._notes = [n for n in self._notes if n.note_id not in ids]

    def get_notes_by_id(self, note_ids):
        self._require_midi()
        by_id = dict((n.note_id, n) for n in self._notes)
        vector = MidiNoteVector()
        for note_id in note_ids:
            note = by_id.get(int(note_id))
            if note is not None:
                vector.append(note._copy())
        return vector

    def apply_note_modifications(self, notes):
        self._require_midi()
        by_id = dict((n.note_id, n) for n in self._notes)
        for incoming in notes:
            target = by_id.get(int(incoming.note_id))
            if target is None:
                raise RuntimeError("apply_note_modifications: note id %d is not in this clip" % incoming.note_id)
            if not 0 <= int(incoming.pitch) <= 127:
                raise RuntimeError("pitch out of range")
            if incoming.duration <= 0:
                raise RuntimeError("duration must be positive")
            for attr in NOTE_ATTRS:
                setattr(target, attr, getattr(incoming, attr))

    def select_all_notes(self):
        pass

    def deselect_all_notes(self):
        pass

    def select_notes_by_id(self, note_ids):
        pass

    def duplicate_loop(self):
        length = self._loop_end - self._loop_start
        new_notes = []
        for note in self._notes:
            if self._loop_start <= note.start_time < self._loop_end:
                copy = note._copy()
                copy.note_id = self._next_note_id
                self._next_note_id += 1
                copy.start_time += length
                new_notes.append(copy)
        self._notes.extend(new_notes)
        self._loop_end += length
        if self._end_marker < self._loop_end:
            self._end_marker = self._loop_end
        for param, envelope in list(self._envelopes.items()):
            self._envelopes[param] = envelope._shifted_copy(param, length)

    def duplicate_region(self, region_start, region_length, destination_time, pitch=-1, transposition_amount=0):
        for note in list(self._notes):
            if region_start <= note.start_time < region_start + region_length and (pitch < 0 or note.pitch == pitch):
                copy = note._copy()
                copy.note_id = self._next_note_id
                self._next_note_id += 1
                copy.start_time = destination_time + (note.start_time - region_start)
                copy.pitch = min(127, max(0, copy.pitch + transposition_amount))
                self._notes.append(copy)

    def quantize(self, grid, amount):
        pass

    # ---- envelopes ----
    def automation_envelope(self, parameter):
        if self._is_arrangement:
            return None
        return self._envelopes.get(parameter)

    def create_automation_envelope(self, parameter):
        if self._is_arrangement:
            raise RuntimeError("Cannot create automation envelopes on arrangement clips through the API")
        envelope = self._envelopes.get(parameter)
        if envelope is None:
            envelope = AutomationEnvelope(parameter)
            self._envelopes[parameter] = envelope
        return envelope

    def clear_envelope(self, parameter):
        self._envelopes.pop(parameter, None)

    def clear_all_envelopes(self):
        self._envelopes.clear()

    # ---- mock internals ----
    def _copy(self, track=None, slot=None, is_arrangement=False, start_time=None):
        clip = Clip(self._name, self._loop_end - self._loop_start, self._is_midi, track, slot, is_arrangement,
                    start_time, self._color_index)
        clip._loop_start = self._loop_start
        clip._loop_end = self._loop_end
        clip._looping = self._looping
        clip._start_marker = self._start_marker
        clip._end_marker = self._end_marker
        clip.signature_numerator = self.signature_numerator
        clip.signature_denominator = self.signature_denominator
        clip.launch_quantization = self.launch_quantization
        clip.launch_mode = self.launch_mode
        for note in self._notes:
            copy = note._copy()
            copy.note_id = clip._next_note_id
            clip._next_note_id += 1
            clip._notes.append(copy)
        for param, envelope in self._envelopes.items():
            copy = AutomationEnvelope(param)
            copy._steps = list(envelope._steps)
            clip._envelopes[param] = copy
        return clip

    def __repr__(self):
        return "<Clip %r>" % object.__getattribute__(self, "_name")
