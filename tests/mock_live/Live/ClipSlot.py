"""Live.ClipSlot."""
from ._core import LomObject, check_number
from .Clip import Clip


class ClipSlot(LomObject):

    def __init__(self, track):
        self._track = track
        self._clip = None
        self.has_stop_button = True

    @property
    def has_clip(self):
        return self._clip is not None

    @property
    def clip(self):
        return self._clip

    @property
    def is_playing(self):
        return self._clip is not None and self._clip._is_playing

    @property
    def is_recording(self):
        return False

    @property
    def is_triggered(self):
        return self._clip is not None and self._clip._is_triggered

    @property
    def playing_status(self):
        return 1 if self.is_playing else 0

    @property
    def will_record_on_start(self):
        return False

    @property
    def is_group_slot(self):
        return self._track._kind == "group"

    @property
    def controls_other_clips(self):
        return False

    @property
    def color(self):
        return None

    @property
    def color_index(self):
        return None

    def create_clip(self, length):
        length = check_number(length, "length")
        if self._clip is not None:
            raise RuntimeError("Slot already has a clip")
        if not self._track.has_midi_input:
            raise RuntimeError("Cannot create a MIDI clip in a slot of a non-MIDI track")
        if length <= 0.0:
            raise RuntimeError("Clip length must be positive")
        self._clip = Clip("", length, True, self._track, self)

    def create_audio_clip(self, path):
        if self._clip is not None:
            raise RuntimeError("Slot already has a clip")
        if not self._track.has_audio_input:
            raise RuntimeError("Audio clips need an audio track")
        self._clip = Clip(str(path).rsplit("/", 1)[-1], 4.0, False, self._track, self)

    def delete_clip(self):
        if self._clip is None:
            raise RuntimeError("Slot is empty")
        self._clip._slot = None
        self._clip = None

    def fire(self, record_length=None, launch_quantization=None, force_legato=False):
        self._track._fire_slot(self)

    def stop(self):
        self._track._stop_slot(self)

    def set_fire_button_state(self, state):
        if state:
            self.fire()

    def duplicate_clip_to(self, target_slot):
        if self._clip is None:
            raise RuntimeError("Source slot is empty")
        if self._track._kind == "group" or target_slot._track._kind == "group":
            raise RuntimeError("Cannot duplicate clips from or to group tracks")
        if self._clip.is_midi_clip != target_slot._track.has_midi_input:
            raise RuntimeError("Source and target tracks have different types")
        target_slot._clip = self._clip._copy(target_slot._track, target_slot)

    def __repr__(self):
        return "<ClipSlot %s>" % ("clip" if object.__getattribute__(self, "_clip") is not None else "empty")
