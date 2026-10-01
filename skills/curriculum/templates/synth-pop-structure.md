# Template: synth-pop / indie dance structure (120 BPM, ~3:36)

Typical of the style, not a transcription of any song. 108 bars at 120 BPM = 432 beats = 216 s. Bar N starts at beat (N − 1) × 4; at 120 BPM a bar is 2.0 s. Key suggestion: D major (`set_scale(root_note="D", scale_name="Major")`), progression I–V–vi–IV = D – A – Bm – G.

## Section table

| # | Section | Bars | Beats (start–end) | Time | What plays | Energy |
|---|---|---|---|---|---|---|
| 0 | Intro | 1–8 | 0–32 | 0:00 | Arp + pad, low-passed; hats enter at bar 5; no kick. | 3 |
| 1 | Verse 1 | 9–24 | 32–96 | 0:16 | Kick + hats (no clap for bars 9–16), bass, pad; melodic space for a topline. Clap joins at bar 17. | 5 |
| 2 | Pre-Chorus 1 | 25–32 | 96–128 | 0:48 | Chords change twice per bar (IV–V alternation), riser, filter opens on the pad, snare build in bars 31–32. | 6 |
| 3 | Chorus 1 | 33–48 | 128–192 | 1:04 | Full drums with open hats, bass, pad, lead hook, arp. Everything. | 9 |
| 4 | Verse 2 | 49–56 | 192–224 | 1:36 | Drop the lead; keep bass + drums; add a counter-arp or a pluck. | 6 |
| 5 | Pre-Chorus 2 | 57–64 | 224–256 | 1:52 | As Pre-Chorus 1 plus a longer riser and a 2-bar snare roll. | 7 |
| 6 | Chorus 2 | 65–80 | 256–320 | 2:08 | Chorus 1 plus a lead harmony a third above (bars 73–80). | 9 |
| 7 | Bridge | 81–88 | 320–352 | 2:40 | No kick. Pad + arp only, filter sweeping down then up; lean on IV and vi; last beat silent. | 4 |
| 8 | Final Chorus | 89–104 | 352–416 | 2:56 | Everything, open hats on every offbeat, lead up an octave in bars 97–104. | 10 |
| 9 | Outro | 105–108 | 416–432 | 3:28 | Pad + arp fading; filter closing; last chord rings. | 2 |

Energy 1–10 is a guide for what to add or remove: each step up adds one element or opens a filter; each step down removes one.

## Role tracks

| Track | Role | Suggested device | Colour (approx. index) |
|---|---|---|---|
| Drums | Drum Rack kit (909-style) | Drum Rack | 14 (red) |
| Sub | sine, octave below bass, choruses only | Operator or Drift (sine) | 1 (orange) |
| Bass | mid synth bass | Drift or Analog, low-pass | 15 (orange) |
| Pad | chords | Drift / Wavetable / Analog pad | 9 (blue) |
| Arp | 16th arpeggio of the chord tones | Arpeggiator → Drift pluck | 7 (cyan) |
| Lead | hook melody | Analog / Wavetable bright saw | 3 (yellow) |
| FX | risers, sweeps, impacts | Drift noise/saw + Auto Filter | 11 (purple) |

## Scenes (Session View)

One scene per section, in order; scene index = row in the table above. Fill each scene with the clips the "What plays" column lists, using `duplicate_clip` from a master version and editing variations (remove the clap for Verse 1, add the open hats for choruses).

```
set_transport(tempo=120, why="Synth-pop tempo")
set_scale(root_note="D", scale_name="Major", why="Bright major key for the hook")
create_scene(name="Intro");  create_scene(name="Verse 1");  create_scene(name="Pre 1")
create_scene(name="Chorus 1");  create_scene(name="Verse 2");  create_scene(name="Pre 2")
create_scene(name="Chorus 2");  create_scene(name="Bridge");  create_scene(name="Final Chorus")
create_scene(name="Outro")
set_scene(scene=3, color_index=3)   # colour the choruses so the grid shows the energy shape
set_scene(scene=6, color_index=3);  set_scene(scene=8, color_index=3)
```

If the set already has scenes, `set_scene(scene=i, name=...)` on the existing ones instead of creating new ones, and say so.

## Locators and arrangement

```
show_view("Arranger")
set_locator(time=0,   name="Intro")
set_locator(time=32,  name="Verse 1")
set_locator(time=96,  name="Pre 1")
set_locator(time=128, name="Chorus 1")
set_locator(time=192, name="Verse 2")
set_locator(time=224, name="Pre 2")
set_locator(time=256, name="Chorus 2")
set_locator(time=320, name="Bridge")
set_locator(time=352, name="Final Chorus")
set_locator(time=416, name="Outro")
set_locator(time=432, name="End")
```

Placing clips: for each section and each role that plays, `add_clip_to_arrangement(track, slot=<scene index>, time=<section start>)`. A 4-bar clip (16 beats) in a 16-bar section goes in four times: `time`, `time+16`, `time+32`, `time+48`. An 8-bar section takes two placements. Verify with `get_arrangement()` (clip `start_time`/`end_time` per track) and ask the user to click **Back to Arrangement** before listening.

Skeleton placeholders (song-study Skeleton level): create one empty MIDI clip per role per section with `create_clip(track, slot=<scene>, length=<section length in beats>, name="<Role> – <Section>")`, colour it with `set_clip(color_index=...)`, then place it once at the section start.

## Checks after laying it out

- `get_arrangement().locators` has 11 entries at the times above, ascending.
- Every section in the table has a Drums clip except Intro (bars 1–4), Bridge and Outro.
- The Lead track is empty in Verse 1, Verse 2 and Bridge.
- `get_transport().song_length` ≈ 432.
