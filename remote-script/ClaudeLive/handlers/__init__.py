"""Handler registry: METHODS maps "namespace.name" -> callable(ctx, params).

Every handler runs on Live's main thread (called from the tick) and returns a
JSON-serialisable dict, or raises errors.LiveRpcError.
"""
import importlib
import platform
import sys

import Live

from .. import lom

SCRIPT_VERSION = "0.1.0"
PROTOCOL_VERSION = 1


class Context(object):
    """What handlers get as their first argument."""

    def __init__(self, control_surface, config, logger):
        self.control_surface = control_surface
        self.config = config or {}
        self.logger = logger
        self.state = {}  # per-instance caches (browser index, ...)
        self._version = None
        self.script_version = SCRIPT_VERSION
        self.protocol_version = PROTOCOL_VERSION

    def song(self):
        return self.control_surface.song()

    def application(self):
        app = None
        getter = getattr(self.control_surface, "application", None)
        if getter is not None:
            try:
                app = getter()
            except AssertionError:
                raise
            except Exception:
                app = None
        if app is None:
            app = Live.Application.get_application()
        return app

    @property
    def version(self):
        """{"major", "minor", "bugfix", "string"} of the running Live (cached)."""
        if self._version is None:
            self._version = lom.live_version(self.application())
        return self._version

    @property
    def tick_count(self):
        return getattr(self.control_surface, "tick_count", 0)

    @property
    def python_version(self):
        return platform.python_version()

    def log_to_live(self, message):
        log = getattr(self.control_surface, "log_message", None)
        if log is not None:
            log(message)


# Handler modules, imported after Context so a reload can rebuild them in order.
from . import system, song, view, track, scene, clip, notes, device, browser, arrangement, automation  # noqa: E402

MODULES = [system, song, view, track, scene, clip, notes, device, browser, arrangement, automation]
METHODS = {}


def build_methods():
    """(Re)populate METHODS in place so holders of the dict see the change."""
    METHODS.clear()
    for module in MODULES:
        METHODS.update(getattr(module, "METHODS", {}))
    return METHODS


def reload_handlers():
    """Dev convenience: importlib.reload the lom/introspect modules and every handler
    module, then rebuild METHODS. ClaudeLive.py, server.py and dispatcher.py are
    NOT reloaded (they hold live sockets/state); changing them needs a Live restart."""
    package = sys.modules[__name__.rsplit(".", 1)[0]]
    reloaded = []
    for name in ("lom", "introspect"):
        module = getattr(package, name, None)
        if module is None:
            module = importlib.import_module("%s.%s" % (package.__name__, name))
        importlib.reload(module)
        reloaded.append(module.__name__)
    for i, module in enumerate(MODULES):
        MODULES[i] = importlib.reload(module)
        reloaded.append(module.__name__)
    build_methods()
    return reloaded


build_methods()
