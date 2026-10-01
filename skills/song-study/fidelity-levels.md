# Fidelity levels: exact tool sequences

All three levels share the same set layout: one MIDI track per role, one scene per section, locators at section starts. Each level adds to the previous one. Indexes below are examples; read `get_session()` first and use the real ones. Fill `why` on every mutating call.

Beats: bar N starts at (N − 1) × 4. A section of B bars is B × 4 beats. Colours are approximate Live palette indexes; the response's `color` hex confirms what was set.

## Level 1 · Skeleton (10–15 min)

Outcome: the song's map in both views, nothing audible yet except the metronome.

```
ableton_status()
get_session()                                   # know what exists; reuse or create
set_transport(tempo=<BPM>, why="Song tempo (confidence: <level>)")
set_scale(root_note=<"D">, scale_name=<"Major">, why="Song key (confidence: <level>)")

# Role tracks (skip ones that exist)
create_midi_track(name="Drums");   set_track(track=<i>, color_index=14)
create_midi_track(name="Sub");     set_track(track=<i>, color_index=1)
create_midi_track(name="Bass");    set_track(track=<i>, color_index=15)
create_midi_track(name="Chords");  set_track(track=<i>, color_index=9)
create_midi_track(name="Lead");    set_track(track=<i>, color_index=3)
create_midi_track(name="Vocal/Hook (placeholder)"); set_track(track=<i>, color_index=5)
create_midi_track(name="FX");      set_track(track=<i>, color_index=11)

# Scenes, one per section, in order
create_scene(name="Intro"); create_scene(name="Verse 1"); ...    # or set_scene on existing rows

# Placeholder clips: one empty MIDI clip per role that plays in the section, section-length
create_clip(track=<Drums>, slot=<scene>, length=<bars*4>, name="Drums – Verse 1")
set_clip(track=<Drums>, slot=<scene>, color_index=14)
...                                              # repeat per role × section from the structure table

# Arrangement
show_view("Arranger")
set_locator(time=0, name="Intro"); set_locator(time=32, name="Verse 1"); ...; set_locator(time=<total>, name="End")
add_clip_to_arrangement(track=<Drums>, slot=<scene>, time=<section start>)   # once per placeholder (section-length clips fit exactly)
...

get_arrangement()                                # verify
select(track=<Drums>, scene=0); show_view("Session")   # end on the grid so the map is visible
```

Verify: locators ascending on multiples of 4; each section's placeholders present with `start_time == section start` and `end_time == next section start`; `get_transport().song_length ≈ total beats`; scene count == section count. Then write the brief at Skeleton level.

## Level 2 · Harmony / bass / drums (+20–30 min)

Outcome: the song plays as a sketch: groove, chords, bass per section.

```
# Instruments
browse(query="Kit", categories=["drums"]); load_device(uri=<kit>, track=<Drums>)
get_devices(track=<Drums>, device_path="0")      # read drum_pads before writing drums
load_device(name="Operator", track=<Sub>)        # sine; fall back to Drift
load_device(name="Drift", track=<Bass>)          # saw, low-pass, mono
load_device(name="Drift", track=<Chords>)        # or a pad preset via browse(query="Pad", categories=["sounds"])
get_devices(track=<Bass>, device_path="0", include_params=true)   # real parameter names
set_parameters(track=<Bass>, device_path="0", values=[{parameter:"LP Freq", normalized:<~0.45>}, {parameter:<voice mode, if exposed>, display:"Mono"}])   # Drift names (LP Freq, LP Res/LP Reso); aim ≈ 800 Hz by the display read-back
load_device(name="EQ Eight", track=<Bass>)       # low cut ~90 Hz on the mid bass

# Drums: write the groove once as a 4-bar clip, then copy it into every scene that has drums
create_clip(track=<Drums>, slot=<first drum scene>, length=16.0, name="Drums main")
add_notes(track=<Drums>, slot=<s>, notes=[...kick/snare/hats per method.md §3...])
duplicate_clip(track=<Drums>, slot=<s>, target_slot=<other scene>)   # per section
remove_notes / add_notes for variations (verse without clap; fill in the last bar before a chorus)

# Chords: one clip per distinct progression, 4 or 8 bars, close voicings (curriculum/topics/05)
create_clip(track=<Chords>, slot=<s>, length=16.0, name="Chords verse")
add_notes(track=<Chords>, slot=<s>, notes=[{pitch, start:0.0, duration:4.0, velocity:90}, ...])
get_notes(track=<Chords>, slot=<s>)              # all pitch classes in scale_intervals

# Bass and sub: roots following the chord clip, in register, mono
create_clip(track=<Bass>, slot=<s>, length=16.0, name="Bass verse"); add_notes(...)
create_clip(track=<Sub>, slot=<s>, length=16.0, name="Sub verse"); add_notes(... same pitch classes, octave lower, longer notes ...)

# Replace placeholders in the arrangement: delete the empty placeholder (ask first) or leave it and place the real clip on top
add_clip_to_arrangement(track=<Drums>, slot=<s>, time=<section start>)  # repeat every 16 beats across the section
fire_scene(<s>)                                  # compare-with-original listening exercise
```

Verify with `production-mentor/feedback-checklists.md` (Drums, Chords, Bass) per clip, and `get_arrangement()` for tiling. Compare exercise after each section (method.md).

## Level 3 · Melody and sound design (+30–45 min)

Outcome: the hook is hummable in Live, and each sound is a stock-device stand-in.

```
# Hook (approximate; say so)
load_device(name="Drift", track=<Lead>)          # or Analog/Wavetable (Suite)
create_clip(track=<Lead>, slot=<chorus>, length=16.0, name="Hook (approx.)")
add_notes(track=<Lead>, slot=<chorus>, notes=[... 4-bar motif on chord tones, mostly steps, one change in bar 4 ...])
get_notes(...)                                   # in key, range ≤ 1.5 octaves, lands on chord tones at 0/4/8/12

# Sound design per track: read, set, read back
get_devices(track=<Chords>, device_path="0", include_params=true)
set_parameters(track=<Chords>, device_path="0", values=[{parameter:"Env 1 Attack", normalized:<…>}, {parameter:"Env 1 Release", normalized:<…>}, {parameter:"LP Freq", normalized:<…>}, {parameter:"Osc 2 Gain", normalized:<…>}])   # aim ≈ 400 ms / 2 s / 1.2 kHz / −3 dB by display read-back; Drift has no Osc 2 On switch
load_device(name="Compressor", track=<Chords>)   # sidechain to kick: user routes Audio From (curriculum/topics/08)
create_return_track(name="A Reverb"); load_device(name="Reverb", track=0, track_type="return")
set_track(track=<Chords>, sends=[{index:0, value:0.3}])

# Riddim bass sound (curriculum/topics/07): Drift → Auto Filter → Saturator → OTT → EQ Eight
load_device(name="Auto Filter", track=<Bass>); set_parameters(... LFO Sync display Sync, LFO Sync Rate display 1/8, LFO Amount normalized ≈ 0.7, Frequency normalized to read ≈ 400 Hz ...)
load_device(name="Saturator", track=<Bass>); load_device(name="OTT", track=<Bass>, category="audio_effects")
set_automation(track=<Bass>, slot=<drop>, device_path=<auto filter>, parameter="LFO Sync Rate", points=[...], mode="steps")

# Transitions (curriculum/topics/10)
set_automation(track=<Chords>, slot=<pre>, device_path=<auto filter>, parameter="Frequency", points=[{time:0,value:<low>},{time:32,value:<high>}], mode="ramp")

get_devices(track=<each>)                        # chain order and is_active
```

Verify: hook in key and on chord tones; every chain in the right order with `is_active: true`; parameter `display` values match the recipe; envelopes `exists`. Run the compare exercise on the chorus/drop twice. Update the brief's Instrument roles and What is approximate.

## Stopping and resuming

Each level ends with: `get_arrangement()` summary to the user, the brief written or updated, the journal appended ("Study: <song> at <level>"). On resume, read the brief and `get_session()` first, then continue at the next level. Never redo a finished level unless asked.
