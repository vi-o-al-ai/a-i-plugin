# Compressor (`Compressor2`)

Turns loud parts down. Two jobs here: **sidechain pumping** (a pad or bass ducks on every kick)
and **control** (even out a bass, add punch to drums).

Load: `load_device(name="Compressor", track=i, category="audio_effects")`.

## Parameters

| LOM name | UI | What it does | Start |
|---|---|---|---|
| `Threshold` | Thresh | Level above which gain reduction starts (dB) | −20 dB; pumping −28 dB |
| `Ratio` | Ratio | How hard: 2:1 gentle, 4:1 firm, 8:1+ pumping | 4:1 |
| `Expansion Ratio` | Ratio (Expand model) | Only when `Model` = Expand | — |
| `Model` | Peak / RMS / Expand | Peak reacts to transients (drums, sidechain), RMS to loudness (bass, pads) | Peak for sidechain |
| `Attack` | Attack (ms) | How fast it clamps. Fast = kills transients; 10–30 ms lets the punch through | sidechain 0.1–1 ms; drums 10–30 ms |
| `Release` | Release (ms) | How fast it recovers. This *is* the pump | pump 150–250 ms @120; 80–120 ms @140 half-time |
| `Auto Release On/Off` | Auto | Program-dependent release | Off for sidechain |
| `Knee` | Knee (dB) | Soft onset of compression | 6 dB |
| `LookAhead` | Lookahead (0/1/10 ms) | Catches transients before they hit | 1 ms |
| `Env Mode` | Lin/Log | Envelope curve | default |
| `Makeup` | Makeup (auto) | Auto make-up gain switch | Off for sidechain |
| `Output Gain` | Out | Manual make-up | 0 dB |
| `Dry/Wet` | Dry/Wet | Parallel compression | 100 %; drums 50–70 % |

Sidechain section: `S/C On`, `S/C Gain`, `S/C Mix` (external vs internal signal), `S/C Listen`,
`S/C EQ On`, `S/C EQ Type`, `S/C EQ Freq`, `S/C EQ Gain` / `S/C EQ Q`.
**Not settable in v1**: the "Audio From" source (track/chain and Pre/Post FX). Tell the user exactly:
"Open the Compressor, click the ▸ at the left to show the Sidechain section, switch *Audio From* on,
choose **Drums** → **Kick** (Post FX)". Then you set everything else.

`Attack`/`Release` `value` are normally in ms (check `min`/`max`); `Threshold` display is dB — use
`normalized` and read back, or `value` if `min`/`max` are in dB.

## Release timing to tempo

Beat length = `60000 / BPM` ms. 120 BPM: 500 ms; 124: 484 ms; 140: 429 ms.
Pump release ≈ 1/3–1/2 of the kick spacing so the signal is back just before the next kick.
Four-on-the-floor at 120 → 150–250 ms. In half-time dubstep the main kick is 4 beats (1.7 s) apart and extra kicks are rare → short release (80–120 ms)
and a *dip*, not a pump; the groove there comes from the bass rhythm, not the ducking.

## Recipes

### Sidechain pump for a pad (synth-pop/house)
1. `load_device(name="Compressor", track=pad)`; user sets Audio From → kick.
2. ```
   S/C On On; Model Peak; Threshold ≈ −28 dB; Ratio 6:1; Attack 0.5 ms; Release 180 ms (120 BPM)
   Knee 6 dB; LookAhead 1 ms; Makeup Off; Output Gain 0 dB; Dry/Wet 100 %
   ```
3. `play`; ask: "Do you hear the pad breathing with the kick?" Too much → raise Threshold; too subtle → lower it or raise Ratio.
4. For bass, same settings but Release 120–150 ms so the bass returns faster.

Why: ducking the pad on every kick makes the kick feel bigger without turning it up, and the
recovery between kicks is the dance-music "pump".

### Dubstep sub: glue, no pump
```
Model RMS; Threshold ≈ −12 dB; Ratio 2:1; Attack 10 ms; Release 100 ms; Knee 6 dB; Makeup On
```
Why: the sub must be constant; 2–3 dB of gentle reduction keeps every note the same weight.

### Drum bus punch
```
Model Peak; Threshold ≈ −18 dB; Ratio 4:1; Attack 20 ms; Release 80 ms; Dry/Wet 60 %
```
Why: the slow attack lets the transient through, the fast release pulls the body up — parallel mix keeps it natural.

### Even out a synth bass
```
Model RMS; Threshold ≈ −16 dB; Ratio 3:1; Attack 5 ms; Auto Release On; Makeup On
```

## Verify
After `set_parameters`, read `display` for `Threshold`, `Attack`, `Release`; make sure `S/C On`
reads "On" when sidechaining. If the pad is not ducking, the routing (by hand) is the first suspect.
