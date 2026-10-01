"""Live.Song and Live.Song.View."""
from ._core import LomObject, check_number
from .Base import LimitationError
from .ClipSlot import ClipSlot
from .CuePoint import CuePoint
from .Scene import Scene
from .Track import Track

SCALES = {
    "Major": [0, 2, 4, 5, 7, 9, 11],
    "Minor": [0, 2, 3, 5, 7, 8, 10],
    "Dorian": [0, 2, 3, 5, 7, 9, 10],
    "Mixolydian": [0, 2, 4, 5, 7, 9, 10],
    "Lydian": [0, 2, 4, 6, 7, 9, 11],
    "Phrygian": [0, 1, 3, 5, 7, 8, 10],
    "Locrian": [0, 1, 3, 5, 6, 8, 10],
    "Whole Tone": [0, 2, 4, 6, 8, 10],
    "Half-whole Dim.": [0, 1, 3, 4, 6, 7, 9, 10],
    "Whole-half Dim.": [0, 2, 3, 5, 6, 8, 9, 11],
    "Minor Blues": [0, 3, 5, 6, 7, 10],
    "Minor Pentatonic": [0, 3, 5, 7, 10],
    "Major Pentatonic": [0, 2, 4, 7, 9],
    "Harmonic Minor": [0, 2, 3, 5, 7, 8, 11],
    "Harmonic Major": [0, 2, 4, 5, 7, 8, 11],
    "Dorian #4": [0, 2, 3, 6, 7, 9, 10],
    "Phrygian Dominant": [0, 1, 4, 5, 7, 8, 10],
    "Melodic Minor": [0, 2, 3, 5, 7, 9, 11],
    "Lydian Augmented": [0, 2, 4, 6, 8, 9, 11],
    "Lydian Dominant": [0, 2, 4, 6, 7, 9, 10],
    "Super Locrian": [0, 1, 3, 4, 6, 8, 10],
    "Bhairav": [0, 1, 4, 5, 7, 8, 11],
    "Hungarian Minor": [0, 2, 3, 6, 7, 8, 11],
    "8-Tone Spanish": [0, 1, 3, 4, 5, 6, 8, 10],
    "Hirajoshi": [0, 2, 3, 7, 8],
    "In-Sen": [0, 1, 5, 7, 10],
    "Iwato": [0, 1, 5, 6, 10],
    "Kumoi": [0, 2, 3, 7, 9],
    "Pelog Selisir": [0, 1, 3, 7, 8],
    "Pelog Tembung": [0, 1, 5, 7, 8],
    "Messaien 3": [0, 2, 3, 4, 6, 7, 8, 10, 11],
    "Messaien 4": [0, 1, 2, 5, 6, 7, 8, 11],
    "Messaien 5": [0, 1, 5, 6, 7, 11],
    "Messaien 6": [0, 2, 4, 5, 6, 8, 10, 11],
    "Messaien 7": [0, 1, 2, 3, 5, 6, 7, 8, 9, 11],
}

MAX_TRACKS = 1000
MAX_SCENES = 1000
MAX_RETURNS = 12
RETURN_LETTERS = "ABCDEFGHIJKL"


class Song(LomObject):

    class View(LomObject):
        def __init__(self, song):
            self._song = song
            self._selected_track = None
            self._selected_scene = None
            self._highlighted_clip_slot = None
            self.detail_clip = None
            self.selected_parameter = None
            self.selected_chain = None
            self.draw_mode = False
            self.follow_song = False
            self._appointed_device = None

        @property
        def selected_track(self):
            return self._selected_track

        @selected_track.setter
        def selected_track(self, track):
            if track not in self._song._all_tracks():
                raise RuntimeError("Track does not belong to this Live Set")
            self._selected_track = track
            self._refresh_highlight()

        @property
        def selected_scene(self):
            return self._selected_scene

        @selected_scene.setter
        def selected_scene(self, scene):
            if scene not in self._song._scenes:
                raise RuntimeError("Scene does not belong to this Live Set")
            self._selected_scene = scene
            self._refresh_highlight()

        @property
        def highlighted_clip_slot(self):
            return self._highlighted_clip_slot

        @highlighted_clip_slot.setter
        def highlighted_clip_slot(self, slot):
            if slot is None:
                self._highlighted_clip_slot = None
                return
            for track in self._song._tracks:
                if slot in track._clip_slots:
                    index = track._clip_slots.index(slot)
                    self._selected_track = track
                    if index < len(self._song._scenes):
                        self._selected_scene = self._song._scenes[index]
                    self._highlighted_clip_slot = slot
                    return
            raise RuntimeError("Clip slot does not belong to this Live Set")

        @property
        def appointed_device(self):
            return self._appointed_device

        def select_device(self, device, ShouldAppointDevice=True):
            track = device._track
            if track is None:
                raise RuntimeError("Device is not in this Live Set")
            self.selected_track = track
            track.view.selected_device = device
            if ShouldAppointDevice:
                self._appointed_device = device

        def _refresh_highlight(self):
            track = self._selected_track
            scene = self._selected_scene
            if track is None or scene is None or not track._clip_slots:
                self._highlighted_clip_slot = None
                return
            index = self._song._scenes.index(scene)
            self._highlighted_clip_slot = track._clip_slots[index] if index < len(track._clip_slots) else None

    def __init__(self):
        self._tempo = 120.0
        self._signature_numerator = 4
        self._signature_denominator = 4
        self._is_playing = False
        self._current_song_time = 0.0
        self.metronome = False
        self.loop = False
        self._loop_start = 0.0
        self._loop_length = 16.0
        self.record_mode = False
        self.session_record = False
        self.session_automation_record = False
        self.arrangement_overdub = False
        self.back_to_arranger = False
        self.clip_trigger_quantization = 4
        self.midi_recording_quantization = 0
        self.swing_amount = 0.0
        self.nudge_down = False
        self.nudge_up = False
        self._tracks = []
        self._return_tracks = []
        self._master_track = Track(self, "Master", "master")
        self._scenes = []
        self._cue_points = []
        self.undo_count = 0
        self.redo_count = 0
        self.view = Song.View(self)
        # Scale awareness (Live 11+/12). Plain attributes so tests can `del` them.
        LomObject.__setattr__(self, "scale_intervals", list(SCALES["Major"]))
        self.root_note = 0
        self.scale_name = "Major"
        self.scale_mode = False

    def __setattr__(self, name, value):
        if name == "scale_name":
            if value not in SCALES:
                raise RuntimeError("Unknown scale name %r" % (value,))
            LomObject.__setattr__(self, name, value)
            LomObject.__setattr__(self, "scale_intervals", list(SCALES[value]))
            return
        if name == "root_note":
            if isinstance(value, bool) or not isinstance(value, int) or not 0 <= value <= 11:
                raise RuntimeError("root_note must be 0-11")
        LomObject.__setattr__(self, name, value)

    # ---- transport ----
    @property
    def tempo(self):
        return self._tempo

    @tempo.setter
    def tempo(self, value):
        value = check_number(value, "tempo")
        if value < 20.0 or value > 999.0:
            raise RuntimeError("Tempo %s is out of range 20..999" % value)
        self._tempo = value

    @property
    def signature_numerator(self):
        return self._signature_numerator

    @signature_numerator.setter
    def signature_numerator(self, value):
        if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= 99:
            raise RuntimeError("signature_numerator must be 1..99")
        self._signature_numerator = value

    @property
    def signature_denominator(self):
        return self._signature_denominator

    @signature_denominator.setter
    def signature_denominator(self, value):
        if value not in (1, 2, 4, 8, 16):
            raise RuntimeError("signature_denominator must be 1, 2, 4, 8 or 16")
        self._signature_denominator = value

    @property
    def is_playing(self):
        return self._is_playing

    def start_playing(self):
        self._is_playing = True

    def stop_playing(self):
        self._is_playing = False

    def continue_playing(self):
        self._is_playing = True

    def play_selection(self):
        self._is_playing = True

    @property
    def current_song_time(self):
        return self._current_song_time

    @current_song_time.setter
    def current_song_time(self, value):
        value = check_number(value, "current_song_time")
        if value < 0:
            raise RuntimeError("current_song_time must be >= 0")
        self._current_song_time = value

    @property
    def loop_start(self):
        return self._loop_start

    @loop_start.setter
    def loop_start(self, value):
        value = check_number(value, "loop_start")
        if value < 0:
            raise RuntimeError("loop_start must be >= 0")
        self._loop_start = value

    @property
    def loop_length(self):
        return self._loop_length

    @loop_length.setter
    def loop_length(self, value):
        value = check_number(value, "loop_length")
        if value <= 0:
            raise RuntimeError("loop_length must be > 0")
        self._loop_length = value

    @property
    def song_length(self):
        end = 0.0
        for track in self._tracks:
            for clip in track._arrangement_clips:
                end = max(end, clip.end_time)
        return end

    @property
    def last_event_time(self):
        return self.song_length

    @property
    def session_record_status(self):
        return 0

    def jump_by(self, beats):
        self.current_song_time = max(0.0, self._current_song_time + float(beats))

    def scrub_by(self, beats):
        self.jump_by(beats)

    def tap_tempo(self):
        pass

    def re_enable_automation(self):
        pass

    # ---- undo ----
    @property
    def can_undo(self):
        return True

    @property
    def can_redo(self):
        return self.undo_count > self.redo_count

    def undo(self):
        self.undo_count += 1

    def redo(self):
        self.redo_count += 1

    def begin_undo_step(self):
        pass

    def end_undo_step(self):
        pass

    # ---- collections ----
    @property
    def tracks(self):
        return tuple(self._tracks)

    @property
    def visible_tracks(self):
        return tuple(self._tracks)

    @property
    def return_tracks(self):
        return tuple(self._return_tracks)

    @property
    def master_track(self):
        return self._master_track

    @property
    def scenes(self):
        return tuple(self._scenes)

    @property
    def cue_points(self):
        return tuple(self._cue_points)

    # ---- tracks ----
    def _check_track_index(self, index, allow_end):
        if isinstance(index, bool) or not isinstance(index, int):
            raise TypeError("index must be an int")
        limit = len(self._tracks) + (1 if allow_end else 0)
        if index != -1 and not 0 <= index < limit:
            raise RuntimeError("Invalid track index %d" % index)

    def create_midi_track(self, index=-1):
        self._check_track_index(index, True)
        if len(self._tracks) >= MAX_TRACKS:
            raise LimitationError("Maximum number of tracks reached")
        track = Track(self, "%d-MIDI" % (len(self._tracks) + 1), "midi")
        self._add_track(track, None if index == -1 else index)
        self.view.selected_track = track
        return track

    def create_audio_track(self, index=-1):
        self._check_track_index(index, True)
        if len(self._tracks) >= MAX_TRACKS:
            raise LimitationError("Maximum number of tracks reached")
        track = Track(self, "%d-Audio" % (len(self._tracks) + 1), "audio")
        self._add_track(track, None if index == -1 else index)
        self.view.selected_track = track
        return track

    def create_return_track(self):
        if len(self._return_tracks) >= MAX_RETURNS:
            raise RuntimeError("Maximum number of return tracks reached")
        letter = RETURN_LETTERS[len(self._return_tracks)]
        track = Track(self, "%s Return" % letter, "return")
        self._return_tracks.append(track)
        # Every player/return track gains a send to the new return; the new return
        # itself gets one send per return (Live shows its own, disabled).
        for other in self._tracks + self._return_tracks:
            if other is track:
                for _ in self._return_tracks:
                    track.mixer_device._add_send()
            else:
                other.mixer_device._add_send()
        self.view.selected_track = track
        return track

    def delete_track(self, index):
        self._check_track_index(index, False)
        if index == -1:
            raise RuntimeError("Invalid track index -1")
        track = self._tracks.pop(index)
        for other in self._tracks:
            if other._group_track is track:
                other._group_track = None
        if self.view._selected_track is track:
            fallback = self._tracks[min(index, len(self._tracks) - 1)] if self._tracks else self._master_track
            self.view.selected_track = fallback

    def delete_return_track(self, index):
        if isinstance(index, bool) or not isinstance(index, int) or not 0 <= index < len(self._return_tracks):
            raise RuntimeError("Invalid return track index %r" % (index,))
        track = self._return_tracks.pop(index)
        for other in self._tracks + self._return_tracks:
            other.mixer_device._remove_send(index)
        if self.view._selected_track is track:
            self.view.selected_track = self._master_track

    def duplicate_track(self, index):
        self._check_track_index(index, False)
        source = self._tracks[index]
        copy = Track(self, source._name, source._kind)
        self._add_track(copy, index + 1)
        for s_slot, c_slot in zip(source._clip_slots, copy._clip_slots):
            if s_slot._clip is not None:
                c_slot._clip = s_slot._clip._copy(copy, c_slot)
        self.view.selected_track = copy
        return copy

    # ---- scenes ----
    def create_scene(self, index=-1):
        if isinstance(index, bool) or not isinstance(index, int):
            raise TypeError("index must be an int")
        if index != -1 and not 0 <= index <= len(self._scenes):
            raise RuntimeError("Invalid scene index %d" % index)
        if len(self._scenes) >= MAX_SCENES:
            raise LimitationError("Maximum number of scenes reached")
        scene = Scene(self, "")
        self._add_scene(scene, None if index == -1 else index)
        self.view.selected_scene = scene
        return scene

    def delete_scene(self, index):
        if isinstance(index, bool) or not isinstance(index, int) or not 0 <= index < len(self._scenes):
            raise RuntimeError("Invalid scene index %r" % (index,))
        if len(self._scenes) == 1:
            raise RuntimeError("Cannot delete the last scene")
        scene = self._scenes.pop(index)
        for track in self._tracks:
            if index < len(track._clip_slots):
                track._clip_slots.pop(index)
        if self.view._selected_scene is scene:
            self.view.selected_scene = self._scenes[min(index, len(self._scenes) - 1)]
        else:
            self.view._refresh_highlight()

    def duplicate_scene(self, index):
        if isinstance(index, bool) or not isinstance(index, int) or not 0 <= index < len(self._scenes):
            raise RuntimeError("Invalid scene index %r" % (index,))
        source = self._scenes[index]
        scene = Scene(self, source._name)
        scene._color_index = source._color_index
        scene._tempo = source._tempo
        scene._tempo_enabled = source._tempo_enabled
        self._add_scene(scene, index + 1)
        for track in self._tracks:
            src_slot = track._clip_slots[index]
            if src_slot._clip is not None:
                dst_slot = track._clip_slots[index + 1]
                dst_slot._clip = src_slot._clip._copy(track, dst_slot)
        self.view.selected_scene = scene
        return scene

    def capture_and_insert_scene(self):
        return self.create_scene(-1)

    def stop_all_clips(self, Quantized=True):
        for track in self._tracks:
            track.stop_all_clips(Quantized)

    def trigger_session_record(self, record_length=None):
        self.session_record = True

    # ---- cue points ----
    def _cue_at_current_time(self):
        for cue in self._cue_points:
            if abs(cue._time - self._current_song_time) < 1e-6:
                return cue
        return None

    def set_or_delete_cue(self):
        existing = self._cue_at_current_time()
        if existing is not None:
            self._cue_points.remove(existing)
            return
        cue = CuePoint(self, self._current_song_time, "%d" % (int(self._current_song_time / 4.0) + 1))
        self._cue_points.append(cue)
        self._cue_points.sort(key=lambda c: c._time)

    def is_cue_point_selected(self):
        return self._cue_at_current_time() is not None

    @property
    def can_jump_to_next_cue(self):
        return any(c._time > self._current_song_time for c in self._cue_points)

    @property
    def can_jump_to_prev_cue(self):
        return any(c._time < self._current_song_time for c in self._cue_points)

    def jump_to_next_cue(self):
        for cue in self._cue_points:
            if cue._time > self._current_song_time:
                self._current_song_time = cue._time
                return

    def jump_to_prev_cue(self):
        for cue in reversed(self._cue_points):
            if cue._time < self._current_song_time:
                self._current_song_time = cue._time
                return

    # ---- mock internals ----
    def _add_track(self, track, index=None):
        track._clip_slots = [ClipSlot(track) for _ in self._scenes]
        for _ in self._return_tracks:
            track.mixer_device._add_send()
        if index is None or index < 0 or index > len(self._tracks):
            self._tracks.append(track)
        else:
            self._tracks.insert(index, track)
        if self.view._selected_track is None:
            self.view.selected_track = track
        return track

    def _add_scene(self, scene, index=None):
        if index is None or index < 0 or index > len(self._scenes):
            index = len(self._scenes)
        self._scenes.insert(index, scene)
        for track in self._tracks:
            track._clip_slots.insert(index, ClipSlot(track))
        if self.view._selected_scene is None:
            self.view.selected_scene = scene
        return scene

    def _all_tracks(self):
        return self._tracks + self._return_tracks + [self._master_track]
