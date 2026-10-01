"""Live.DeviceParameter."""
from ._core import LomObject, make_enum, check_number

AutomationState = make_enum("Live.DeviceParameter.AutomationState", ("none", "playing", "overridden"))
ParameterState = make_enum("Live.DeviceParameter.ParameterState", ("enabled", "irrelevant", "disabled"))


class DeviceParameter(LomObject):

    def __init__(self, name, value=0.0, min_value=0.0, max_value=1.0, default=None, is_quantized=False,
                 value_items=None, display=None, original_name=None, is_enabled=True):
        self._name = name
        self._original_name = original_name if original_name is not None else name
        self._min = float(min_value)
        self._max = float(max_value)
        self._quantized = bool(is_quantized)
        if self._quantized and value_items is None:
            value_items = [str(i) for i in range(int(self._min), int(self._max) + 1)]
        self._items = list(value_items) if value_items is not None else None
        self._display = display
        self._default = float(default) if default is not None else float(value)
        self._value = float(value)
        self._enabled = bool(is_enabled)
        self._automation_state = AutomationState.none
        self._state = ParameterState.enabled
        self.gesture_depth = 0

    # ---- identity ----
    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        self._name = str(value)

    @property
    def original_name(self):
        return self._original_name

    # ---- value ----
    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, new_value):
        new_value = check_number(new_value, "value")
        if self._quantized:
            new_value = float(round(new_value))
        if new_value < self._min or new_value > self._max:
            raise RuntimeError("Invalid value %r for parameter '%s' (range %s..%s)" % (
                new_value, self._name, self._min, self._max))
        self._value = new_value

    @property
    def min(self):
        return self._min

    @property
    def max(self):
        return self._max

    @property
    def default_value(self):
        if self._quantized:
            raise RuntimeError("default_value is only available for non-quantized parameters")
        return self._default

    @property
    def is_quantized(self):
        return self._quantized

    @property
    def value_items(self):
        if not self._quantized:
            raise RuntimeError("value_items is only available for quantized parameters")
        return tuple(self._items)

    @property
    def is_enabled(self):
        return self._enabled

    @property
    def state(self):
        return self._state

    @property
    def automation_state(self):
        return self._automation_state

    def str_for_value(self, value):
        value = check_number(value, "value")
        if self._quantized:
            index = int(round(value)) - int(self._min)
            if 0 <= index < len(self._items):
                return self._items[index]
            return str(int(round(value)))
        if self._display is not None:
            return self._display(value)
        return "%.2f" % value

    def __str__(self):
        return self.str_for_value(self._value)

    def re_enable_automation(self):
        self._automation_state = AutomationState.none

    def begin_gesture(self):
        self.gesture_depth += 1

    def end_gesture(self):
        self.gesture_depth = max(0, self.gesture_depth - 1)

    # Listener API (no-ops in the mock)
    def add_value_listener(self, callback):
        pass

    def remove_value_listener(self, callback):
        pass

    def value_has_listener(self, callback):
        return False
