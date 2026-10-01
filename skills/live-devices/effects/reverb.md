# Reverb (`Reverb`)

Algorithmic reverb: input filter → early reflections → diffusion network (the tail) with its own
shelving EQ, chorus and freeze. Use on a **return track** with sends, not on every track.

Load: `create_return_track(name="Reverb")` then
`load_device(name="Reverb", track=0, track_type="return", category="audio_effects")`; set the
return's device `Dry/Wet` 100 % and feed it with `set_track(track, sends=[{"index": 0, "value": 0.3}])`.

## Parameters

| LOM name | Section | What it does | Start |
|---|---|---|---|
| `Predelay` | Input | Gap before the reverb starts (ms) — separates source from tail | 10 ms snare · 25 ms pad |
| `In LowCut On`, `In HighCut On`, `In Filter Freq`, `In Filter Width` | Input | Band-limit what enters the reverb | LowCut ≈ 200 Hz on |
| `ER Spin On`, `ER Spin Rate`, `ER Spin Amount`, `ER Shape` | Early reflections | Movement and shape of the first echoes | Spin on, small |
| `Reflect Level` | Early reflections | Level of early echoes vs tail | 0 dB |
| `Room Size` | Tail | Size (small room → hall) | 30 snare · 90 pad |
| `Size Smoothing` | Tail | How fast size changes glide | default |
| `Decay Time` | Tail | Length of the tail (ms/s) — the big one | 1.2 s snare · 5 s pad |
| `Diffusion`, `Density` | Tail | Smoothness / thickness | high for pads |
| `Scale` | Tail | Spacing of the diffusion network (metallic ↔ smooth) | default |
| `LowShelf On`, `LowShelf Freq`, `LowShelf Gain` | Tail EQ | Remove low mud from the tail | ≈ 250 Hz, −6 dB |
| `HiFilter On`, `HiFilter Freq`, `HiShelf Gain` (newer builds: `Diff. Hi Freq`, `Diff. Hi Type`) | Tail EQ | Darken the tail | ≈ 5 kHz, −4 dB |
| `Chorus On`, `Chorus Rate`, `Chorus Amount` | Tail | Modulates the tail — lush, less metallic | On, 0.3 Hz, small |
| `Freeze On`, `Flat On`, `Cut On` | Tail | Infinite hold (riser/drone), bypass tail EQ when frozen, cut input | Off |
| `Stereo Image` | Output | 0 = mono, 120 = wide | 100–120 |
| `Diffuse Level` | Output | Tail level vs early reflections | 0 dB |
| `Dry/Wet` | Output | 100 % on returns; 15–30 % as insert | — |
| Quality (Eco/Mid/High) | Output | UI chooser; verify if a parameter appears | High |

## Recipes

### Lush pad hall (return)
```
Predelay 25 ms; In LowCut On ≈ 220 Hz; Room Size 95; Decay Time 5 s; Diffusion 90 %; Density high
LowShelf On ≈ 250 Hz −6 dB; HiFilter On ≈ 5 kHz −3 dB; Chorus On, Rate 0.3 Hz, Amount 20 %
Stereo Image 120; Dry/Wet 100 % (return); sends: pad 0.35, lead 0.2, stabs 0.15
```
Why: long, dark, moving tail makes synth-pop chords feel wide without clouding the mix.

### Dubstep snare room/plate
```
Predelay 8 ms; Room Size 35; Decay Time 1.4 s; In LowCut ≈ 300 Hz; HiFilter ≈ 6 kHz; Stereo Image 100
As insert on the snare: Dry/Wet 22 %; or a dedicated return with send 0.4
```
Why: a short bright tail makes the snare on 3 sound huge without smearing the next kick.

### Freeze riser
```
Decay Time 10 s; Freeze On On during the last 2 bars of a build (automate `Freeze On` with mode "steps"); Dry/Wet 100 % on a return; automate send up
```

### Tiny ambience for stabs
```
Predelay 5 ms; Room Size 15; Decay Time 0.7 s; Dry/Wet 15 % as insert
```

## Rules
Never send kick, sub or mid bass to reverb. High-pass the return. Predelay before decay when it sounds muddy.
