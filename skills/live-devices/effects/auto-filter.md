# Auto Filter (`AutoFilter`)

A filter with an LFO and an envelope follower. Fully API-controllable — so it is the reliable
way to get a **wobble** (synth matrices are by hand) and the obvious device for a **build-up sweep**.

Load: `load_device(name="Auto Filter", track=i, category="audio_effects")`.
Newer Live 12 builds may report class `AutoFilter2` with different names (`Filter Morph`, `Formant`,
`Control`, `LFO Wave`, `LFO T Mode`, `LFO Freq`/`LFO Time`/`LFO 16th`, `Dry/Wet`, DJ/Vowel filter types).
If so, map by meaning and read back.

## Parameters

| LOM name | What it does | Start |
|---|---|---|
| `Filter Type` | `Lowpass` / `Highpass` / `Bandpass` / `Notch` / `Morph` (quantized) | Lowpass |
| `Frequency` | Cutoff | wobble base ≈ 250 Hz; sweep 200 Hz → 18 kHz |
| `Resonance` | Peak at cutoff — "wetness" | 25–35 % wobble; 10 % sweep |
| `Filter Circuit - LP/HP` | `Clean` / `OSR` / `MS2` / `SMP` / `PRD` — analog models with drive and character | OSR for bass |
| `Filter Circuit - BP/NO/Morph` | Circuit for the other types | Clean |
| `Drive` | Input drive for the analog circuits | 3–6 dB bass |
| `Morph` | Position when type = Morph | — |
| `Slope` | `12` / `24` dB | 24 |
| `Env. Modulation` | Envelope follower depth (±) — auto-wah | 0; wah +40 % |
| `Env. Attack`, `Env. Release` | Follower speed | 5 ms / 200 ms |
| `LFO Amount` | Depth of LFO on cutoff | 60–90 % wobble |
| `LFO Waveform` | Sine / Triangle / Saw Up / Saw Down / Square / S&H variants (read `value_items`) | Triangle (smooth) · Saw Down (riddim "yoi") · Square (chop) |
| `LFO Sync` | `Free` / `Sync` | Sync |
| `LFO Frequency` | Hz when Free | — |
| `LFO Sync Rate` | Division when Sync (`1/4`, `1/8`, `1/8T`, `1/16` …) | 1/8 or 1/8T |
| `LFO Offset` | Phase offset of the synced LFO relative to the beat | 0 |
| `LFO Phase` / `LFO Spin`, `LFO Stereo Mode` | Stereo LFO relationship (phase or spin) | Phase 0 for mono bass |
| `LFO Quantize On`, `LFO Quantize Rate` | Steps the LFO | Off |
| `S/C On`, `S/C Mix`, `S/C Gain` | External sidechain into the envelope follower (routing by hand) | Off |

No dry/wet on the classic Auto Filter — it is always 100 % wet; use a Utility or a rack for parallel.

## Recipes

### LFO wobble on a bass (riddim)
```
Filter Type Lowpass; Slope 24; Filter Circuit - LP/HP OSR; Drive 4 dB
Frequency ≈ 250 Hz; Resonance 30 %
LFO Amount 80 %; LFO Sync Sync; LFO Sync Rate 1/8 (straight) or 1/8T (triplet bounce); LFO Waveform Triangle; LFO Offset 0; LFO Phase 0
```
Why: the LFO opens and closes the filter in time, so a held note gets the rhythm. Automate
`LFO Sync Rate` per bar (`set_automation`, mode `"steps"`: 1/4 → 1/8 → 1/16 → 1/8T) for the
classic rate-switching wobble. Put it after distortion for a cleaner wobble, before it for a nastier one.

### Build-up sweep over 4 bars (16 beats)
1. Read `Frequency`'s `min`/`max`/`value`.
2. `set_automation(track, slot, device_path, parameter="Frequency", points=[{"time":0.0,"value":<≈200 Hz>},{"time":16.0,"value":<≈16 kHz>}], mode="ramp")`
   — use `value` units from the read (`min`/`max`), not Hz, unless the read shows Hz.
3. `Resonance` 15 %; type Lowpass. For a "thinning" build use Highpass rising 30 Hz → 2 kHz instead.
Why: opening a low-pass is the sound of energy arriving; a rising high-pass is tension leaving the floor.

### Rhythmic chop (trance-gate feel)
```
Lowpass 24; Frequency ≈ 400 Hz; Resonance 10 %; LFO Waveform Square; LFO Sync Rate 1/16; LFO Amount 100 %
```

### Auto-wah / envelope follower on a pluck
```
Bandpass; Frequency ≈ 500 Hz; Resonance 40 %; Env. Modulation +50 %; Env. Attack 3 ms; Env. Release 180 ms; LFO Amount 0
```

## Verify
Confirm `LFO Sync` reads "Sync" and `LFO Sync Rate` display is the division you meant; for
`AutoFilter2`, read the names and map `LFO Wave`/`LFO T Mode` accordingly.
