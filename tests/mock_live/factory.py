"""Builds a populated fake Live set, browser and application for the tests.

Layout (indexes are what the tests rely on):
  tracks:  0 Drums (Drum Rack w/ 4 pads, Compressor)      MIDI
           1 Bass  (Operator)                              MIDI
           2 Pad   (Arpeggiator, Chord, Instrument Rack w/ 2 chains x Wavetable, Auto Filter)  MIDI
           3 Vox   (EQ Eight, Reverb)                      audio
           4 Synths (group)
           5 Lead  (Drift; grouped under Synths)           MIDI
  returns: 0 A-Reverb (Reverb), 1 B-Delay (Delay)
  master:  Limiter
  scenes:  8, named
  clips:   Drums 0/1, Bass 0/1, Pad 0, Vox 0 (audio), Lead 2; two arrangement clips on Drums
  cue:     "Drop" at 64.0
"""
import Live  # noqa: F401  (ensures the mock package is the one on sys.path)
from Live.Application import Application
from Live.Browser import Browser, BrowserItem
from Live.Chain import Chain, DrumChain
from Live.Clip import Clip, MidiNoteSpecification
from Live.Device import Device, DeviceType
from Live.DeviceParameter import DeviceParameter
from Live.MixerDevice import fader_display
from Live.RackDevice import RackDevice
from Live.Scene import Scene
from Live.Song import Song
from Live.Track import Track

SCENE_NAMES = ("Intro", "Verse 1", "Chorus 1", "Verse 2", "Chorus 2", "Bridge", "Chorus 3", "Outro")
FILTER_TYPES = ("Lowpass", "Highpass", "Bandpass", "Notch", "Morph")


# --------------------------------------------------------------------------
# Display helpers (monotonic, roughly Live-like)
# --------------------------------------------------------------------------

def hz_display(value):
    freq = 20.0 * (1000.0 ** value)
    if freq < 1000.0:
        return "%.0f Hz" % freq
    return "%.2f kHz" % (freq / 1000.0)


def pct_display(value):
    return "%.0f %%" % (value * 100.0)


def ms_display(value):
    return "%.1f ms" % value


def st_display(value):
    return "%d st" % int(round(value))


def db_display(value):
    return "%.1f dB" % value


def threshold_display(value):
    return "%.1f dB" % (-60.0 + 60.0 * value)


def plain(fmt):
    return lambda value: fmt % value


def P(name, value, low, high, display=None, default=None, original_name=None):
    return DeviceParameter(name, value, low, high, default=default, display=display, original_name=original_name)


def Q(name, value, items, original_name=None):
    return DeviceParameter(name, value, 0, len(items) - 1, is_quantized=True, value_items=list(items),
                           original_name=original_name)


# --------------------------------------------------------------------------
# Devices
# --------------------------------------------------------------------------

def make_wavetable():
    return Device("Wavetable", "InstrumentVector", "Wavetable", DeviceType.instrument, [
        P("Osc 1 Transp", 0.0, -48.0, 48.0, st_display, 0.0),
        P("Osc 1 Pos", 0.0, 0.0, 1.0, pct_display, 0.0),
        Q("Osc 1 Wave", 0, ["Basic Shapes", "Harmonics", "Noise"]),
        P("Filter 1 Freq", 0.6, 0.0, 1.0, hz_display, 0.6),
        P("Filter 1 Res", 0.2, 0.0, 1.25, plain("%.2f"), 0.2),
        Q("Filter 1 Type", 0, FILTER_TYPES),
        P("Volume", 0.8, 0.0, 1.0, fader_display, 0.8),
        P("Unison Amount", 0.0, 0.0, 1.0, pct_display, 0.0),
        P("Sub Gain", 0.0, 0.0, 1.0, pct_display, 0.0),
    ])


def make_operator():
    # Two parameters share the display name "Attack" (distinct original names) so
    # the tests can exercise the `ambiguous` flag and the original_name fallback.
    return Device("Operator", "Operator", "Operator", DeviceType.instrument, [
        P("Osc-A Level", 0.8, 0.0, 1.0, fader_display, 0.8),
        P("Osc-A Coarse", 1.0, 0.0, 48.0, plain("%.0f"), 1.0),
        Q("Osc-A Wave", 0, ["Sine", "Saw D", "Square D", "Noise White"]),
        P("Filter Freq", 0.5, 0.0, 1.0, hz_display, 0.5),
        P("Filter Res", 0.0, 0.0, 1.25, plain("%.2f"), 0.0),
        Q("Filter On", 1, ["Off", "On"]),
        P("Attack", 1.0, 0.1, 20000.0, ms_display, 1.0, original_name="Ae Attack"),
        P("Attack", 5.0, 0.1, 20000.0, ms_display, 5.0, original_name="Be Attack"),
        P("Volume", 0.7, 0.0, 1.0, fader_display, 0.7),
        P("Transpose", 0.0, -48.0, 48.0, st_display, 0.0),
        P("LFO Rate", 0.3, 0.0, 1.0, hz_display, 0.3),
    ])


def make_analog():
    return Device("Analog", "UltraAnalog", "Analog", DeviceType.instrument, [
        P("F1 Freq", 0.5, 0.0, 1.0, hz_display, 0.5),
        P("F1 Reso", 0.1, 0.0, 1.0, pct_display, 0.1),
        P("Volume", 0.8, 0.0, 1.0, fader_display, 0.8),
    ])


def make_drift():
    return Device("Drift", "Drift", "Drift", DeviceType.instrument, [
        P("Filter Freq", 0.5, 0.0, 1.0, hz_display, 0.5),
        P("Filter Res", 0.1, 0.0, 1.0, pct_display, 0.1),
        Q("Osc 1 Shape", 0, ["Sine", "Triangle", "Saw", "Rect"]),
        P("Volume", 0.8, 0.0, 1.0, fader_display, 0.8),
    ])


def make_simpler(sample_name):
    device = Device("Simpler", "OriginalSimpler", "Simpler", DeviceType.instrument, [
        P("Volume", 0.8, 0.0, 1.0, fader_display, 0.8),
        P("Transpose", 0.0, -48.0, 48.0, st_display, 0.0),
        P("Filter Freq", 1.0, 0.0, 1.0, hz_display, 1.0),
        P("S Start", 0.0, 0.0, 1.0, pct_display, 0.0),
    ])
    device.name = sample_name
    return device


def make_compressor():
    return Device("Compressor", "Compressor2", "Compressor", DeviceType.audio_effect, [
        P("Threshold", 0.5, 0.0, 1.0, threshold_display, 0.5),
        P("Ratio", 4.0, 1.0, 20.0, plain("%.1f : 1"), 4.0),
        P("Attack", 1.0, 0.01, 1000.0, ms_display, 1.0),
        P("Release", 50.0, 1.0, 3000.0, ms_display, 50.0),
        P("Knee", 6.0, 0.0, 18.0, db_display, 6.0),
        Q("Model", 0, ["Peak", "RMS", "Expand"]),
        P("Dry/Wet", 1.0, 0.0, 1.0, pct_display, 1.0),
        P("Output Gain", 0.0, -36.0, 36.0, db_display, 0.0),
    ])


def make_eq8():
    return Device("EQ Eight", "Eq8", "EQ Eight", DeviceType.audio_effect, [
        P("1 Frequency A", 0.3, 0.0, 1.0, hz_display, 0.3),
        P("1 Gain A", 0.0, -15.0, 15.0, db_display, 0.0),
        P("2 Frequency A", 0.6, 0.0, 1.0, hz_display, 0.6),
        P("2 Gain A", 0.0, -15.0, 15.0, db_display, 0.0),
        Q("Mode", 0, ["Stereo", "L/R", "M/S"]),
        P("Output Gain", 0.0, -12.0, 12.0, db_display, 0.0),
    ])


def make_reverb():
    return Device("Reverb", "Reverb", "Reverb", DeviceType.audio_effect, [
        P("Decay Time", 2000.0, 200.0, 60000.0, ms_display, 2000.0),
        P("PreDelay", 2.5, 0.5, 250.0, ms_display, 2.5),
        P("Room Size", 50.0, 0.22, 500.0, plain("%.1f"), 50.0),
        Q("Quality", 1, ["Eco", "Mid", "High"]),
        P("Dry/Wet", 0.3, 0.0, 1.0, pct_display, 0.3),
    ])


def make_hybrid_reverb():
    return Device("Hybrid Reverb", "Hybrid", "Hybrid Reverb", DeviceType.audio_effect, [
        P("Decay", 2.0, 0.1, 60.0, plain("%.2f s"), 2.0),
        P("Dry/Wet", 0.3, 0.0, 1.0, pct_display, 0.3),
    ])


def make_delay():
    return Device("Delay", "Delay", "Delay", DeviceType.audio_effect, [
        P("L Time", 250.0, 1.0, 5000.0, ms_display, 250.0),
        P("R Time", 375.0, 1.0, 5000.0, ms_display, 375.0),
        P("Feedback", 0.4, 0.0, 0.95, pct_display, 0.4),
        Q("Mode", 0, ["Repitch", "Fade", "Jump"]),
        P("Dry/Wet", 0.25, 0.0, 1.0, pct_display, 0.25),
    ])


def make_saturator():
    return Device("Saturator", "Saturator", "Saturator", DeviceType.audio_effect, [
        P("Drive", 0.0, 0.0, 36.0, db_display, 0.0),
        Q("Type", 0, ["Analog Clip", "Soft Sine", "Medium Curve", "Hard Curve", "Sinoid Fold", "Digital Clip"]),
        P("Dry/Wet", 1.0, 0.0, 1.0, pct_display, 1.0),
    ])


def make_roar():
    return Device("Roar", "Roar", "Roar", DeviceType.audio_effect, [
        P("Drive", 0.3, 0.0, 1.0, pct_display, 0.3),
        P("Tone", 0.5, 0.0, 1.0, pct_display, 0.5),
        P("Dry/Wet", 1.0, 0.0, 1.0, pct_display, 1.0),
    ])


def make_limiter():
    return Device("Limiter", "Limiter", "Limiter", DeviceType.audio_effect, [
        P("Gain", 0.0, -24.0, 24.0, db_display, 0.0),
        P("Ceiling", -0.3, -24.0, 0.0, db_display, -0.3),
        Q("Lookahead", 1, ["1.5 ms", "3 ms", "6 ms"]),
    ])


def make_utility():
    return Device("Utility", "StereoGain", "Utility", DeviceType.audio_effect, [
        P("Gain", 0.0, -35.0, 35.0, db_display, 0.0),
        P("Stereo Width", 1.0, 0.0, 4.0, pct_display, 1.0),
        Q("Mono", 0, ["Off", "On"]),
    ])


def make_arpeggiator():
    return Device("Arpeggiator", "MidiArpeggiator", "Arpeggiator", DeviceType.midi_effect, [
        Q("Style", 0, ["Up", "Down", "UpDown", "DownUp", "Random", "Chord Trigger"]),
        P("Synced Rate", 5.0, 0.0, 10.0, plain("1/%.0f"), 5.0),
        P("Gate", 0.5, 0.0, 2.0, pct_display, 0.5),
        P("Steps", 0.0, 0.0, 8.0, plain("%.0f"), 0.0),
    ])


def make_chord():
    return Device("Chord", "MidiChord", "Chord", DeviceType.midi_effect, [
        P("Shift1", 0.0, -36.0, 36.0, st_display, 0.0),
        P("Shift2", 0.0, -36.0, 36.0, st_display, 0.0),
        P("Velocity1", 100.0, 1.0, 200.0, pct_display, 100.0),
    ])


def make_scale_effect():
    return Device("Scale", "MidiScale", "Scale", DeviceType.midi_effect, [
        P("Base", 0.0, 0.0, 11.0, plain("%.0f"), 0.0),
        P("Transpose", 0.0, -12.0, 12.0, st_display, 0.0),
    ])


def make_auto_filter():
    return Device("Auto Filter", "AutoFilter", "Auto Filter", DeviceType.audio_effect, [
        P("Frequency", 0.7, 0.0, 1.0, hz_display, 0.7),
        P("Resonance", 0.3, 0.0, 1.25, plain("%.2f"), 0.3),
        Q("Filter Type", 0, FILTER_TYPES),
        P("LFO Amount", 0.0, 0.0, 1.0, pct_display, 0.0),
        P("LFO Rate", 1.0, 0.01, 50.0, plain("%.2f Hz"), 1.0),
        P("Env. Amount", 0.0, -1.0, 1.0, pct_display, 0.0),
        P("Dry/Wet", 1.0, 0.0, 1.0, pct_display, 1.0),
    ])


DEFAULT_PADS = ((36, "Kick 909"), (38, "Snare 909"), (42, "Hat Closed 909"), (39, "Clap 909"))
KIT_PADS = {
    "808 Core Kit": ((36, "Kick 808"), (38, "Snare 808"), (42, "Hat 808"), (46, "Open Hat 808"), (39, "Clap 808")),
    "909 Core Kit": DEFAULT_PADS,
}


def make_drum_rack(name="Drum Rack", pads=DEFAULT_PADS):
    chains = [DrumChain(pad_name, note, [make_simpler(pad_name)]) for note, pad_name in pads]
    return RackDevice(name, "DrumGroupDevice", "Drum Rack", DeviceType.instrument, chains, is_drum_rack=True)


def make_instrument_rack(name="Pad Rack"):
    chains = [Chain("Pad A", [make_wavetable()]), Chain("Pad B", [make_wavetable()])]
    rack = RackDevice(name, "InstrumentGroupDevice", "Instrument Rack", DeviceType.instrument, chains)
    # Renamed macros keep their original_name ("Macro 1", "Macro 2").
    rack.parameters[1].name = "Cutoff"
    rack.parameters[2].name = "Reso"
    return rack


def make_audio_effect_rack(name="FX Rack"):
    chains = [Chain("Wet", [make_reverb()]), Chain("Dry", [make_utility()])]
    return RackDevice(name, "AudioEffectGroupDevice", "Audio Effect Rack", DeviceType.audio_effect, chains)


# --------------------------------------------------------------------------
# Browser
# --------------------------------------------------------------------------

def _preset(name, uri, factory):
    return BrowserItem(name, uri, is_loadable=True, is_device=False, factory=factory)


def _device_item(name, uri, factory, presets=()):
    return BrowserItem(name, uri, is_loadable=True, is_device=True, factory=factory, children=presets)


def _folder(name, uri, children):
    return BrowserItem(name, uri, is_folder=True, children=children)


def make_browser():
    instruments = _folder("Instruments", "query:Synths", [
        _device_item("Analog", "query:Synths#Analog", make_analog, [
            _preset("Analog Bass", "query:Synths#Analog:Analog%20Bass.adv", make_analog)]),
        _device_item("Drift", "query:Synths#Drift", make_drift),
        _device_item("Drum Rack", "query:Synths#Drum%20Rack", lambda: make_drum_rack("Drum Rack", ()), [
            _preset("808 Core Kit", "query:Synths#Drum%20Rack:808%20Core%20Kit.adg",
                    lambda: make_drum_rack("808 Core Kit", KIT_PADS["808 Core Kit"])),
            _preset("909 Core Kit", "query:Synths#Drum%20Rack:909%20Core%20Kit.adg",
                    lambda: make_drum_rack("909 Core Kit", KIT_PADS["909 Core Kit"]))]),
        _device_item("Instrument Rack", "query:Synths#Instrument%20Rack", lambda: make_instrument_rack("Instrument Rack")),
        _device_item("Operator", "query:Synths#Operator", make_operator, [
            _preset("Deep Bass", "query:Synths#Operator:Deep%20Bass.adv", make_operator),
            _preset("FM Pluck", "query:Synths#Operator:FM%20Pluck.adv", make_operator)]),
        _device_item("Wavetable", "query:Synths#Wavetable", make_wavetable, [
            _preset("Bright Keys", "query:Synths#Wavetable:Bright%20Keys.adv", make_wavetable),
            _preset("Warm Pad", "query:Synths#Wavetable:Warm%20Pad.adv", make_wavetable)]),
    ])
    audio_effects = _folder("Audio Effects", "query:AudioFx", [
        _device_item("Audio Effect Rack", "query:AudioFx#Audio%20Effect%20Rack", make_audio_effect_rack),
        _device_item("Auto Filter", "query:AudioFx#Auto%20Filter", make_auto_filter),
        _device_item("Compressor", "query:AudioFx#Compressor", make_compressor, [
            _preset("Glue Bus", "query:AudioFx#Compressor:Glue%20Bus.adv", make_compressor)]),
        _device_item("Delay", "query:AudioFx#Delay", make_delay),
        _device_item("EQ Eight", "query:AudioFx#EQ%20Eight", make_eq8),
        _device_item("Hybrid Reverb", "query:AudioFx#Hybrid%20Reverb", make_hybrid_reverb),
        _device_item("Limiter", "query:AudioFx#Limiter", make_limiter),
        _device_item("Reverb", "query:AudioFx#Reverb", make_reverb, [
            _preset("Big Hall", "query:AudioFx#Reverb:Big%20Hall.adv", make_reverb)]),
        _device_item("Roar", "query:AudioFx#Roar", make_roar),
        _device_item("Saturator", "query:AudioFx#Saturator", make_saturator),
        _device_item("Utility", "query:AudioFx#Utility", make_utility),
    ])
    midi_effects = _folder("MIDI Effects", "query:MidiFx", [
        _device_item("Arpeggiator", "query:MidiFx#Arpeggiator", make_arpeggiator),
        _device_item("Chord", "query:MidiFx#Chord", make_chord),
        _device_item("Scale", "query:MidiFx#Scale", make_scale_effect),
    ])
    drums = _folder("Drums", "query:Drums", [
        _folder("Drum Hits", "query:Drums#Drum%20Hits", [
            _preset("Kick 909.aif", "query:Drums#Drum%20Hits:Kick%20909.aif", None),
            _preset("Snare 909.aif", "query:Drums#Drum%20Hits:Snare%20909.aif", None),
        ]),
        _folder("Drum Kits", "query:Drums#Drum%20Kits", [
            _preset("808 Core Kit", "query:Drums#Drum%20Kits:808%20Core%20Kit.adg",
                    lambda: make_drum_rack("808 Core Kit", KIT_PADS["808 Core Kit"])),
        ]),
    ])
    sounds = _folder("Sounds", "query:Sounds", [
        _folder("Bass", "query:Sounds#Bass", [
            _preset("Deep Bass", "query:Sounds#Bass:Deep%20Bass.adg", make_operator),
            _preset("Sub Bass", "query:Sounds#Bass:Sub%20Bass.adg", make_operator),
        ]),
        _folder("Pad", "query:Sounds#Pad", [
            _preset("Warm Pad", "query:Sounds#Pad:Warm%20Pad.adg", make_wavetable),
            _preset("Reverb Tail", "query:Sounds#Pad:Reverb%20Tail.adg", make_wavetable),
        ]),
    ])
    plugins = _folder("Plug-Ins", "query:Plugins", [])
    max_for_live = _folder("Max for Live", "query:M4L", [
        _device_item("LFO", "query:M4L#LFO", make_utility)])
    packs = _folder("Packs", "query:Packs", [])
    user_library = _folder("User Library", "query:UserLibrary", [
        _folder("Presets", "query:UserLibrary#Presets", [
            _preset("My Bass.adv", "query:UserLibrary#Presets:My%20Bass.adv", make_operator)]),
        # A node that raises on access, as some roots do in real Live.
        BrowserItem("Broken Folder", "query:UserLibrary#Broken", is_folder=True, raises_on_children=True),
    ])
    samples = _folder("Samples", "query:Samples", [
        _preset("Vinyl Noise.wav", "query:Samples#Vinyl%20Noise.wav", None)])
    clips = _folder("Clips", "query:Clips", [
        _preset("Groove 1.alc", "query:Clips#Groove%201.alc", None)])
    return Browser(instruments=instruments, sounds=sounds, drums=drums, audio_effects=audio_effects,
                   midi_effects=midi_effects, plugins=plugins, max_for_live=max_for_live, packs=packs,
                   user_library=user_library, samples=samples, clips=clips)


# --------------------------------------------------------------------------
# Set
# --------------------------------------------------------------------------

def _notes(*triples):
    """(pitch, start, duration[, velocity]) tuples -> MidiNoteSpecification tuple."""
    specs = []
    for item in triples:
        pitch, start, duration = item[0], item[1], item[2]
        velocity = item[3] if len(item) > 3 else 100.0
        specs.append(MidiNoteSpecification(pitch=pitch, start_time=start, duration=duration, velocity=velocity))
    return tuple(specs)


def _midi_clip(track, slot_index, name, length, notes):
    slot = track.clip_slots[slot_index]
    slot.create_clip(length)
    clip = slot.clip
    clip.name = name
    if notes:
        clip.add_new_notes(notes)
    return clip


class FakeCInstance(object):
    """What Live passes to create_instance()."""

    def __init__(self, song):
        self._song = song
        self.logged = []
        self.shown = []

    def song(self):
        return self._song

    def log_message(self, message):
        self.logged.append(message)

    def show_message(self, message):
        self.shown.append(message)

    def handle(self):
        return None

    def update_locks(self):
        pass

    def set_feedback_velocity(self, velocity):
        pass


class FakeLive(object):
    def __init__(self, app, song, browser):
        self.app = app
        self.song = song
        self.browser = browser

    def track(self, name):
        for track in self.song.tracks:
            if track.name == name:
                return track
        raise KeyError(name)


def make_set():
    song = Song()
    for name in SCENE_NAMES:
        song._add_scene(Scene(song, name))

    drums = song._add_track(Track(song, "Drums", "midi"))
    drums.color_index = 1
    drums._insert_device(make_drum_rack("Drum Rack"))
    drums._insert_device(make_compressor())

    bass = song._add_track(Track(song, "Bass", "midi"))
    bass.color_index = 14
    bass._insert_device(make_operator())

    pad = song._add_track(Track(song, "Pad", "midi"))
    pad.color_index = 25
    pad._insert_device(make_arpeggiator())
    pad._insert_device(make_chord())
    pad._insert_device(make_instrument_rack())
    pad._insert_device(make_auto_filter())

    vox = song._add_track(Track(song, "Vox", "audio"))
    vox.color_index = 40
    vox._insert_device(make_eq8())
    vox._insert_device(make_reverb())

    synths = song._add_track(Track(song, "Synths", "group"))
    synths.color_index = 55

    lead = song._add_track(Track(song, "Lead", "midi"))
    lead.color_index = 60
    lead._group_track = synths
    lead._insert_device(make_drift())

    return_a = song.create_return_track()
    return_a.name = "A-Reverb"
    return_a._insert_device(make_reverb())
    return_b = song.create_return_track()
    return_b.name = "B-Delay"
    return_b._insert_device(make_delay())
    song.master_track._insert_device(make_limiter())

    _midi_clip(drums, 0, "Drums 1", 4.0, _notes(
        (36, 0.0, 0.25, 110), (36, 1.0, 0.25, 110), (36, 2.0, 0.25, 110), (36, 3.0, 0.25, 110),
        (38, 1.0, 0.25, 100), (38, 3.0, 0.25, 100),
        (42, 0.5, 0.25, 80), (42, 1.5, 0.25, 80), (42, 2.5, 0.25, 80), (42, 3.5, 0.25, 80)))
    _midi_clip(drums, 1, "Drums 2", 8.0, _notes(*[(36, float(beat), 0.25, 110) for beat in range(8)]))
    _midi_clip(bass, 0, "Bass 1", 4.0, _notes(
        (36, 0.0, 1.0, 100), (36, 1.0, 0.5, 90), (43, 1.5, 0.5, 90), (36, 2.0, 1.0, 100), (41, 3.0, 1.0, 95)))
    _midi_clip(bass, 1, "Bass 2", 8.0, _notes((36, 0.0, 2.0), (39, 2.0, 2.0), (41, 4.0, 2.0), (43, 6.0, 2.0)))
    _midi_clip(pad, 0, "Pad 1", 16.0, _notes(
        (60, 0.0, 8.0, 80), (64, 0.0, 8.0, 80), (67, 0.0, 8.0, 80),
        (62, 8.0, 8.0, 80), (65, 8.0, 8.0, 80), (69, 8.0, 8.0, 80)))
    _midi_clip(lead, 2, "Lead 1", 4.0, _notes((72, 0.0, 0.5), (74, 0.5, 0.5), (76, 1.0, 1.0)))

    vox_slot = vox.clip_slots[0]
    vox_clip = Clip("Vox Take 1", 8.0, is_midi=False, track=vox, slot=vox_slot)
    vox_slot._clip = vox_clip

    drums.duplicate_clip_to_arrangement(drums.clip_slots[0].clip, 0.0)
    drums.duplicate_clip_to_arrangement(drums.clip_slots[1].clip, 8.0)

    song.current_song_time = 64.0
    song.set_or_delete_cue()
    song.cue_points[0].name = "Drop"
    song.current_song_time = 0.0

    song.view.selected_track = bass
    song.view.selected_scene = song.scenes[0]

    browser = make_browser()
    app = Application(song, browser, version=(12, 1, 5))
    return FakeLive(app, song, browser)
