"""Live.DrumPad."""
from ._core import LomObject


class DrumPad(LomObject):

    def __init__(self, rack, note):
        self._rack = rack
        self._note = int(note)
        self.mute = False
        self.solo = False

    @property
    def note(self):
        return self._note

    @property
    def chains(self):
        return tuple(chain for chain in self._rack._chains if getattr(chain, "in_note", None) == self._note)

    @property
    def name(self):
        chains = self.chains
        return chains[0].name if chains else ""

    def delete_all_chains(self):
        for chain in list(self.chains):
            self._rack._chains.remove(chain)

    def __repr__(self):
        return "<DrumPad %d>" % object.__getattribute__(self, "_note")
