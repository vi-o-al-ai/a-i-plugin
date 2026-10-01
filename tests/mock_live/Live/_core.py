"""Shared machinery for the mock Live module: the main-thread guard, boost-style
enums and the colour palette. Not part of the real API (hence the underscore)."""
import colorsys
import threading

MAIN_THREAD = None
VIOLATIONS = []


def set_main_thread(thread=None):
    """The harness designates the thread allowed to touch LOM objects."""
    global MAIN_THREAD
    MAIN_THREAD = thread if thread is not None else threading.current_thread()


def clear_main_thread():
    global MAIN_THREAD
    MAIN_THREAD = None


def check_thread(name):
    if MAIN_THREAD is None:
        return
    current = threading.current_thread()
    if current is not MAIN_THREAD:
        VIOLATIONS.append((name, current.name))
        raise AssertionError("LOM accessed off main thread (attribute %r from thread %r)" % (name, current.name))


class LomObject(object):
    """Base for every mock LOM object: any non-dunder attribute access or write off
    the designated main thread raises AssertionError."""

    def __getattribute__(self, name):
        if not name.startswith("__"):
            check_thread(name)
        return object.__getattribute__(self, name)

    def __setattr__(self, name, value):
        check_thread(name)
        object.__setattr__(self, name, value)

    def __delattr__(self, name):
        check_thread(name)
        object.__delattr__(self, name)


class EnumValue(int):
    """An int that remembers its enum name, like boost.python enums."""

    def __new__(cls, value, name, owner):
        obj = int.__new__(cls, value)
        obj.name = name
        obj.owner = owner
        return obj

    def __repr__(self):
        return "%s.%s" % (self.owner, self.name)

    __str__ = __repr__


def make_enum(qualname, names):
    attrs = {}
    members = []
    for i, name in enumerate(names):
        member = EnumValue(i, name, qualname)
        attrs[name] = member
        members.append(member)
    attrs["values"] = dict((int(m), m) for m in members)
    attrs["names"] = dict((m.name, m) for m in members)
    return type(qualname.rsplit(".", 1)[-1], (object,), attrs)


def _build_palette():
    palette = []
    saturations = (0.9, 0.7, 0.5, 0.8, 0.3)
    values = (1.0, 0.85, 0.7, 0.55, 0.45)
    for row in range(5):
        for col in range(14):
            r, g, b = colorsys.hsv_to_rgb(col / 14.0, saturations[row], values[row])
            palette.append((int(round(r * 255)) << 16) | (int(round(g * 255)) << 8) | int(round(b * 255)))
    return tuple(palette)


PALETTE = _build_palette()  # 70 entries, index 0-69


def color_for_index(index):
    if index is None:
        return None
    return PALETTE[int(index) % len(PALETTE)]


def nearest_color_index(color):
    color = int(color) & 0xFFFFFF
    r, g, b = (color >> 16) & 0xFF, (color >> 8) & 0xFF, color & 0xFF
    best, best_distance = 0, None
    for i, candidate in enumerate(PALETTE):
        cr, cg, cb = (candidate >> 16) & 0xFF, (candidate >> 8) & 0xFF, candidate & 0xFF
        distance = (r - cr) ** 2 + (g - cg) ** 2 + (b - cb) ** 2
        if best_distance is None or distance < best_distance:
            best, best_distance = i, distance
    return best


def check_color_index(value):
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int):
        raise RuntimeError("color_index must be an int or None")
    if value < 0 or value >= len(PALETTE):
        raise RuntimeError("color_index %d out of range 0-%d" % (value, len(PALETTE) - 1))
    return value


def check_number(value, what):
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError("%s must be a number, not %s" % (what, type(value).__name__))
    return float(value)
