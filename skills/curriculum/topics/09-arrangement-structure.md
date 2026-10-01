# 09 · Arrangement structure

**Goal.** Turn a set of loops into a song skeleton: named scenes in the order of the song, then the same sections laid on the Arrangement timeline with locators and clips. The user can read a section map in bars and knows the Back to Arrangement button.

**Prerequisites.** At least drums, bass and chords clips in slot 0 of their tracks (02/03, 04, 05). 01 for the beats maths.

**Terms.** Section, phrase (4/8/16 bars), scene, locator, energy curve, Back to Arrangement.

## Section maps (details and tool sequences in the templates)

| Synth-pop 120 BPM (`curriculum/templates/synth-pop-structure.md`) | Riddim 140 BPM (`curriculum/templates/riddim-dubstep-structure.md`) |
|---|---|
| Intro 8 · Verse 16 · Pre 8 · Chorus 16 · Verse 8 · Pre 8 · Chorus 16 · Bridge 8 · Final Chorus 16 · Outro 4 = 108 bars ≈ 3:36 | Intro 16 · Build 16 · Drop 32 · Breakdown 16 · Build 8 · Drop 32 · Outro 4 = 124 bars ≈ 3:33 |

Bar N starts at beat (N − 1) × 4. A section of B bars is B × 4 beats long.

## Plan (15–20 min)

1. **Show me · read the map (2 min).** Open the template for the user's genre. Read the table with them: sections, bar counts, energy 1–10. One sentence: "Every 8 bars something changes; every chorus/drop has one more element than the last."
2. **Show me · scenes as the song (4 min).** `get_session()` for existing scenes. `create_scene(name=...)` / `set_scene(scene, name=..., color_index=...)` in order from the template. Then populate: `duplicate_clip(track, slot=0, target_slot=<scene>)` for each role that plays in each section, and edit variations (`remove_notes` the clap for Verse 1; `transpose_notes` the lead +12 for Final Chorus; empty drums in Intro/Bridge), why on each ("Verse drops the clap so the chorus can bring it back"). `show_view("Session")`; the grid now reads top to bottom as the song.
3. **Show me · play it through (2 min).** `fire_scene(0)`, then each scene after ~8 bars (or let the user click the scene launch buttons). Ask: "Where does the energy jump? Where does it dip?" Adjust one scene by adding or removing a clip.
4. **Show me · locators (3 min).** `show_view("Arranger")`. `set_locator(time, name)` for every section from the template, why="Locators are the song's table of contents". `get_arrangement().locators` to read them back; point at the markers in the Arrangement scrub area.
5. **Show me · clips onto the timeline (4 min).** For each section and role: `add_clip_to_arrangement(track, slot=<scene>, time=<section start>)`, repeated every clip length (`get_clip().length`) until the section is filled: a 16-beat clip in a 64-beat section goes at time, +16, +32, +48. Narrate the first two, then do the rest and summarise. `get_arrangement()` → check `start_time`/`end_time` chain with no gaps. Say the rule: "Session clips still override the Arrangement; click the orange Back to Arrangement button, then press play."
6. **Let me try · one section by hand (3 min).** Task: "Drag the Chorus lead clip from Session into the Lead lane in Arrangement so it starts exactly at the Chorus 2 locator (hold while dragging to snap; the position shows at the top). Then click Back to Arrangement and play from the Chorus 2 locator (click the locator's marker)." Verify `get_arrangement()` → Lead has a clip with `start_time == <Chorus 2 beats>`. Feedback right / change / why ("sections that start on a locator are easy to move later").
7. **Recap and journal (1 min).** Record which template was used and how many sections are laid out.

## Exercise (Let me try)

Make Verse 2 differ from Verse 1 in the Arrangement: delete the Arp clip from Verse 2 (click it, Delete) and extend the Pad clip across the whole verse (drag its right edge). Verify with `get_arrangement()`: Arp absent in bars 49–56, Pad `end_time` at the Pre-Chorus 2 start.

## Verification

- Scenes named and ordered as the template; chorus/drop scenes have the most clips, intro/bridge the fewest.
- Locators at the template's beat positions, ascending, on multiples of 4.0.
- For each role, arrangement clips tile each section with `end_time == next start_time`; no clip crosses a section boundary unless intended.
- `get_transport().song_length` within one bar of the template total.

## Recap

- Phrases of 4, 8 and 16 bars; a section map is a list of bar counts and energy levels.
- Scenes first (one row per section), then locators, then clips on the timeline at the section start times.
- Back to Arrangement before listening to the arrangement.

## Go deeper

[10-transitions-and-automation.md](10-transitions-and-automation.md) joins the sections; [12-finishing.md](12-finishing.md) completes it. `/ableton-live:study` lays out a skeleton of a reference track the same way.
