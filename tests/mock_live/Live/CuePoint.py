"""Live.CuePoint (arrangement locator)."""
from ._core import LomObject


class CuePoint(LomObject):

    def __init__(self, song, time, name=""):
        self._song = song
        self._time = float(time)
        self._name = name

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        self._name = str(value)

    @property
    def time(self):
        return self._time

    def jump(self):
        """When playing, jump quantized; otherwise move the start position."""
        self._song.current_song_time = self._time

    def __repr__(self):
        d = object.__getattribute__(self, "__dict__")
        return "<CuePoint %r @ %s>" % (d["_name"], d["_time"])
