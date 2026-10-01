"""Live.RackDevice (Instrument/Audio Effect/MIDI Effect/Drum racks)."""
from ._core import LomObject
from .Device import Device, DeviceType
from .DeviceParameter import DeviceParameter
from .DrumPad import DrumPad


def _macro_display(value):
    return "%.0f" % value


class RackDevice(Device):

    class View(LomObject):
        def __init__(self, rack):
            self._rack = rack
            self.selected_chain = None
            self.selected_drum_pad = None
            self.drum_pads_scroll_position = 0
            self.is_collapsed = False

    def __init__(self, name, class_name, class_display_name=None, device_type=DeviceType.instrument,
                 chains=None, is_drum_rack=False, macros=8):
        params = [DeviceParameter("Macro %d" % (i + 1), 0.0, 0.0, 127.0, default=0.0, display=_macro_display)
                  for i in range(macros)]
        Device.__init__(self, name, class_name, class_display_name, device_type, params)
        self._chains = []
        self._is_drum_rack = bool(is_drum_rack)
        self._drum_pads = [DrumPad(self, note) for note in range(128)] if is_drum_rack else []
        self.view = RackDevice.View(self)
        for chain in chains or []:
            self._add_chain(chain)
        if self._chains:
            self.view.selected_chain = self._chains[0]

    @property
    def can_have_chains(self):
        return True

    @property
    def can_have_drum_pads(self):
        return self._is_drum_rack

    @property
    def chains(self):
        return tuple(self._chains)

    @property
    def return_chains(self):
        return ()

    @property
    def drum_pads(self):
        if not self._is_drum_rack:
            raise RuntimeError("drum_pads: this rack cannot have drum pads")
        return tuple(self._drum_pads)

    @property
    def visible_drum_pads(self):
        if not self._is_drum_rack:
            raise RuntimeError("visible_drum_pads: this rack cannot have drum pads")
        return tuple(self._drum_pads[36:52])

    @property
    def has_drum_pads(self):
        return self._is_drum_rack and bool(self._chains)

    @property
    def macros_mapped(self):
        return tuple(False for _ in self._parameters[1:])

    @property
    def has_macro_mappings(self):
        return False

    @property
    def variation_count(self):
        return 0

    def randomize_macros(self):
        pass

    def insert_chain(self, index):
        raise RuntimeError("RackDevice.insert_chain is not available in this Live")

    # Mock internals
    def _add_chain(self, chain, index=None):
        chain._rack = self
        for device in chain._devices:
            device._set_track(self._track)
        if index is None:
            self._chains.append(chain)
        else:
            self._chains.insert(index, chain)

    def _set_track(self, track):
        self._track = track
        for chain in self._chains:
            for device in chain._devices:
                device._set_track(track)
