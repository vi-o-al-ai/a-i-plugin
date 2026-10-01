"""Live.Track."""
from ._core import LomObject, make_enum, color_for_index, nearest_color_index, check_color_index, check_number
from .ClipSlot import ClipSlot
from .MixerDevice import MixerDevice

DeviceInsertMode = make_enum("Live.Track.DeviceInsertMode", ("default", "selected_left", "selected_right"))

_next_color = [0]


class RoutingType(LomObject):
    def __init__(self, display_name):
        self.display_name = display_name


class Track(LomObject):
    """kind: 'midi' | 'audio' | 'group' | 'return' | 'master'."""

    class View(LomObject):
        def __init__(self, track):
            self._track = track
            self._selected_device = None
            self.device_insert_mode = DeviceInsertMode.default
            self.is_collapsed = False

        @property
        def selected_device(self):
            return self._selected_device

        @selected_device.setter
        def selected_device(self, device):
            if device is not None and not self._track._contains_device(device):
                raise RuntimeError("Device does not belong to this track")
            self._selected_device = device

        def select_instrument(self):
            for device in self._track._devices:
                if int(device.type) == 1:
                    self._selected_device = device
                    return True
            return False

    def __init__(self, song, name, kind="midi"):
        self._song = song
        self._name = name
        self._kind = kind
        self._color_index = _next_color[0] % 70
        _next_color[0] += 1
        self._mute = False
        self._solo = False
        self._arm = False
        self._clip_slots = []
        self._devices = []
        self._arrangement_clips = []
        self._group_track = None
        self._fold_state = 0
        self._playing_slot_index = -1
        self._fired_slot_index = -1
        self.mixer_device = MixerDevice(kind)
        self.view = Track.View(self)
        self.implicit_arm = False
        self.current_monitoring_state = 1
        self.input_routing_type = RoutingType("All Ins")
        self.output_routing_type = RoutingType("Master")

    # ---- identity ----
    @property
    def name(self):
        return self._name

    @name.setter
    def name(self, value):
        self._name = str(value)

    @property
    def color(self):
        return color_for_index(self._color_index)

    @color.setter
    def color(self, value):
        self._color_index = nearest_color_index(value)

    @property
    def color_index(self):
        return self._color_index

    @color_index.setter
    def color_index(self, value):
        self._color_index = check_color_index(value)

    @property
    def has_midi_input(self):
        return self._kind == "midi"

    @property
    def has_audio_input(self):
        return self._kind == "audio"

    @property
    def has_audio_output(self):
        return True

    @property
    def has_midi_output(self):
        return False

    @property
    def is_foldable(self):
        return self._kind == "group"

    @property
    def is_grouped(self):
        return self._group_track is not None

    @property
    def group_track(self):
        return self._group_track

    @property
    def fold_state(self):
        if self._kind != "group":
            raise RuntimeError("fold_state is only available on group tracks")
        return self._fold_state

    @fold_state.setter
    def fold_state(self, value):
        if self._kind != "group":
            raise RuntimeError("fold_state is only available on group tracks")
        self._fold_state = 1 if value else 0

    @property
    def is_visible(self):
        return True

    @property
    def is_frozen(self):
        return False

    @property
    def can_be_frozen(self):
        return self._kind in ("midi", "audio")

    # ---- mix state ----
    @property
    def mute(self):
        return self._mute

    @mute.setter
    def mute(self, value):
        self._mute = bool(value)

    @property
    def solo(self):
        return self._solo

    @solo.setter
    def solo(self, value):
        self._solo = bool(value)

    @property
    def arm(self):
        if self._kind in ("return", "master"):
            raise RuntimeError("Master and Return Tracks have no 'Arm' state!")
        return self._arm

    @arm.setter
    def arm(self, value):
        if not self.can_be_armed:
            raise RuntimeError("This track cannot be armed")
        self._arm = bool(value)

    @property
    def can_be_armed(self):
        return self._kind in ("midi", "audio")

    # ---- session ----
    @property
    def playing_slot_index(self):
        return self._playing_slot_index

    @property
    def fired_slot_index(self):
        return self._fired_slot_index

    @property
    def clip_slots(self):
        return tuple(self._clip_slots)

    @property
    def devices(self):
        return tuple(self._devices)

    @property
    def arrangement_clips(self):
        if self._kind not in ("midi", "audio"):
            return ()
        return tuple(self._arrangement_clips)

    def duplicate_clip_to_arrangement(self, clip, destination_time):
        destination_time = check_number(destination_time, "destination_time")
        if self._kind not in ("midi", "audio"):
            raise RuntimeError("This track cannot hold arrangement clips")
        if clip.is_midi_clip != (self._kind == "midi"):
            raise RuntimeError("Clip type and track type are incompatible")
        new_clip = clip._copy(track=self, slot=None, is_arrangement=True, start_time=destination_time)
        self._arrangement_clips.append(new_clip)
        self._arrangement_clips.sort(key=lambda c: c._start_time)
        return new_clip

    def delete_clip(self, clip):
        if clip in self._arrangement_clips:
            self._arrangement_clips.remove(clip)
            return
        for slot in self._clip_slots:
            if slot._clip is clip:
                slot.delete_clip()
                return
        raise RuntimeError("The clip belongs to another track")

    def duplicate_clip_slot(self, index):
        source = self._clip_slots[index]
        if source._clip is None:
            raise RuntimeError("Slot is empty")
        if index + 1 >= len(self._clip_slots):
            self._song.create_scene(-1)
        target = self._clip_slots[index + 1]
        target._clip = source._clip._copy(self, target)
        return index + 1

    def delete_device(self, index):
        if isinstance(index, bool) or not isinstance(index, int) or index < 0 or index >= len(self._devices):
            raise RuntimeError("Invalid device index %r" % (index,))
        device = self._devices.pop(index)
        device._track = None
        if self.view._selected_device is device:
            self.view._selected_device = self._devices[min(index, len(self._devices) - 1)] if self._devices else None

    def insert_device(self, device_name, target_index=None):
        raise RuntimeError("Track.insert_device is not available in this Live")

    def stop_all_clips(self, Quantized=True):
        for slot in self._clip_slots:
            if slot._clip is not None:
                slot._clip._is_playing = False
        self._playing_slot_index = -1
        self._fired_slot_index = -1

    def jump_in_running_session_clip(self, beats):
        pass

    # ---- mock internals ----
    def _fire_slot(self, slot):
        index = self._clip_slots.index(slot)
        for other in self._clip_slots:
            if other._clip is not None:
                other._clip._is_playing = False
        if slot._clip is not None:
            slot._clip._is_playing = True
            self._playing_slot_index = index
        else:
            self._playing_slot_index = -1
        self._fired_slot_index = -1

    def _stop_slot(self, slot):
        if slot._clip is not None:
            slot._clip._is_playing = False
        if self._playing_slot_index == self._clip_slots.index(slot):
            self._playing_slot_index = -1

    def _insert_device(self, device, index=None):
        device._set_track(self)
        if index is None or index < 0 or index > len(self._devices):
            self._devices.append(device)
        else:
            self._devices.insert(index, device)
        self.view._selected_device = device

    def _contains_device(self, device, devices=None):
        devices = self._devices if devices is None else devices
        for candidate in devices:
            if candidate is device:
                return True
            if candidate.can_have_chains:
                for chain in candidate._chains:
                    if self._contains_device(device, chain._devices):
                        return True
        return False

    def __repr__(self):
        d = object.__getattribute__(self, "__dict__")
        return "<Track %r %s>" % (d["_name"], d["_kind"])
