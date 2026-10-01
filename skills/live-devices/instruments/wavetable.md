# Wavetable (`InstrumentVector`)

Two wavetable oscillators that *scan* through a table (the Position knob is the sound), a sub
oscillator, two filters with routing, three envelopes, two LFOs and a modulation matrix. The
go-to for modern pads, plucks and dubstep bass.

Load: `load_device(name="Wavetable", track=i, category="instruments")`.
Names below are LOM `parameter.name` (Live 12.0–12.4 definitions). UI labels differ (UI
"Position" = `Osc 1 Pos`, UI "Transpose" = `Osc 1 Transp`). Read the list first.

## Oscillators 1 and 2 (`Osc 1 …`, `Osc 2 …`)

| LOM name | UI | What it does | Start |
|---|---|---|---|
| `Osc 1 On` | On | Oscillator enable | On |
| `Osc 1 Category` | category menu | Which wavetable family (quantized; `value_items` lists them) | Basic Shapes for clean; Complex/Formant/Distortion for bass |
| `Osc 1 Table` | wavetable menu | The table inside the category (quantized) | read `value_items` |
| `Osc 1 Pos` | Position | Scans through the table: *the* timbre control, and the classic wobble target | 0–0.3 pads; modulate for bass |
| `Osc 1 Transp` | Transpose | Semitones | 0; `-12` for bass weight |
| `Osc 1 Detune` | Detune | Cents; detune Osc 2 against Osc 1 for width | Osc 2: 5–12 ct |
| `Osc 1 Pitch` | (combined pitch) | Also present in newer builds — verify which one your Live exposes | — |
| `Osc 1 Gain` | Gain | Oscillator level | 0 dB |
| `Osc 1 Pan` | Pan | Per-osc pan; opposite pans = instant width | ±20 for pads |
| `Osc 1 Effect Type` | effect mode | `None` / `FM` / `Classic` / `Modern` (quantized) | FM for growl, Classic for PWM |
| `Osc 1 Effect 1` | FM: Tune · Classic: Pulse Width · Modern: Warp | First effect control; meaning depends on mode | — |
| `Osc 1 Effect 2` | FM: Amount · Classic: Sync · Modern: Fold | Second effect control | FM Amount 20–50 % for growl |

## Sub (`Sub …`)

`Sub Gain` (level, the clean low end), `Sub Tone` (sine → brighter), `Sub Transpose` (octave:
−1 for bass). Sub on/off is a UI switch; if no `Sub On` parameter appears, set `Sub Gain` to minimum.

## Filters 1 and 2 (`Filter 1 …`, `Filter 2 …`)

| LOM name | What it does | Start |
|---|---|---|
| `Filter 1 On` | Enable | On |
| `Filter 1 Type` | `Lowpass` / `Highpass` / `Bandpass` / `Notch` / `Morph` (quantized) | Lowpass |
| `Filter 1 Freq` | Cutoff — brightness | pads ≈ 1–3 kHz, bass ≈ 200–500 Hz |
| `Filter 1 Res` | Resonance — peak at cutoff; the "wet" in wobbles | 10–30 % |
| `Filter 1 Drive` | Pre-filter drive (not with Morph) | 0–6 dB bass |
| `Filter 1 Morph` | Morph position when Type = Morph | — |
| `Filter 1 Slope` | `12` / `24` dB (quantized) | 24 for bass |
| `Filter 1 LP/HP` | Circuit: `Clean` / `OSR` / `MS2` / `SMP` / `PRD` (LP/HP types) | OSR or MS2 for grit |
| `Filter 1 BP/NO/Morph` | Circuit for the other types | Clean |
| `Filter Routing` | `Serial` / `Parallel` / `Split` (quantized) | Serial |

## Envelopes

`Amp Attack`, `Amp Decay`, `Amp Sustain`, `Amp Release`, slopes `Amp A Slope` / `Amp D Slope` /
`Amp R Slope`, `Amp Loop Mode`. Same for `Env 2 …` and `Env 3 …` (with `Env 2 Loop Mode`, `Env 3 Loop Mode`).
Amp = loudness shape. Env 2/3 only do something once routed in the matrix (by hand).

| Sound | Attack | Decay | Sustain | Release |
|---|---|---|---|---|
| Pad | 400–900 ms | 1 s | 80 % | 1.5–3 s |
| Pluck/arp | 0–2 ms | 250–400 ms | 0 | 150–300 ms |
| Bass | 0–5 ms | 300 ms | 70–100 % | 80–150 ms |

## LFOs (`LFO 1 …`, `LFO 2 …`)

`LFO 1 Shape` (Sine/Triangle/Saw Up/Saw Down/Square/Random…; read `value_items`), `LFO 1 Shaping`
(skew), `LFO 1 Sync` (`Free` / `Tempo`), `LFO 1 Rate` (Hz when Free), `LFO 1 S. Rate` (division when
Tempo, e.g. `1/8`, `1/8T`), `LFO 1 Amount` (global depth), `LFO 1 Attack Time` (fade-in),
`LFO 1 Phase Offset`, `LFO 1 Retrigger` (restart per note: on for bass wobbles, off for pads).

## Modulation matrix

Routings (LFO 1 → `Osc 1 Pos`, Env 2 → `Filter 1 Freq`, …) are **not plain parameters in v1**.
Tell the user: "In Wavetable's Matrix tab, find the row for *Osc 1 Pos* and type 40 in the *LFO 1*
column". Real parameters that scale everything: `Global Mod Amount` (0–100 % of all matrix depths —
automate this for drops) and `Time` (scales all envelope/LFO times). Pushes expose per-source
amounts (`Lfo 1 Mod Amount`, `Env 2 Mod Amount`, `MIDI Velocity Mod Amount`…); if they appear in
your parameter list they act on the *currently selected* target only — verify by read-back.

## Global

`Mono On` (mono/legato; bass = On), `Poly Voices` (polyphony), `Glide` (portamento time, mono only),
`Unison Mode` (`None`/`Classic`/`Shimmer`/`Noise`/`Phase Sync`/`Position Spread`/`Random Note` — verify
`value_items`), `Unison Voices` (2–8), `Unison Amount` (spread), `Transpose`, `Volume`.

## Recipes

### 80s poly pad (synth-pop)
```
Osc 1 Category/Table: Basic Shapes (saw-ish); Osc 1 Pos 0.15
Osc 2 On; same table; Osc 2 Detune +8 ct; Osc 2 Pan −25, Osc 1 Pan +25
Sub Gain −inf (pads do not need sub)
Unison Mode Classic; Unison Voices 4; Unison Amount 35 %
Filter 1 Lowpass 24, Freq ≈ 1.8 kHz, Res 10 %
Amp Attack 600 ms, Decay 1 s, Sustain 85 %, Release 2 s
LFO 1 Sync Free, Rate 0.15 Hz, Amount 100 %, Retrigger Off → (by hand) Osc 1 Pos +15, Filter 1 Freq +10
After: Chorus-Ensemble, Compressor sidechained to kick, Reverb send
```
Why: detune + unison = chorus-like width; slow attack lets the kick breathe; slow LFO keeps a long chord alive.

### Plucky arp lead
```
Osc 1: Basic Shapes, square or saw table, Pos 0.2; Osc 2 Off
Mono On Off (poly); Unison None
Filter 1 Lowpass 24, Freq ≈ 1.2 kHz, Res 20 %
Amp Attack 0 ms, Decay 300 ms, Sustain 0, Release 200 ms
Env 2 Attack 0, Decay 250 ms, Sustain 0 → (by hand) Env 2 → Filter 1 Freq +40
After: Echo (dotted 1/8, ducked), light Saturator
```
Why: zero sustain = every note is a pluck; a filter envelope gives the "tick" at the start.

### Riddim wobble bass (LFO → position and filter)
```
Osc 1 Category Complex or Formant (harmonically rich table); Osc 1 Transp −12; Osc 1 Pos 0.4
Osc 1 Effect Type FM; Effect 2 (Amount) 25 % for growl edge (optional)
Sub Gain −3 dB, Sub Transpose −1  (or keep the sub on its own Operator track and set Sub Gain −inf)
Mono On On; Glide 60 ms; Unison None
Filter 1 Lowpass 24, circuit OSR, Freq ≈ 300 Hz, Res 28 %, Drive 4 dB
Amp Attack 0, Decay 200 ms, Sustain 100 %, Release 90 ms
LFO 1 Sync Tempo; S. Rate 1/8 (straight) or 1/8T (riddim triplet); Shape Triangle or Saw Down; Amount 100 %; Retrigger On
(by hand) Matrix: LFO 1 → Osc 1 Pos +45, LFO 1 → Filter 1 Freq +55
Automate Global Mod Amount or LFO 1 S. Rate per bar (1/4 → 1/8 → 1/16) for the classic rate-switch wobble
After: Roar or Saturator → OTT (Multiband Dynamics) → Utility Bass Mono
```
Why: the LFO sweeps the table and the filter together, so tone *and* brightness pulse on the beat;
retrigger makes each MIDI note restart the wobble so the rhythm in `midi-writing/bass.md` stays legible.

### Clean sub
```
Osc 1 Off; Osc 2 Off; Sub Gain 0 dB, Sub Tone 0, Sub Transpose 0 (write notes at 24–40, typically 28–40)
Mono On; Glide 30 ms; Filter 1 Off
Amp Attack 3 ms, Decay 0, Sustain 100 %, Release 120 ms
```
Why: a sub is a sine with a volume envelope; anything else is a different instrument's job.

## Verify
After loading, `get_devices(..., include_params=true)` and confirm `Osc 1 Pos`, `Filter 1 Freq`,
`LFO 1 S. Rate` exist; if the list shows `Osc 1 Pitch` without `Osc 1 Transp`, use `Osc 1 Pitch`.
