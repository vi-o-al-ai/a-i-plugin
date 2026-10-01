"""Live.Chain, Live.DrumChain and Live.ChainMixerDevice."""
from ._core import LomObject, color_for_index, check_color_index
from .DeviceParameter import DeviceParameter


class ChainMixerDevice(LomObject):
    def __init__(self):
        self.volume = DeviceParameter("Chain Volume", 0.85, 0.0, 1.0, default=0.85)
        self.panning = DeviceParameter("Chain Pan", 0.0, -1.0, 1.0, default=0.0)
        self.sends = ()
        self.chain_activator = DeviceParameter("Chain Activator", 1.0, 0.0, 1.0, is_quantized=True,
                                               value_items=["Off", "On"])


class Chain(LomObject):

    def __init__(self, name, devices=None, color_index=None):
        self._name = name
        self._devices = []
        self._rack = None
        self.mute = False
        self.solo = False
        self._color_index = color_index
        self.is_auto_colored = True
        self.mixer_device = ChainMixerDevice()
        for device in devices or []:
            self._insert_device(device)

    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        self._name = str(value)

    @property
    def devices(self):
        return tuple(self._devices)

    @property
    def muted_via_solo(self):
        return False

    @property
    def color(self):
        return color_for_index(self._color_index)

    @property
    def color_index(self):
        return self._color_index

    @color_index.setter
    def color_index(self, value):
        self._color_index = check_color_index(value)

    @property
    def has_midi_input(self):
        return True

    @property
    def has_audio_input(self):
        return True

    @property
    def has_audio_output(self):
        return True

    @property
    def has_midi_output(self):
        return False

    def delete_device(self, index):
        if isinstance(index, bool) or not isinstance(index, int) or index < 0 or index >= len(self._devices):
            raise RuntimeError("Invalid device index %r" % (index,))
        device = self._devices.pop(index)
        device._chain = None
        device._track = None

    def insert_device(self, device_name, index=None):
        raise RuntimeError("Chain.insert_device is not available in this Live")

    # Mock internals
    def _insert_device(self, device, index=None):
        device._chain = self
        rack = self._rack
        if rack is not None:
            device._set_track(rack._track)
        if index is None or index < 0 or index > len(self._devices):
            self._devices.append(device)
        else:
            self._devices.insert(index, device)

    def __repr__(self):
        return "<Chain %r>" % object.__getattribute__(self, "_name")


class DrumChain(Chain):

    def __init__(self, name, note, devices=None, color_index=None):
        Chain.__init__(self, name, devices, color_index)
        self.out_note = int(note)
        self.in_note = int(note)
        self.choke_group = 0
