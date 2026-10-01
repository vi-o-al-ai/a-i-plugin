# Echo (`Echo`)

Live's "big" delay: two synced or free delay lines (Stereo / Ping Pong / Mid-Side), a filter in the
feedback path, modulation, a reverb tail, gating and **ducking** (the echo only appears between
notes), plus noise/wobble for tape character.

Load: `load_device(name="Echo", track=i, category="audio_effects")`.
Note the mix parameter is `Dry Wet` (space, no slash) — unlike every other device.

## Parameters

| LOM name | Section | What it does | Start |
|---|---|---|---|
| `L Sync`, `R Sync` | Echo | Sync to tempo on/off | On |
| `L Sync Mode`, `R Sync Mode` | Echo | `Notes` / `Triplet` / `Dotted` / `16th` | Dotted for lead echo |
| `L Division`, `R Division` | Echo | Note value when synced | 1/8 |
| `L 16th`, `R 16th` | Echo | Length in 16ths when Sync Mode = 16th | 3 = dotted 8th |
| `L Time`, `R Time` | Echo | ms when not synced | — |
| `L Offset`, `R Offset` | Echo | Fine shift (%) — stereo drift | R +5 % |
| `Link` | Echo | Right follows left | On |
| `Channel Mode` | Echo | `Stereo` / `Ping Pong` / `Mid/Side` | Ping Pong (lead) |
| `Feedback` | Echo | Repeats | 30–45 %; dub throws 65 % |
| `Feedback Inv` | Echo | Polarity flip of feedback — hollower | Off |
| `Input Gain`, `Output Gain`, `Clip Dry` | Echo | Gain staging; drive the input for tape grit | 0 / 0 / Off |
| `Stereo Width` | Global | Width of the echo | 100 % |
| `Repitch` | Global | Pitch glide when time changes (tape) vs crossfade | On for dub |
| `Filter On`, `HP Freq`, `HP Res`, `LP Freq`, `LP Res` | Filter | Band-limits repeats so they sit behind the source | HP 300 Hz, LP 5 kHz |
| `Mod Wave`, `Mod Sync`, `Mod Rate` / `Mod Freq`, `Mod Phase`, `Mod 4x` | Modulation | LFO shape/rate | Sine, 0.3 Hz |
| `Dly < Mod`, `Flt < Mod`, `Env Mix` | Modulation | LFO → delay time (chorus/tape wow), → filter; envelope follower blend | Dly 5 %, Flt 10 % |
| `Reverb Level`, `Reverb Loc` (Pre/Post/Tail), `Reverb Decay` | Character | Reverb inside the delay | Level 15 %, Tail |
| `Gate On`, `Gate Thr`, `Gate Release` | Character | Gate the echo input | Off |
| `Duck On`, `Duck Thr`, `Duck Release` | Character | **Ducks repeats while the source plays** | On, −20 dB, 300 ms |
| `Noise On`, `Noise Amt`, `Noise Mrph`, `Wobble On`, `Wobble Amt`, `Wobble Mrph` | Character | Tape hiss / flutter | Wobble 10 % for dub |
| `Dry Wet` | Output | Mix | 20–30 % insert; 100 % on return |

## Recipes

### Synth-pop lead echo (dotted 8th, ducked)
```
L Sync On; L Sync Mode Dotted; L Division 1/8; Link On; Channel Mode Ping Pong
Feedback 38 %; Filter On, HP Freq ≈ 300 Hz, LP Freq ≈ 5 kHz
Duck On, Duck Thr −20 dB, Duck Release 300 ms; Reverb Level 10 %, Reverb Loc Tail
Dry Wet 25 %
```
Why: the dotted-8th repeats fall between the straight 8ths of the melody, filling gaps with
rhythm; ducking keeps the melody clear while it is playing and lets the echoes bloom in the rests.

### Dub throw (dubstep break / vocal)
```
L Sync Mode Notes; L Division 1/4 (or Triplet 1/8 for the riddim feel); Feedback 65 %; Repitch On
Filter HP ≈ 250 Hz, LP ≈ 3.5 kHz; Wobble On 12 %; Noise On 8 %
Dry Wet 0 % normally — automate it to 60 % on the last beat of a phrase (set_automation, mode "steps")
```
Why: a one-beat "throw" sends a single hit into long repeats — the classic transition cue.

### Pad widener
```
Channel Mode Stereo; L Division 1/16, R Division 1/16, R Offset +12 %; Feedback 10 %; Dly < Mod 8 %, Mod Freq 0.25 Hz
Dry Wet 35 %; Filter HP ≈ 400 Hz
```

## Verify
Read `L Sync Mode` `value_items` (the strings for Dotted/Triplet) and confirm `Dry Wet` by name.
If the lead sounds washed out, lower `Feedback` before `Dry Wet`.
