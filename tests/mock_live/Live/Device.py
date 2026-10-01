"""Live.Device."""
from ._core import LomObject, make_enum
from .DeviceParameter import DeviceParameter

DeviceType = make_enum("Live.Device.DeviceType", ("audio_effect", "instrument", "midi_effect", "undefined"))


class Device(LomObject):

    class View(LomObject):
        def __init__(self):
            self.is_collapsed = False

    def __init__(self, name, class_name, class_display_name=None, device_type=DeviceType.audio_effect,
                 parameters=None, device_on=True):
        self._name = name
        self._class_name = class_name
        self._class_display_name = class_display_name if class_display_name is not None else name
        self._type = device_type
        params = []
        if device_on:
            params.append(DeviceParameter("Device On", 1.0, 0.0, 1.0, is_quantized=True, value_items=["Off", "On"]))
        params.extend(parameters or [])
        self._parameters = params
        self._track = None
        self._chain = None
        self.view = Device.View()

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        self._name = str(value)

    @property
    def class_name(self):
        return self._class_name

    @property
    def class_display_name(self):
        return self._class_display_name

    @property
    def type(self):
        return self._type

    @property
    def is_active(self):
        on = True
        if self._parameters and self._parameters[0].name.startswith("Device On"):
            on = self._parameters[0].value > 0.5
        parent_active = True
        chain = self._chain
        if chain is not None and chain._rack is not None:
            parent_active = chain._rack.is_active
        return bool(on and parent_active)

    @property
    def parameters(self):
        return tuple(self._parameters)

    @property
    def can_have_chains(self):
        return False

    @property
    def can_have_drum_pads(self):
        return False

    def store_chosen_bank(self, script_index, bank_index):
        pass

    # Listener API (no-ops)
    def add_parameters_listener(self, callback):
        pass

    def remove_parameters_listener(self, callback):
        pass

    def add_name_listener(self, callback):
        pass

    def remove_name_listener(self, callback):
        pass

    # Mock internals
    def _set_track(self, track):
        self._track = track

    def __repr__(self):
        return "<%s %r>" % (type(self).__name__, object.__getattribute__(self, "_name"))
