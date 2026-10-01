# Method: deconstructing any track

Order matters: form first, then harmony, then drums, then bass against the kick, then the hook's rhythm, then texture, then transitions. Each step names what to listen for (the user's job), what to decide (Claude's job), and how it maps onto the tools.

Claude cannot hear. Every step below is a conversation: Claude proposes from memory and genre knowledge with a confidence label, the user listens to the original and confirms or corrects, Claude writes it into Live.

## 1. Form: count bars, mark sections

Listen for: where the drums enter, where the vocal/hook enters, where everything drops out, where the biggest moment is.
Decide: tempo (user taps along; or Claude's remembered value, labelled), the list of sections with bar counts (multiples of 4; 8 and 16 most common), total length.
Tools: `set_transport(tempo=...)`; `set_locator(time=(bar−1)*4, name=...)` per section; `create_scene(name=...)` per section. Check: total beats × 60 / BPM ≈ the song's duration; if it is off by more than ~10 s, a section count is wrong.
Tip: ask the user for the song's duration (any player shows it) and solve for the missing bar count.

## 2. Harmonic rhythm and key

Listen for: how often the chord changes (every bar? every two beats?), whether the bass note moves with it, whether it feels bright (major) or dark (minor), whether the chorus feels like it "opens up" (often a move to IV or vi in the bass).
Decide: key (Claude proposes from memory or from the genre's common keys, low confidence unless remembered), the progression per section as Roman numerals, chords per bar.
Tools: `set_scale(root_note, scale_name)`; chords via `add_notes` on a Chords track using close voicings (see `curriculum/topics/05-chords-and-keys.md`). Check with `get_notes` that every pitch class is in `get_session().scale.scale_intervals`.
If the user cannot tell major from minor: write both versions in two slots and let them A/B against the original.

## 3. Drum grid

Listen for: kick on every beat or on 1 and 3 or on 1 only; snare/clap on 2 and 4 or on 3; hats straight or offbeat or triplet; where fills happen.
Decide: the one-bar grid for the main groove, the variation bar, the fill bar.
Tools: Drum Rack via `load_device`; read `drum_pads`; `add_notes` kick/snare/hats; `duplicate_clip_loop` to 4 bars; variations by `remove_notes`/`add_notes`. Check with `production-mentor/feedback-checklists.md` (Drums).
Common cases: synth-pop → four-on-the-floor, clap 2 and 4, offbeat hats; riddim → kick 1, snare 3, sparse.

## 4. Bass relationship to the kick

Listen for: does the bass hit with every kick, between kicks, or hold long notes; does it jump octaves; is there a separate sub hum under a brighter bass.
Decide: rhythm cell (one bar), register (sub 24–40, typically 28–40; mid 36–55), whether two layers are needed.
Tools: Sub and Bass tracks; `add_notes` roots following the chord chart; mono check via `get_notes` (no overlaps). Riddim: triplet cells and a 2-bar call/response; synth-pop: octave bounce or 8th pulses.

## 5. Hook rhythm, then contour

Listen for: the hook's rhythm first (clap it), then its shape (up, down, arch), where it lands relative to bar lines, how many notes.
Decide: a rhythm of 4–8 attacks per bar, a contour over chord tones, repetition with one change in bar 4.
Tools: Lead track, `add_notes`. Say "approximate" every time; verify in key and on chord tones with `get_notes`. Vocal hooks: rhythm and contour only, never words.

## 6. Texture per section

Listen for: what is added at each section (a pad, an arp, open hats, a second bass, a vocal layer) and what is removed.
Decide: a role × section grid (the brief's structure table) with an energy number 1–10.
Tools: `duplicate_clip` into each scene; `remove_notes`/`transpose_notes` for variations; `set_track(color_index)` by role so the grid reads at a glance; `add_clip_to_arrangement` per section.

## 7. Transitions

Listen for: risers, filter sweeps, drum rolls, silence before drops, reverse cymbals, impacts.
Decide: one transition device per boundary.
Tools: `set_automation` on Auto Filter Frequency / mixer Send A / Volume; fill clips; `remove_notes` for the gap; crash at the downbeat. See `curriculum/topics/10-transitions-and-automation.md`.

## 8. Sound design (Melody and sound design level only)

Listen for, per instrument: waveform family (buzzy saw / hollow square / pure sine / noisy), brightness, attack speed, movement (wobble, vibrato), space (dry / reverb / delay), width.
Decide: a stock-device recipe per sound (`curriculum/topics/06-pads-and-leads.md`, `curriculum/topics/07-wobble-and-growl-bass.md`).
Tools: `load_device`, `get_devices(include_params=true)`, `set_parameters`. Verify by `display` read-back; the user judges by ear with an A/B against the original.

## The compare-with-the-original listening exercise

Run it after every section (and once more at the end):

1. Claude: "Play the original from <section> for 8 bars. Listen only for <one thing: the kick pattern / the chord change rate / the bass rhythm>."
2. Claude fires the Live version (`fire_scene(<section>)` or asks the user to play from the locator after Back to Arrangement) and asks them to listen for the same thing.
3. User reports differences in their own words ("the real one has more hats", "the bass is busier", "the chord feels sadder").
4. Claude translates into a change (add offbeat hats; add triplet notes; try the vi instead of the IV), makes it with `why="Compare: user heard ..."`, and repeats once. Two rounds per section, then move on; perfection is not the goal.
5. Write what still differs into the brief's "What is approximate" list.

Say when a reported difference is outside Claude's reach (a specific sample, a vocal timbre, a mastering trait) and note it as "listen for this in the original" rather than trying to fake it.

## Mapping summary

| Deconstruction step | Primary tools | Verify with |
|---|---|---|
| Form | `set_transport`, `set_locator`, `create_scene`/`set_scene` | `get_arrangement().locators`, duration maths |
| Harmony | `set_scale`, `add_notes` | `get_notes` vs `scale_intervals` |
| Drums | `load_device`, `add_notes`, `duplicate_clip_loop` | `get_notes`, `drum_pads` |
| Bass | `add_notes`, `transpose_notes` | `get_notes` (mono, register) |
| Hook | `add_notes` | `get_notes` (in key, chord tones) |
| Texture | `duplicate_clip`, `set_track`, `add_clip_to_arrangement` | `get_arrangement()`, `get_session()` |
| Transitions | `set_automation`, `remove_notes` | `get_automation` |
| Sound design | `load_device`, `set_parameters` | `get_devices(include_params=true)` |
