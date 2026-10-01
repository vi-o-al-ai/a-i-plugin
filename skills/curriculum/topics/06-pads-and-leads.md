# 06 · Pads and leads

**Goal.** The user can explain the four building blocks of a subtractive synth (oscillator, filter, envelope, LFO), build a lush pad and a bright lead on a stock Live synth, and add an arpeggio with the Arpeggiator MIDI effect.

**Prerequisites.** 05 (a chord clip to play through the pad); 01.

**Terms.** Oscillator, waveform, filter cutoff, resonance, ADSR envelope, LFO, detune/unison, arpeggiator.

## Parameter names are read, not guessed

Before any `set_parameter`, call `get_devices(track, device_path="0", include_params=true)` and use the `name` strings it returns. Likely names (verify):

| Device | Oscillator | Filter | Amp envelope | LFO | Notes |
|---|---|---|---|---|---|
| Drift (all editions) | "Osc 1 Shape", "Osc 1 Oct", "Osc 2 Gain" (no on/off switch: raise the gain), "Osc 2 Detune" | "LP Freq", "LP Res" ("LP Reso" in Live 12.0 — use what the read shows), "LP Type" | "Env 1 Attack/Decay/Sustain/Release" | "LFO Rate", "LFO Amt", "LFO Wave" | Mod routing is partly fixed ("LP Mod Amt 2" is the LFO → filter depth); "Voice Mode" for mono/poly. |
| Wavetable (Suite) | "Osc 1 Pos", "Osc 1 Transp", "Osc 1 Gain", "Osc 2 On" | "Filter 1 Freq", "Filter 1 Res", "Filter 1 Type" | "Amp Attack/Decay/Sustain/Release" | "LFO 1 Rate", "LFO 1 Amount", "LFO 1 Shape" | Mod-matrix routing is UI-only (Let me try). Wavetable selection is UI-only. |
| Analog (Suite) | "OSC1 Shape", "OSC1 Octave", "OSC2 Detune" | "F1 Freq", "F1 Resonance" | "AEG1 Attack/Decay/Sustain", "AEG1 Rel" | "LFO1 Speed", "LFO1 Shape" | Two full voices; good for detuned pads. |
| Operator (Suite) | "Osc-A Wave", "A Coarse", "Osc-B Level" | "Filter Freq", "Filter Res" | "Ae Attack/Decay/Sustain/Release" | "LFO Rate", "LFO Amt" | FM; see 07. |

If a device fails to load, the edition lacks it: use Drift and say so.

## Recipes (set, then read `display` back)

| | Pad (lush) | Lead (bright) | Arp pluck |
|---|---|---|---|
| Oscillator | saw; osc 2 on, detuned ~10–15 cents, or unison/"Drift" up | saw or pulse, osc 2 one octave up at low level | saw or triangle |
| Filter | low-pass 800 Hz–1.5 kHz, resonance 10–15 % | low-pass 4–8 kHz, resonance 10 % | low-pass 2 kHz, envelope-modulated if available |
| Amp envelope | attack 300–800 ms, decay 1 s, sustain 80 %, release 1.5–2.5 s | attack 1–5 ms, decay 300 ms, sustain 70 %, release 200 ms | attack 0, decay 200–300 ms, sustain 0, release 100 ms |
| LFO | 0.1–0.3 Hz to filter, small amount | vibrato 5 Hz to pitch, tiny amount, or none | none |
| Voice | poly | mono with glide if exposed | poly |

## Plan (15–20 min)

1. **Show me · four blocks (3 min).** `select(track=<Chords>, device_path="0", show_device_detail=true)`. With the default Drift playing the chord clip: name the four sections on screen. One sentence each: oscillator = the raw tone; filter = how bright; envelope = the shape over time; LFO = the wobble.
2. **Show me · filter A/B (2 min).** `set_parameter(track=<Chords>, device_path="0", parameter="LP Freq", normalized=<low, e.g. 0.3>)` → play → `normalized=<high, e.g. 0.8>`, why="A/B: cutoff decides bright vs dark". Use `normalized` (0–1 of the parameter's range) rather than guessing Hz; quote `display` back.
3. **Show me · the pad bloom A/B (3 min).** Attack 5 ms vs 500 ms, why="Slow attack makes a pad bloom instead of stab". Then release 100 ms vs 2 s. Ask what changed between chords.
4. **Show me · width (2 min).** Turn on osc 2 and detune, or raise the unison/drift amount, why="Two slightly out-of-tune oscillators make the pad wide". A/B on/off.
5. **Let me try · LFO to filter (4 min).** Task (Drift): "Find the LFO section; set Rate to about 0.2 Hz and point the LFO at the filter cutoff (LP Freq) in the modulation section (the small matrix below the envelopes), amount about 20 %." Task (Wavetable): "Open the Matrix tab on the right; in the LFO 1 row, click under 'Filter 1 Freq' and drag up to about 20." Verify what can be read (`LFO Rate`, `LFO Amt`, `LP Mod Amt 2` if present) and ask them to describe whether the pad now slowly breathes. Be explicit: Claude can set the LFO rate but not the routing in Wavetable.
6. **Show me · lead (3 min).** `create_midi_track(name="Lead")`, `set_track(color_index=3)`, `load_device(name="Drift")` or Analog; apply the lead recipe. `create_clip(slot=0, length=16.0)`, a simple 4-bar hook on chord tones (D major example: 74 74 76 78 | 81 78 76 | 74 71 74 | 76 … durations 0.5–1.0, mostly stepwise), why="A hook that lands on chord tones at bar starts". `select(show_clip_detail=true)`, play with chords.
7. **Show me · arpeggio (2 min).** `create_midi_track(name="Arp")`, `load_device(name="Arpeggiator", track)` then `load_device(name="Drift", track)`; confirm with `get_devices` that Arpeggiator is at `"0"` and Drift at `"1"` (MIDI effect before instrument). Set Arpeggiator "Rate" to 1/16 (via `display` from `value_items`) and "Style" Up. `duplicate_clip` the chord clip onto this track (`target_track`), why="Same chords through an arpeggiator become the 16th-note sparkle". Recap and journal.

## Exercise (Let me try)

Make the lead brighter in the chorus: set the filter cutoff (`LP Freq` on Drift) by ear to where the hook cuts through the pad, then tell Claude the value; Claude reads `display` back and asks them to explain why the lead should be brighter than the pad (answer: separation).

## Verification

- Pad: attack ≥ 300 ms, release ≥ 1.5 s, cutoff ≤ 1.5 kHz, osc 2 on or unison up (`display` strings).
- Lead: attack ≤ 10 ms, cutoff ≥ 4 kHz; clip notes in key, range ≤ 1.5 octaves, mostly steps.
- Arp track: Arpeggiator before the instrument; Rate 1/16; its clip equals the chord clip's notes.

## Recap

- Oscillator → filter → amplifier envelope, with an LFO moving something slowly: that is every synth.
- Pads: slow attack, long release, dark filter, detune. Leads: instant attack, open filter, mono.
- An arpeggiator turns a chord clip into motion without writing new notes.

## Go deeper

[07-wobble-and-growl-bass.md](07-wobble-and-growl-bass.md) applies the LFO idea to bass; [08-sidechain-and-space.md](08-sidechain-and-space.md) gives the pad room; the `live-devices` skill (if present) lists more parameter names.
