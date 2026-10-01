"""Live.Base: Timer and LimitationError."""
from ._core import LomObject


class LimitationError(RuntimeError):
    """Raised by Live when a set limit (tracks, scenes, ...) is exceeded."""


class Timer(LomObject):
    """A timer that will trigger a callback after a certain interval (ms)."""

    def __init__(self, callback=None, interval=100, repeat=False, start=False):
        self._callback = callback
        self.interval = int(interval)
        self.repeat = bool(repeat)
        self.running = False
        self.fired = 0
        if start:
            self.start()

    def start(self):
        self.running = True

    def stop(self):
        self.running = False

    def restart(self):
        self.running = True

    def fire(self):
        """Harness helper: simulate the interval elapsing."""
        if not self.running:
            return
        self.fired += 1
        if not self.repeat:
            self.running = False
        if self._callback is not None:
            self._callback()
