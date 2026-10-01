"""Live.Browser and Live.Browser.BrowserItem."""
from ._core import LomObject, make_enum

FilterType = make_enum("Live.Browser.FilterType", (
    "disabled", "hotswap_off", "instrument_hotswap", "audio_effect_hotswap", "midi_effect_hotswap",
    "drum_pad_hotswap", "midi_track_devices", "samples"))
Relation = make_enum("Live.Browser.Relation", ("none", "equal", "ancestor", "descendant"))

ROOT_NAMES = ("instruments", "sounds", "drums", "audio_effects", "midi_effects", "plugins", "max_for_live",
              "packs", "user_library", "current_project", "samples", "clips")


class BrowserItem(LomObject):

    def __init__(self, name, uri=None, is_loadable=False, is_folder=False, is_device=False, children=(),
                 factory=None, source="Live", raises_on_children=False):
        self._name = name
        self._uri = uri if uri is not None else "query:%s" % name.replace(" ", "%20")
        self._is_loadable = bool(is_loadable)
        self._is_folder = bool(is_folder)
        self._is_device = bool(is_device)
        self._children = list(children)
        self._factory = factory  # callable returning a Device, or None for samples/clips
        self._source = source
        self._raises_on_children = raises_on_children
        self.is_selected = False

    @property
    def name(self):
        return self._name

    @property
    def uri(self):
        return self._uri

    @property
    def is_loadable(self):
        return self._is_loadable

    @property
    def is_folder(self):
        return self._is_folder

    @property
    def is_device(self):
        return self._is_device

    @property
    def children(self):
        if self._raises_on_children:
            raise RuntimeError("children: access denied for this item")
        return tuple(self._children)

    @property
    def iter_children(self):
        return iter(self.children)

    @property
    def source(self):
        return self._source

    def __repr__(self):
        return "<BrowserItem %r>" % object.__getattribute__(self, "_name")


class Browser(LomObject):

    def __init__(self, **roots):
        for name in ROOT_NAMES:
            root = roots.get(name)
            if root is None:
                root = BrowserItem(name.replace("_", " ").title(), "query:%s" % name, is_folder=True)
            setattr(self, name, root)
        self.colors = ()
        self.user_folders = ()
        self.legacy_libraries = ()
        self.hotswap_target = None
        self.filter_type = FilterType.disabled
        self.loaded_items = []
        self.previewing = None

    def load_item(self, item):
        from .Application import get_application
        if not item.is_loadable:
            raise RuntimeError("Item '%s' is not loadable" % item.name)
        song = get_application().get_document()
        track = song.view.selected_track
        if track is None:
            raise RuntimeError("No track selected")
        self.loaded_items.append(item)
        factory = item._factory
        if factory is None:
            return  # sample or clip: nothing happens to the device chain in this mock
        device = factory()
        target = self.hotswap_target
        devices = track._devices
        if target is not None and target in devices:
            index = devices.index(target)
            track.delete_device(index)
            track._insert_device(device, index)
            return
        mode = track.view.device_insert_mode
        selected = track.view.selected_device
        if int(mode) == 2 and selected in devices:  # selected_right
            track._insert_device(device, devices.index(selected) + 1)
        elif int(mode) == 1 and selected in devices:  # selected_left
            track._insert_device(device, devices.index(selected))
        else:
            track._insert_device(device)

    def preview_item(self, item):
        self.previewing = item

    def stop_preview(self):
        self.previewing = None

    def relation_to_hotswap_target(self, item):
        return Relation.none

    def add_hotswap_target_listener(self, callback):
        pass

    def remove_hotswap_target_listener(self, callback):
        pass
