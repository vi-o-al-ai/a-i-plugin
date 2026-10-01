# Delay (`Delay`)

The plain, clean delay: left/right lines in 16ths or ms, ping-pong, feedback, a filter and light
modulation. Use when you want repeats without character; use Echo for triplets, ducking and dub.

Load: `load_device(name="Delay", track=i, category="audio_effects")`.

## Parameters

| LOM name | What it does | Start |
|---|---|---|
| `L Sync`, `R Sync` | Tempo sync on/off | On |
| `L 16th`, `R 16th` | Delay in 16th notes (1–16): 2 = 1/8, 3 = dotted 1/8, 4 = 1/4, 6 = dotted 1/4, 8 = 1/2 | 3 |
| `L Time`, `R Time` | ms when unsynced | — |
| `L Offset`, `R Offset` | ± % shift of the synced time — stereo drift or "lazy" feel | R +3 % |
| `Link` | Right follows left | On (Off for L 3 / R 4 patterns) |
| `Ping Pong` | Alternate L/R | On for leads |
| `Delay Mode` | `Repitch` / `Fade` / `Jump` — what happens when time changes | Fade (clean) · Repitch (tape) |
| `Feedback` | Repeats | 25–40 % |
| `Freeze` | Hold the buffer forever | Off; automate for stutters |
| `Filter On`, `Filter Freq`, `Filter Width` | Band-pass in the feedback loop | On, ≈ 1 kHz, width 5 |
| `Mod Freq` (newer: `LFO Freq`) | Modulation rate | 0.3 Hz |
| `Filter < Mod` (newer: `LFO > Filter`) | LFO → filter | 10 % |
| `Dly < Mod` (newer: `LFO > Delay`) | LFO → delay time — chorus-like | 3 % |
| `Dry/Wet` | Mix | 20 % |

Triplets are not possible in 16th units — use Echo (`L Sync Mode` Triplet) or set `L Sync` Off
and `L Time` = `60000 / BPM / 1.5` ms for a quarter triplet (e.g. 286 ms at 140 BPM).

## Recipes

### Stab / lead ping-pong (synth-pop)
```
L Sync On, L 16th 3; Link On; Ping Pong On; Feedback 30 %; Filter On ≈ 1.2 kHz, Width 6; Dry/Wet 20 %
```
Why: dotted-8th ping-pong fills the stereo field between hits without adding mud.

### Dubstep one-shot "throw" (automated)
```
L 16th 4 (1/4); Ping Pong On; Feedback 55 %; Delay Mode Repitch; Filter ≈ 800 Hz
Dry/Wet 0 %; set_automation Dry/Wet to 70 % for one beat before the drop (mode "steps"), back to 0
```

### Slapback for vocals/claps
```
L Sync Off; L Time 90 ms; R Time 110 ms; Link Off; Ping Pong Off; Feedback 5 %; Dry/Wet 15 %
```

### Polyrhythmic L/R
```
Link Off; L 16th 3; R 16th 4; Ping Pong Off; Feedback 35 %; Dry/Wet 25 %
```
Why: 3 against 4 creates a rolling pattern that implies 16ths without writing them.

## Verify
Confirm whether modulation names are `Mod Freq`/`Filter < Mod`/`Dly < Mod` or `LFO Freq`/`LFO > Filter`/`LFO > Delay`
in your build; both sets exist across Live 12 versions.
