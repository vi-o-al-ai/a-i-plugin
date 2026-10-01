# Template: riddim / dubstep structure (140 BPM, ~3:33)

Typical of the style, not a transcription of any song. 124 bars at 140 BPM = 496 beats ≈ 212.6 s. Bar N starts at beat (N − 1) × 4; at 140 BPM a bar is 1.714 s (seconds = beats × 60 / 140). Felt as half-time: snare on beat 3. Key suggestion: F minor (`set_scale(root_note="F", scale_name="Minor")`), sub root F0 = MIDI 29, mid bass root F1 = MIDI 41.

## Section table

| # | Section | Bars | Beats (start–end) | Time | What plays | Energy |
|---|---|---|---|---|---|---|
| 0 | Intro | 1–16 | 0–64 | 0:00 | Atmosphere pad on i (drone), filtered hats, a vocal-chop-style stab or FX every 4 bars, sub hint at bars 13–16. | 3 |
| 1 | Build 1 | 17–32 | 64–128 | 0:27 | Snare on 3 enters at bar 17; riser from bar 25; hats double at bar 29; snare roll bars 31–32; **beat 4 of bar 32 silent** (or a shout). | 6 → 8 |
| 2 | Drop 1 (A) | 33–48 | 128–192 | 0:55 | Half-time drums, wobble bass call (bars 33–34) and growl response (35–36) repeating; clean sub follows the bass roots; laser FX on phrase ends. | 10 |
| 2 | Drop 1 (B) | 49–64 | 192–256 | 1:22 | Switch-up: new bass sound or rhythm (e.g. 1/16 wobble instead of triplets); extra kick on the "and" of 4 every second bar; fill at 63–64. | 10 |
| 3 | Breakdown | 65–80 | 256–320 | 1:50 | Pad progression i–VI–III–VII, pluck melody, no kick/snare for bars 65–72; hats and a soft snare return at 73. | 4 |
| 4 | Build 2 | 81–88 | 320–352 | 2:17 | Short build: riser + snare roll (8 bars), filter opening, silent last beat. | 8 |
| 5 | Drop 2 (A) | 89–104 | 352–416 | 2:31 | Drop 1 A material with the roles swapped (growl calls, wobble answers) or a new growl. | 10 |
| 5 | Drop 2 (B) | 105–120 | 416–480 | 2:58 | Second switch-up; densest bass rhythm of the track; double-time hats for bars 117–120. | 10 |
| 6 | Outro | 121–124 | 480–496 | 3:26 | Sub tail on the root, atmosphere, one last FX hit. | 2 |

Drop halves share a scene number in Session (one 32-bar section, two 16-bar scenes if you want the switch-up as its own row: then renumber scenes 2a/2b and 5a/5b).

## Role tracks

| Track | Role | Suggested device | Colour (approx. index) |
|---|---|---|---|
| Drums | kick, snare + clap layer, hats | Drum Rack kit (hard electronic) | 14 (red) |
| Sub | clean sine, mono, no FX | Operator (default sine) | 1 (orange) |
| Wobble | LFO-filtered bass, call | Drift/Wavetable saw → Auto Filter → Saturator → OTT → EQ Eight low cut | 15 (orange) |
| Growl | FM / wavetable-position bass, response | Operator FM or Wavetable → Saturator/Roar → OTT → EQ Eight low cut | 12 (magenta) |
| Pad | breakdown chords, intro drone | Drift / Wavetable pad | 9 (blue) |
| Pluck | breakdown melody | Drift pluck + delay send | 7 (cyan) |
| FX | risers, impacts, lasers, sub drop | Drift noise/saw + Auto Filter; Operator pitch envelope | 11 (purple) |

## Scenes (Session View)

```
set_transport(tempo=140, why="Dubstep tempo, felt as half-time")
set_scale(root_note="F", scale_name="Minor", why="Minor key; F0 sub sits in the sub range")
create_scene(name="Intro");  create_scene(name="Build 1")
create_scene(name="Drop 1 A");  create_scene(name="Drop 1 B")
create_scene(name="Breakdown");  create_scene(name="Build 2")
create_scene(name="Drop 2 A");  create_scene(name="Drop 2 B")
create_scene(name="Outro")
set_scene(scene=2, color_index=14);  set_scene(scene=3, color_index=14)
set_scene(scene=6, color_index=14);  set_scene(scene=7, color_index=14)
```

With this split, scene indexes are: 0 Intro, 1 Build 1, 2 Drop 1 A, 3 Drop 1 B, 4 Breakdown, 5 Build 2, 6 Drop 2 A, 7 Drop 2 B, 8 Outro. Use these as `slot` when placing clips.

## Locators and arrangement

```
show_view("Arranger")
set_locator(time=0,   name="Intro")
set_locator(time=64,  name="Build 1")
set_locator(time=128, name="Drop 1")
set_locator(time=192, name="Drop 1 B")
set_locator(time=256, name="Breakdown")
set_locator(time=320, name="Build 2")
set_locator(time=352, name="Drop 2")
set_locator(time=416, name="Drop 2 B")
set_locator(time=480, name="Outro")
set_locator(time=496, name="End")
```

Placing clips: `add_clip_to_arrangement(track, slot=<scene>, time=<section start>)` once per clip-length repeat. Riddim bass phrases are usually 2-bar clips (`length=8.0`) or 4-bar (`length=16.0`); a 16-bar drop half takes 8 or 4 placements. For drops, place the drum clip as 4-bar repeats and the bass as 2-bar repeats, then replace the last repeat with a fill variation. Verify with `get_arrangement()`; remind the user to click **Back to Arrangement**.

Skeleton placeholders: one empty MIDI clip per role per section, `create_clip(track, slot, length=<section beats>, name="<Role> – <Section>")`, coloured with `set_clip(color_index=...)`, placed once.

## Checks after laying it out

- 10 locators at the times above, ascending; the gap Build → Drop is exactly 64 beats (16 bars).
- Drums present in Build 1 (snare only in bars 17–24 is a variation clip), both drops, bars 73–80 of the Breakdown, Build 2; absent in Intro bars 1–8, Breakdown bars 65–72, Outro.
- Sub and bass tracks empty in the Breakdown except the sub drone if intended.
- The last beat before each drop (beats 124–128 and 348–352) has no drum notes.
- `get_transport().song_length` ≈ 496.
