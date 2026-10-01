# 08 · Sidechain and space

**Goal.** Pads that duck to the kick (sidechain compression), shared Reverb and Delay on return tracks fed by sends, and the dry/wet idea. The user routes the sidechain themselves because the tools cannot.

**Prerequisites.** 02 or 03 (a kick), 05/06 (a pad or chords track).

**Terms.** Compressor (threshold, ratio, attack, release), sidechain, return track, send, dry/wet, pre/post.

## Plan (15–20 min)

1. **Show me · returns (3 min).** `get_session(include_returns=true)`. If fewer than two returns: `create_return_track(name="A Reverb")`, `create_return_track(name="B Delay")`. `load_device(name="Reverb", track=0, track_type="return")`; `load_device(name="Delay", track=1, track_type="return")`. Read params; set Reverb "Dry/Wet" 100 %, "Decay Time" 2.5–3.5 s (synth-pop) or 4–6 s (dubstep breakdown); Delay "Dry/Wet" 100 %, sync on, 1/8 dotted (synth-pop) or 1/8 (riddim), feedback ~35 %, why="Returns are 100 % wet; the send knob decides how much". `select(track=0, track_type="return", show_device_detail=true)`.
2. **Show me · sends A/B (2 min).** `set_track(track=<Pad>, sends=[{index:0, value:0.0}])`, play 4 bars; then `value: 0.35`, why="A/B: dry pad vs pad with shared reverb". Point at the send knob under the pan in the Mixer section. Say why returns beat per-track reverb: one space, many instruments, one knob to mix it.
3. **Show me · a compressor on the pad (3 min).** `load_device(name="Compressor", track=<Pad>)`. Read params; set Ratio ~4:1, Threshold −20 to −25 dB, Attack 1 ms, Release 150 ms (120 BPM) or 100 ms (140 BPM), why="Fast attack, release that recovers before the next kick". Explain in one line each: threshold = when it starts, ratio = how much, attack = how fast it grabs, release = how fast it lets go.
4. **Let me try · route the sidechain (4 min, required).** Task: "In Device View on the Pad track, click the small ▸ at the far left of the Compressor's title bar to unfold the Sidechain section. Turn on **Sidechain**. In **Audio From**, choose the Drums track; in the second chooser pick the Kick pad (or 'Post Mixer' if there is no kick entry). Tell me when it's set." Verify: `get_devices(track, device_path=<comp>, include_params=true)` → a parameter like "S/C On" showing on, if exposed; ask the user to confirm "Drums" is in the Audio From box. Then `fire_scene` with pad + drums and ask them to watch the orange gain-reduction meter dip on every kick. Feedback: right / change / why ("the compressor now listens to the kick instead of the pad, so the pad gets out of the kick's way").
5. **Show me · tune the pump A/B (3 min).** Release 50 ms vs 250 ms, why="Short release = tight tick; long release = the classic pump; too long and it never recovers". At 120 BPM a beat is 500 ms, so release + attack must sit well under that. Then Threshold until the dip is obvious; ask them to describe it; keep what they like.
6. **Show me · reverb and the low end (2 min).** `load_device(name="EQ Eight", track=0, track_type="return")` so it sits after Reverb on the return; low cut ~200 Hz, why="Reverb below 200 Hz turns to mud; the return never carries lows". Check with `get_devices(track=0, track_type="return")` that the order is Reverb then EQ Eight.
7. **Recap and journal (1 min).**

## Dubstep variant (mention, build if time)

A "ghost kick" track: `create_midi_track(name="Ghost Kick")`, a kick pattern on 1 and 3 (or 1 only), its fader at 0.0 (`set_track(volume=0.0)`), used only as the Audio From source (Pre FX). Pads and bass pump without an audible kick. The user picks it in Audio From exactly as above.

## Exercise (Let me try)

Add a Compressor to the Bass track and sidechain it to the same kick, but with a lower ratio (2:1) and shorter release (80 ms), so the bass dips but does not pump. Verify params by read-back; ask them to confirm Audio From.

## Verification

- Return A: Reverb at 100 % wet, decay in range, EQ Eight low cut after it; Return B: Delay 100 % wet, synced.
- Pad track: sends[0] 0.2–0.4; Compressor after the instrument; Ratio ≥ 3:1, Attack ≤ 5 ms, Release 80–250 ms; "S/C On" on if exposed; user confirmed the source.
- Drums and Sub tracks: sends 0.0, no compressor sidechained to themselves.

## Recap

- Sidechain = the compressor listens to the kick and turns the pad down on every hit; release decides the pump.
- Reverb and Delay live on returns at 100 % wet; each track's send decides how much space it gets.
- Keep lows out of reverb; keep sub and kick dry.

## Go deeper

[11-mixing-basics.md](11-mixing-basics.md) for levels and EQ; [10-transitions-and-automation.md](10-transitions-and-automation.md) to automate sends for risers and washes; Glue Compressor on a drum group (needs the UI to group).
