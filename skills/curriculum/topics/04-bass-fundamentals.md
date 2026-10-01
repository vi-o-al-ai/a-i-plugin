# 04 · Bass fundamentals

**Goal.** Two bass tracks that work together: a clean mono sub in the right register and a mid bass with character, both in key, locked to the kick. The user can say why bass is mono and where the sub lives.

**Prerequisites.** 01; a drum clip from 02 or 03 in slot 0 of a Drums track; a key chosen (`set_scale`) or chosen now.

**Terms.** Sub bass, mid bass, fundamental, monophonic, register, root.

## Registers (MIDI numbers; Live labels 60 as C3)

| Layer | Range | Live labels | Roughly |
|---|---|---|---|
| Sub | 28–40 | E0–E1 | 41–82 Hz: felt more than heard, mono, no effects |
| Mid bass (synth-pop) | 36–50 | C1–D2 | 65–147 Hz: the note you hum |
| Mid/growl bass (riddim) | 40–55 | E1–G2 | high-passed ~80–100 Hz; the sub owns what is below |

Flag any sub note below 24 (inaudible on most systems) or above 43 (no longer "sub").

## Plan (15–20 min)

1. **Show me · key and root (2 min).** Synth-pop: `set_scale(root_note="D", scale_name="Major")`; riddim: `set_scale(root_note="F", scale_name="Minor")`. "The root is home; the bass lives on it most of the time." Sub root: D → MIDI 38 (D1); F → MIDI 29 (F0). If Live rejects the scale name, use the `available` list from the error.
2. **Show me · a sub (4 min).** `create_midi_track(name="Sub")`, `set_track(color_index=1)`. `load_device(name="Operator", track)` (its default is a sine); if unavailable, `load_device(name="Drift")` and set oscillator 1 to sine. `get_devices(track, device_path="0", include_params=true)`; find the voice/polyphony parameter (named like "Voices", "Voice Mode", "Poly") and set it to mono via `display` from its `value_items`; if none is exposed, ask the user to set it in the UI and say why. Short release (~100–150 ms). `create_clip(track, slot=0, length=4.0, name="Sub A")`. Synth-pop: root on every kick, `add_notes` at 0,1,2,3 duration 0.9 pitch 38, velocity 100, why="Sub on every kick: one note, felt not heard". Riddim: root at 0.0 (duration 1.8) and 2.0 (duration 1.8), pitch 29, why="Sub holds under kick and snare, leaving beat 2 and 4 for air". Fire Drums + Sub together (`fire_scene(0)`).
3. **Show me · register A/B (3 min).** `transpose_notes(track, slot=0, semitones=12, why="A/B: same line an octave up")`. Play. "Which one disappears into the kick and which one sits under it?" `undo` back to the low octave. Say: too low and it is inaudible on small speakers; too high and it is no longer sub.
4. **Show me · mono (2 min).** `get_notes(track, slot=0)`; show that each `start + duration ≤ next start`. "Two sub notes at once cancel and smear; the sub is always one voice." Do not demonstrate an overlap by writing one; a read-back that proves there is none teaches the check.
5. **Show me · mid bass (4 min).** `create_midi_track(name="Bass")`, `set_track(color_index=15)`. `load_device(name="Drift")` (or Analog); saw oscillator, low-pass filter ~600–900 Hz, short amp release, mono voice mode. Same roots an octave above the sub: synth-pop pitch 50 (D2) with the octave bounce (50 on the beat, 62 on the offbeat, durations 0.4), why="Octave bounce is the disco bass motor"; riddim pitch 41 with a triplet group at 0, 0.333, 0.667 (durations 0.3), rest, 2.0 with the snare, 3.0, 3.333, 3.667, why="Triplet stabs; the sub keeps the fundamental steady". Then `load_device(name="EQ Eight", track)`, set band 1 to a low cut around 90 Hz (read `value_items` for the filter type name), why="Mid bass hands the lows to the sub".
6. **Let me try · the pickup (3 min).** Task: "In the Bass clip, at the last 8th of bar 1 (ruler 1.4.3), draw one note on the 5th of the key (A for D major: A2 = MIDI 57; C for F minor: C2 = MIDI 48) one 8th long. Make sure it does not overlap the note before it." Verify `get_notes`: a note at 3.5, pitch in key, no overlap. Feedback right / change / why ("a pickup into bar 1 pulls the loop forward").
7. **Recap and journal (1 min).**

## Exercise (Let me try)

Write a second sub pattern in slot 1 that moves to the IV (synth-pop: G1 = 43; riddim: Bb0 = 34) for bar 2 of a 2-bar clip, while bar 1 stays on the root. Claude `duplicate_clip_loop`s first. Verify: roots at bar 2 match, still mono, still in range.

## Verification

- Sub: all pitches 28–43; monophonic; every pitch class in scale; notes on kicks (synth-pop) or on 1 and 3 (riddim).
- Mid bass: pitches 36–55; monophonic; roots agree with the sub an octave up; EQ Eight low cut present after the instrument.
- Both tracks pan centre (`pan.value` ≈ 0) and sends 0.0.

## Recap

- Sub = one sine, mono, MIDI 28–40, on the root, no effects. Mid bass = character an octave up, high-passed.
- Lock the bass to the kick: on it (synth-pop) or around it (riddim).
- In key, on the root at every chord change; move to the 5th or IV for motion.

## Go deeper

[07-wobble-and-growl-bass.md](07-wobble-and-growl-bass.md) builds on the mid bass; [08-sidechain-and-space.md](08-sidechain-and-space.md) makes kick and sub share the low end; [11-mixing-basics.md](11-mixing-basics.md) for mono low end with Utility.
