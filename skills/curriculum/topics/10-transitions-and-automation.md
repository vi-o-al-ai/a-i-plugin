# 10 · Transitions and automation

**Goal.** Join sections with risers, filter sweeps, drum fills and the silent beat before a drop, using clip-envelope automation written with `set_automation`. The user can draw one envelope by hand and explain why a drop needs a gap before it.

**Prerequisites.** 09 (a skeleton with scenes), 06 (filter), 08 (sends) helpful.

**Terms.** Automation / clip envelope, ramp vs steps, riser, sweep, fill, impact, the gap.

## How `set_automation` works here

Session clip envelopes: `set_automation(track, slot, device_path, parameter, points=[{time, value}], mode="ramp"|"steps")`. `time` is beats inside the clip; `value` is in the parameter's own units (read `min`/`max` with `get_devices(..., include_params=true)` first; quantized parameters take the `value_items` index). `device_path="mixer"` reaches "Volume", "Pan", "Send A", "Send B". The last point holds to the clip end. Envelopes travel with the clip when it is placed into the Arrangement with `add_clip_to_arrangement`. Check with `get_automation`.

## Plan (15–20 min)

1. **Show me · filter sweep into the chorus (4 min).** On the Pad track's Pre-Chorus clip (8 bars = 32 beats; `duplicate_clip_loop` until `loop_end: 32.0` if shorter), ensure an Auto Filter follows the instrument (`load_device(name="Auto Filter")` if needed; low-pass, resonance ~20 %). `set_automation(track, slot, device_path=<auto filter>, parameter="Frequency", points=[{time:0, value:<~300 Hz>}, {time:32, value:<~12 kHz>}], mode="ramp", why="Opening the filter over 8 bars pulls the ear toward the chorus")`. `select(track, slot, show_clip_detail=true)` and point at the Envelopes box with Auto Filter → Frequency chosen. `fire_scene(<pre>)` and listen. `get_automation` to confirm.
2. **Show me · riser (4 min).** `create_midi_track(name="FX")`, `set_track(color_index=11)`, `load_device(name="Drift")` (saw; or Operator with "Osc-A Wave" set to a noise item from `value_items` if the user has Suite). `create_clip(slot=<pre>, length=32.0, name="Riser 8 bars")`; one note MIDI 55, start 0, duration 32. `load_device(name="Auto Filter")` low-pass; automation: Frequency 200 Hz → 10 kHz ramp over 32; mixer "Send A" 0.1 → 0.6 ramp; mixer "Volume" 0.5 → 0.8 ramp, why="A riser rises in brightness, space and level at once". Play with the pads.
3. **Show me · the drum fill (3 min).** `duplicate_clip` the drum clip into the pre-chorus/build scene as "Drums build". Last bar: `remove_notes(from_time=12.0, time_span=4.0)` then `add_notes` a 16th snare roll 12.0–15.75 with velocities 70 → 127 (riddim: triplets 12.0–13.667 then 16ths), why="A roll with rising velocity is the turn signal before the next section".
4. **Show me · the gap and the impact (3 min).** Riddim: `remove_notes(from_time=15.0, time_span=1.0)` on the build drums and bass so the last beat is silent, why="Silence before the drop makes the drop twice as loud". Synth-pop: keep the kick but drop everything else for the last beat (remove hats and clap at 15.0–15.75). Then in the chorus/drop drum clip `add_notes` a crash (pad 49 if `has_chain`) at 0.0 velocity 120, why="Impact on the downbeat of the drop". A/B with and without the gap.
5. **Let me try · draw a send envelope (4 min).** Task: "Open the Chorus pad clip in Clip View. In the Envelopes box choose 'Mixer' in the first chooser and 'Send A' in the second. Press B, then draw a line that starts low at bar 1 and rises to about three-quarters by bar 4, so the reverb swells across the last bars before the drop/bridge." Verify `get_automation(track, slot, device_path="mixer", parameter="Send A")` → `exists`, first value < last value. Feedback right / change / why.
6. **Show me · reverse the sweep for the bridge (1 min).** `set_automation` Frequency 12 kHz → 400 Hz ramp on the Bridge pad clip, why="Closing the filter drops the energy without stopping the music". Recap and journal.

## Exercise (Let me try)

Automate the Wobble's Auto Filter "LFO Sync Rate" by hand (Envelopes → Auto Filter → LFO Sync Rate, steps every half bar: 1/4, 1/8, 1/8T, 1/16) in a copy of the drop bass clip; Claude verifies four distinct values with `get_automation(resolution=0.5)`.

## Verification

- Pre-chorus/build pad: Frequency envelope `exists`, first point low, last point high; drums build clip ends with a roll of ascending velocities; last beat before the drop has no drum notes (riddim).
- FX riser: a single long note; Frequency, Send A and Volume envelopes all rising.
- Drop/chorus drums: crash at 0.0 on a pad with `has_chain: true`.
- Bridge pad: Frequency envelope falling.
- No parameter shows `automation_state: "overridden"` (if it does, click Re-enable Automation in the Control Bar).

## Recap

- A transition is add-add-add then a gap: open a filter, raise a send, roll the snare, go silent for one beat, hit the downbeat.
- `set_automation` writes clip envelopes: ramps for sweeps, steps for rhythm; they travel with the clip into the Arrangement.
- Drops are loud because the moment before them is quiet.

## Go deeper

[11-mixing-basics.md](11-mixing-basics.md); [12-finishing.md](12-finishing.md). Reverse reverb and sub-drop FX are Simpler/audio tricks the user does in the UI; Claude can set up the tracks and verify.
