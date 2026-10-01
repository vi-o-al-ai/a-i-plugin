# 07 · Wobble and growl bass

**Goal.** A riddim bass pair: a tempo-synced wobble (LFO → filter) and a growl (FM or wavetable movement + distortion + OTT), high-passed, over a separate clean sub, arranged as a 2-bar call and a 2-bar response. The user can explain what the LFO is doing and why the sub is separate.

**Prerequisites.** 03 (half-time drums at 140), 04 (sub + mid bass, EQ low cut), 06 (filter, envelope, LFO).

**Terms.** Tempo-synced LFO, wobble, growl, FM, wavetable position, saturation, OTT, resampling, call and response.

## The simplest chain Claude can drive end to end

`Instrument (saw/square, mono, MIDI 40–52) → Auto Filter (LFO) → Saturator → Multiband Dynamics "OTT" → EQ Eight (low cut 80–100 Hz)`

Auto Filter does the wobble on its own, with parameters the tools can set (likely names; verify with `get_devices(..., include_params=true)`): "Filter Type", "Frequency", "Resonance", "LFO Amount", "LFO Waveform", "LFO Sync" (on), "LFO Sync Rate" (quantized: 1/4, 1/8, 1/8T, 1/16 …), "LFO Rate" (free Hz when not synced), "LFO Phase". Wavetable's matrix and Operator's LFO destination are UI-only, so start here.

## Plan (15–20 min)

1. **Show me · the wobble (4 min).** Reuse the Bass track from 04 or `create_midi_track(name="Wobble")`, `set_track(color_index=15)`, `load_device(name="Drift")` with a saw, filter fully open, mono, short release. 2-bar clip (`length=8.0`), root F1 = MIDI 41, long notes: 0.0–1.9, 2.0–3.9, then bar 2 the same, why="Long notes so the LFO, not the notes, makes the rhythm". `load_device(name="Auto Filter", track)`; set low-pass, Frequency ~400 Hz, Resonance ~25 %, LFO Sync on, LFO Sync Rate 1/4, LFO Amount ~70 %, why="Tempo-synced LFO on the cutoff is the wobble". `select(track, device_path="1", show_device_detail=true)`; fire with the drums.
2. **Show me · rate A/B (2 min).** Sync Rate 1/4 → 1/8 → 1/8T → 1/16 (via `display` from `value_items`), playing each, why="Faster LFO = faster wobble; triplets match the riddim swing". Ask which feels like the drums. Keep one.
3. **Show me · rhythm from rate changes (3 min).** `set_automation(track, slot, device_path="1", parameter="LFO Sync Rate", points=[{time:0,value:<idx 1/4>},{time:2,value:<idx 1/8>},{time:4,value:<idx 1/8T>},{time:6,value:<idx 1/16>}], mode="steps", why="Switching the LFO rate every half bar writes the bass rhythm")`. For quantized parameters `value` is the index into `value_items`; read it first. Point at the Envelopes box in Clip View. `get_automation` to confirm `exists`.
4. **Show me · grit (3 min).** `load_device(name="Saturator", track)`: Drive 12–18 dB, type via `value_items` (e.g. "Analog Clip" or "Soft Sine"), why="Saturation adds the harmonics the filter can sweep through". `load_device(name="OTT", track, category="audio_effects")` (the Multiband Dynamics preset; if not found, load "Multiband Dynamics" and raise "Amount" to ~50 %), why="OTT squashes and brightens; the dubstep sound". `load_device(name="EQ Eight", track)` low cut ~90 Hz, why="Hand the lows to the sub". Read the chain back: `get_devices(track)` order Drift, Auto Filter, Saturator, Multiband Dynamics, EQ Eight. Say plainly: "I can't hear whether it growls or just hisses; tell me, and we'll move Drive and LFO Amount."
5. **Show me · growl (3 min).** `create_midi_track(name="Growl")`, `set_track(color_index=12)`. Option A, Operator (Suite): `load_device(name="Operator")`; raise "Osc-B Level", set "Osc-B Coarse" to 2 or 3, then an LFO on Osc B level (destination in UI: Let me try) → FM growl. Option B, Wavetable: pick a formant/vocal wavetable in the UI (Let me try), LFO 1 → "Osc 1 Pos" in the Matrix (UI), Claude sets "LFO 1 Rate" synced to 1/8. Option C, any edition: Drift square → Auto Filter band-pass with high resonance (~60 %) and LFO Sync Rate 1/8T → Saturator Drive 20 dB → OTT. Then the same Saturator/OTT/EQ Eight tail as the wobble. Same clip length; write the response rhythm: triplet stabs 0, 0.333, 0.667 (dur 0.3) on 41 and 44, rest, 2.0 with the snare, bar 2 answering on 48 → 41.
6. **Let me try · call and response (3 min).** Task: "Mute the Growl clip's bar 1 and the Wobble clip's bar 2: in each Clip View select the notes in that bar and press 0 (deactivate) so bar 1 is the wobble's call and bar 2 is the growl's answer." Verify `get_notes` → `mute: true` on the right notes. Feedback: right / change / why ("two voices talking, never at once, is riddim's joke and its groove").
7. **Show me · sub follows (1 min).** On the Sub track, `replace_notes` (ask first if the user wrote it) so sub pitches are the bass pitch classes an octave down (29 for 41, 32 for 44, 36 for 48), one note per bass phrase start, why="The sub tracks the mid bass roots and nothing else". Recap and journal.

## Resampling idea (talk, then UI)

Record the processed bass to audio: `create_audio_track(name="Bass Resample")`; the user sets Audio From → Wobble (Post FX) in the In/Out section, arms, records 2 bars, then chops or reverses the audio in Simpler. Explain why: once it is audio, you can filter, pitch and re-distort it again, which is how layered growls are built. Claude cannot set the routing or record; it can verify the new track exists and later load devices onto it.

## Exercise (Let me try)

Pick a different LFO Waveform in Auto Filter (Square vs Sine vs Saw Down) and a different Sync Rate by ear; tell Claude the choice; Claude reads them back and asks which bar of drums it locks to.

## Verification

- Wobble chain order: instrument → Auto Filter → Saturator → Multiband Dynamics → EQ Eight; all `is_active`.
- Auto Filter: LFO Sync on, LFO Amount > 50 %, Sync Rate one of 1/4, 1/8, 1/8T, 1/16; `get_automation(...,"LFO Sync Rate").exists` true.
- Growl and Wobble clips: never both unmuted in the same bar; pitches in F minor; mid bass 40–55; mono.
- Sub: pitch classes match the bass; 28–40; EQ low cut on both mid-bass tracks, none on the sub.

## Recap

- Wobble = LFO on a filter cutoff, synced to tempo; change the rate to write rhythm.
- Growl = movement inside the oscillator (FM or wavetable position) plus distortion plus OTT.
- Sub is separate and clean; mid basses are high-passed; two basses talk in turns.

## Go deeper

[10-transitions-and-automation.md](10-transitions-and-automation.md) for drops; [11-mixing-basics.md](11-mixing-basics.md) for keeping the low end clean; `genre-notes.md` riddim row for rhythm defaults.
