"""Mock of _Framework.ControlSurface.ControlSurface.

Models the pieces ClaudeLive relies on: song()/application() as *methods*,
log_message(), show_message(), schedule_message() with the exact off-by-one and
falsy-parameter behaviour of the shipped framework, and a harness `tick()` that
plays the role of update_display() (one tick ~ 100 ms in Live).
"""
import Live


class ControlSurface(object):

    def __init__(self, c_instance):
        self._c_instance = c_instance
        self._scheduled = []  # [remaining_ticks, callback, parameter]
        self._pending = []
        self._is_sending_scheduled_messages = False
        self.log_messages = []
        self.shown_messages = []
        self.disconnected = False
        self.ticks = 0

    # ---- what Live gives a control surface ----
    def song(self):
        return self._c_instance.song()

    def application(self):
        return Live.Application.get_application()

    def log_message(self, *message):
        text = "(%s) %s" % (self.__class__.__name__, " ".join(map(str, message)))
        self.log_messages.append(text)
        self._c_instance.log_message(text)

    def show_message(self, message):
        self.shown_messages.append(message)
        self._c_instance.show_message(message)

    def schedule_message(self, delay_in_ticks, callback, parameter=None):
        """Same semantics as the shipped framework (asserts stripped in Live 11/12)."""
        assert callable(callback)
        if not self._is_sending_scheduled_messages:
            delay_in_ticks -= 1
        entry = [delay_in_ticks, callback, parameter]
        if self._is_sending_scheduled_messages:
            self._pending.append(entry)
        else:
            self._scheduled.append(entry)

    def disconnect(self):
        self.disconnected = True
        self._scheduled = []
        self._pending = []

    def refresh_state(self):
        pass

    def connect_script_instances(self, instanciated_scripts):
        pass

    def build_midi_map(self, midi_map_handle):
        pass

    def receive_midi(self, midi_bytes):
        pass

    def can_lock_to_devices(self):
        return False

    def suggest_input_port(self):
        return ""

    def suggest_output_port(self):
        return ""

    # ---- harness ----
    def tick(self):
        """One update_display(): decrement delays, run everything that is due.

        Callbacks scheduled *during* the tick are queued for later ticks (as the
        real TaskGroup does), and a falsy `parameter` is dropped - `callback()`
        is called without arguments.
        """
        self.ticks += 1
        self._is_sending_scheduled_messages = True
        try:
            due = []
            remaining = []
            for entry in self._scheduled:
                entry[0] -= 1
                if entry[0] <= 0:
                    due.append(entry)
                else:
                    remaining.append(entry)
            self._scheduled = remaining
            for _delay, callback, parameter in due:
                if parameter:
                    callback(parameter)
                else:
                    callback()
        finally:
            self._is_sending_scheduled_messages = False
            self._scheduled.extend(self._pending)
            self._pending = []

    update_display = tick

    @property
    def scheduled_count(self):
        return len(self._scheduled) + len(self._pending)
