"""Live.MixerDevice (track mixer)."""
import math

from ._core import LomObject
from .DeviceParameter import DeviceParameter

SEND_LETTERS = "ABCDEFGHIJKL"


def fader_to_db(value):
    if value <= 0.0:
        return float("-inf")
    if value >= 0.85:
        return (value - 0.85) / 0.15 * 6.0
    return 40.0 * math.log10(value / 0.85)


def fader_display(value):
    db = fader_to_db(value)
    if db == float("-inf"):
        return "-inf dB"
    return "%.1f dB" % db


def pan_display(value):
    if abs(value) < 0.005:
        return "C"
    amount = int(round(abs(value) * 50))
    return "%d%s" % (amount, "L" if value < 0 else "R")


class MixerDevice(LomObject):

    def __init__(self, kind="midi"):
        self._kind = kind
        self.volume = DeviceParameter("Volume", 0.85, 0.0, 1.0, default=0.85, display=fader_display)
        self.panning = DeviceParameter("Pan", 0.0, -1.0, 1.0, default=0.0, display=pan_display)
        self._sends = []
        self.track_activator = DeviceParameter("Track Activator", 1.0, 0.0, 1.0, is_quantized=True,
                                               value_items=["Off", "On"])
        self.crossfade_assign = 1
        self.panning_mode = 0
        if kind == "master":
            self.crossfader = DeviceParameter("Crossfader", 0.0, -1.0, 1.0, default=0.0)
            self.cue_volume = DeviceParameter("Cue Volume", 0.85, 0.0, 1.0, default=0.85, display=fader_display)
            self.song_tempo = DeviceParameter("Song Tempo", 120.0, 20.0, 999.0, default=120.0,
                                              display=lambda v: "%.2f BPM" % v)

    @property
    def sends(self):
        return tuple(self._sends)

    # Mock internals
    def _add_send(self):
        index = len(self._sends)
        letter = SEND_LETTERS[index] if index < len(SEND_LETTERS) else str(index)
        self._sends.append(DeviceParameter("Send %s" % letter, 0.0, 0.0, 1.0, default=0.0, display=fader_display))

    def _remove_send(self, index):
        if 0 <= index < len(self._sends):
            self._sends.pop(index)
