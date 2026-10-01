"""Test double for Ableton Live's embedded `Live` module.

Names mirror the real API (docs/research/live-api.md). Every object derives from
_core.LomObject, whose attribute access asserts it runs on the harness-designated
main thread.
"""
from . import _core  # noqa: F401
from . import Base  # noqa: F401
from . import DeviceParameter  # noqa: F401
from . import Device  # noqa: F401
from . import Chain  # noqa: F401
from . import DrumPad  # noqa: F401
from . import RackDevice  # noqa: F401
from . import MixerDevice  # noqa: F401
from . import Clip  # noqa: F401
from . import ClipSlot  # noqa: F401
from . import Scene  # noqa: F401
from . import CuePoint  # noqa: F401
from . import Track  # noqa: F401
from . import Song  # noqa: F401
from . import Browser  # noqa: F401
from . import Application  # noqa: F401
