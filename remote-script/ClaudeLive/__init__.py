"""ClaudeLive - Ableton Live 12 Remote Script exposing the Live Object Model over
newline-delimited JSON-RPC on 127.0.0.1 (see docs/PROTOCOL.md).

Install: copy this folder to
  macOS:   ~/Music/Ableton/User Library/Remote Scripts/ClaudeLive/
  Windows: Documents\\Ableton\\User Library\\Remote Scripts\\ClaudeLive\\
then select "ClaudeLive" in Preferences > Link, Tempo & MIDI > Control Surface.

Live imports this folder as a package and calls create_instance().
Python 3.7 (Live 12.0/12.1) and 3.11 (Live 12.3) compatible; stdlib only.
"""
from .ClaudeLive import ClaudeLive


def create_instance(c_instance):
    return ClaudeLive(c_instance)
