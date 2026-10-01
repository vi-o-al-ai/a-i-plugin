"""Live.Scene."""
from ._core import LomObject, color_for_index, nearest_color_index, check_color_index, check_number


class Scene(LomObject):

    def __init__(self, song, name=""):
        self._song = song
        self._name = name
        self._color_index = None
        self._tempo = -1.0
        self._tempo_enabled = False
        self._is_triggered = False
        self.time_signature_numerator = 4
        self.time_signature_denominator = 4
        self.time_signature_enabled = False

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
        self._color_index = check_color_index(value)

    @property
    def is_triggered(self):
        return self._is_triggered

    @property
    def is_empty(self):
        index = self._index()
        for track in self._song._tracks:
            slots = track._clip_slots
            if index < len(slots) and slots[index]._clip is not None:
                return False
        return True

    @property
    def tempo(self):
        return self._tempo

    @tempo.setter
    def tempo(self, value):
        value = check_number(value, "tempo")
        if value < 0:
            self._tempo = -1.0
            self._tempo_enabled = False
            return
        if value < 20.0 or value > 999.0:
            raise RuntimeError("Scene tempo out of range")
        self._tempo = value
        self._tempo_enabled = True

    @property
    def tempo_enabled(self):
        return self._tempo_enabled

    @tempo_enabled.setter
    def tempo_enabled(self, value):
        self._tempo_enabled = bool(value)
        if self._tempo_enabled and self._tempo < 0:
            self._tempo = 120.0

    @property
    def clip_slots(self):
        index = self._index()
        return tuple(track._clip_slots[index] for track in self._song._tracks if index < len(track._clip_slots))

    def fire(self, force_legato=False, can_select_scene_on_launch=True):
        index = self._index()
        for track in self._song._tracks:
            slots = track._clip_slots
            if index < len(slots):
                track._fire_slot(slots[index])
        if can_select_scene_on_launch:
            self._song.view.selected_scene = self

    def set_fire_button_state(self, state):
        if state:
            self.fire()

    def _index(self):
        return self._song._scenes.index(self)

    def __repr__(self):
        return "<Scene %r>" % object.__getattribute__(self, "_name")
