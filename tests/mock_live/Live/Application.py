"""Live.Application, Live.Application.View and get_application()."""
from ._core import LomObject, make_enum

_application = None

VIEW_NAMES = ("Session", "Arranger", "Detail", "Detail/Clip", "Detail/DeviceChain", "Browser")


class Application(LomObject):

    class View(LomObject):
        NavDirection = make_enum("Live.Application.Application.View.NavDirection", ("up", "down", "left", "right"))

        def __init__(self):
            self._visible = set(["Session", "Detail", "Detail/DeviceChain", "Browser"])
            self.shown = []
            self.focused = []
            self.focused_document_view = "Session"
            self.browse_mode = False

        def show_view(self, name):
            if name not in VIEW_NAMES:
                raise RuntimeError("Unknown view name %r" % (name,))
            self.shown.append(name)
            self._visible.add(name)
            if name in ("Session", "Arranger"):
                self._visible.discard("Arranger" if name == "Session" else "Session")
                self.focused_document_view = name
            if name == "Detail/Clip":
                self._visible.discard("Detail/DeviceChain")
                self._visible.add("Detail")
            if name == "Detail/DeviceChain":
                self._visible.discard("Detail/Clip")
                self._visible.add("Detail")

        def hide_view(self, name):
            if name not in VIEW_NAMES:
                raise RuntimeError("Unknown view name %r" % (name,))
            self._visible.discard(name)

        def focus_view(self, name):
            self.show_view(name)
            self.focused.append(name)

        def is_view_visible(self, name, main_window_only=True):
            if name not in VIEW_NAMES:
                raise RuntimeError("Unknown view name %r" % (name,))
            return name in self._visible

        def available_main_views(self):
            return list(VIEW_NAMES)

        def scroll_view(self, direction, name, modifier_pressed):
            pass

        def zoom_view(self, direction, name, modifier_pressed):
            pass

        def toggle_browse(self):
            self.browse_mode = not self.browse_mode

    def __init__(self, song, browser, version=(12, 1, 5)):
        self._song = song
        self._browser = browser
        self._version = tuple(version)
        self.view = Application.View()
        self.control_surfaces = ()
        self.open_dialog_count = 0
        self.current_dialog_message = ""
        self.average_process_usage = 0.1

    def get_major_version(self):
        return self._version[0]

    def get_minor_version(self):
        return self._version[1]

    def get_bugfix_version(self):
        return self._version[2]

    def get_version_string(self):
        return "%d.%d.%d" % self._version

    def get_document(self):
        return self._song

    @property
    def browser(self):
        return self._browser

    def has_option(self, name):
        return False

    def press_current_dialog_button(self, index):
        pass


def get_application():
    if _application is None:
        raise RuntimeError("No Live application has been installed in the mock (call _set_application)")
    return _application


def _set_application(app):
    """Harness helper (not part of the real API)."""
    global _application
    _application = app
