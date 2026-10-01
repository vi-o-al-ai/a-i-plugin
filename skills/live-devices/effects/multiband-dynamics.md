# Multiband Dynamics (`MultibandDynamics`)

Three bands (Low / Mid / High), each with **Above** (loud parts) and **Below** (quiet parts)
processing. Upward compression of the quiet parts plus downward compression of the loud parts
in every band = the "OTT" sound: dense, bright, aggressive. Dubstep bass and drums live on it;
synth-pop uses it lightly for sheen.

Load: `load_device(name="Multiband Dynamics", track=i, category="audio_effects")`.
Live ships an **"OTT"** preset for this device — try `browse(query="OTT", categories=["audio_effects"])`
and `load_device(uri=...)` first; then tune `Amount`.

## Parameters (per band: `(Low)`, `(Mid)`, `(High)`)

| LOM name | What it does | Start |
|---|---|---|
| `Band Activator (Low)` | Band on/off | On |
| `Input Gain (Low)` | Drive into the band | 0 dB |
| `Above Threshold (Low)` / `Above Ratio (Low)` | Loud material above this level is compressed (ratio > 1:1) or expanded (< 1:1) | −25 dB / 3:1 |
| `Below Threshold (Low)` / `Below Ratio (Low)` | Quiet material below this level is lifted (ratio < 1:1, upward compression) or pushed down (> 1:1, gating) | −40 dB / lift |
| `Attack Time (Low)` / `Release Time (Low)` | Speed per band | 1 ms / 100 ms (OTT-ish) |
| `Output Gain (Low)` | Band make-up | to taste |
| `Low-Mid Crossover`, `Mid-High Crossover` | Band split frequencies | 120 Hz / 2.5 kHz |
| `Amount` | Global depth of all compression (0–100 %) — the one knob to automate | 40–60 % |
| `Master Output` | Output trim | compensate |
| `Time Scaling` | Scales all attack/release times | 100 % |
| `Peak/RMS Mode` | Detection | RMS for bass, Peak for drums |
| `Soft Knee On/Off` | Softer onset | On |
| `S/C On`, `S/C Mix`, `S/C Gain` | External sidechain (routing by hand) | Off |

Read `display` to see how Live prints the Below ratios before you set them; set ratios with
`normalized` plus read-back, or `value` once you have seen the units.

## Recipes

### OTT-style squash for dubstep bass or drums
1. Try the preset: `browse(query="OTT", categories=["audio_effects"])` → `load_device(uri=...)`.
2. Then `Amount` 40–60 % (100 % is a lot), `Time Scaling` 100 %, `Master Output` −3 to −6 dB.
3. No preset? Approximate by hand (tune by ear):
   ```
   All bands: Above Threshold ≈ −30 dB, Above Ratio ≈ 3:1; Below Threshold ≈ −45 dB, Below Ratio lifting (≈ 1:3 upward)
   Attack 1 ms, Release 120 ms on all bands; Low-Mid Crossover ≈ 120 Hz; Mid-High ≈ 2.5 kHz
   Amount 50 %; Soft Knee On; Peak/RMS RMS
   ```
Why: every band is brought to the same loudness, so the quiet harmonics of a growl become as
loud as its fundamental — that is the modern "in your face" bass texture. Put it **after**
distortion and **before** Utility Bass Mono; never on the sub track.

### Tame a harsh lead (de-harsh)
```
Only High band active (others off); Mid-High Crossover ≈ 3 kHz; Above Threshold ≈ −24 dB; Above Ratio 4:1; Attack 0.5 ms; Release 60 ms; Amount 100 %
```

### Consistent sub without pumping
```
Only Low band active; Low-Mid Crossover ≈ 150 Hz; Above Threshold ≈ −14 dB; Above Ratio 3:1; Attack 10 ms; Release 150 ms; Peak/RMS RMS
```

### Synth-pop master sheen (light)
```
OTT preset; Amount 15–20 %; Master Output −2 dB
```
Why: a little upward compression adds air and detail without the aggression.

## Verify
Confirm band names include the `(Low)`/`(Mid)`/`(High)` suffix exactly; confirm `Amount`'s display after setting.
