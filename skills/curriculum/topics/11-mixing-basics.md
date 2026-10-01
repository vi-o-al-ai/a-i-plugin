# 11 · Mixing basics

**Goal.** A balanced rough mix: faders set with headroom (0.85 ≈ 0 dB), EQ Eight low cuts and one mud cut, a bus mindset (drum group, returns), and a mono low end. The user can read a fader in dB and say what a high-pass does.

**Prerequisites.** A skeleton with 5–7 tracks (09), sidechain and returns (08).

**Terms.** Gain staging, headroom, high-pass / low cut, mud, bus / group, mono low end.

## Fader numbers

`volume` is normalized 0–1: 0.85 ≈ 0 dB, 1.0 = +6 dB, 0.0 = −∞. The curve is not linear in dB, so set a value, read `display` back from `get_track`, and adjust. Rough anchors to start from (verify by read-back): ~0.75 ≈ −5 dB, ~0.65 ≈ −10 dB, ~0.55 ≈ −15 dB. Never push a track above 0.85 to make it louder; turn the others down.

Starting balance (then adjust by ear): Drums 0.85 (0 dB) · Sub 0.80 · Bass 0.75 · Pad 0.60 · Arp 0.65 · Lead 0.72 · FX 0.60 · Returns 0.85 · Master 0.85.

## Plan (15–20 min)

1. **Show me · read the levels (2 min).** `get_session()`; list every track's `volume.display`, `pan.display`, `mute`, `solo`. Clear stray solos (`set_track(solo=false)`). Set the Master to 0.85 if it is not, why="Master at 0 dB; loudness comes from the mix, not the master fader".
2. **Show me · gain staging (3 min).** Apply the starting balance with `set_track(track, volume=...)`, reading `display` back after each, why on each ("Pad 10 dB under the drums so the kick leads"). Play the chorus/drop scene; ask the user to watch the Master meter: peaks should stay below the red (clipping). If it hits red, lower everything by the same amount. Point at the Mixer section.
3. **Show me · high-pass everything but kick and sub (4 min).** For Pad, Arp, Lead, FX: `load_device(name="EQ Eight")` if absent; `get_devices(..., include_params=true)`; set band 1's filter type to the low-cut item from `value_items`, frequency 120–200 Hz (pads/arps) or 150–250 Hz (lead, FX), why="Everything that is not kick or sub leaves the low end". A/B on the Pad with the kick and sub playing: "Does the low end feel cleaner?"
4. **Show me · one mud cut (2 min).** On the Pad's EQ Eight, band 2 bell at ~300 Hz, gain −3 dB, Q ~1, why="Pads pile up around 300 Hz; a small cut makes room for the bass". A/B on/off with `set_device_enabled`.
5. **Show me · mono low end (2 min).** `load_device(name="Utility", track=<Sub>)`; set "Bass Mono" on and "Bass Freq" ~120 Hz (read names first), why="Sub in mono so it hits the same on every speaker". Same on the Bass track at 150 Hz if it is wide.
6. **Let me try · a drum bus (4 min, UI-only).** Task: "In Session View, click the Drums track name, Cmd/Ctrl-click any other percussion tracks, press Cmd/Ctrl+G. Live makes a Group track; name it 'DRUMS'. Drag a Glue Compressor (Audio Effects) onto the group." Verify `get_session()`: a track with `type: "group"`/`is_foldable: true`, drums with `is_grouped: true`; `get_devices` on the group shows Glue Compressor. Claude then sets Ratio 2:1, Attack 10 ms, Release 0.2 s, Threshold until the needle moves ~2 dB (user reports), why="Glue on the drum bus makes the kit one instrument". Feedback right / change / why. Note that group creation moved track indexes: re-read `get_session()` before further tool calls.
7. **Recap and journal (1 min).**

## Exercise (Let me try)

Pan the Arp 20 % left and the Lead 15 % right by hand (drag the pan dials), leaving kick, snare, sub, bass and vocals centred. Verify `get_track().pan.value` ≈ −0.2 and 0.15; drums/bass within ±0.05.

## Verification

- No track `volume.value` > 0.85; Master 0.85; `solo` false everywhere; the user confirms no red on the Master meter in the loudest section.
- EQ Eight with a low cut on every non-bass melodic track; none on kick/sub.
- Utility with Bass Mono on the Sub.
- Group track exists with drums inside and Glue Compressor on it.
- Returns: Reverb has its own low cut (from 08).

## Recap

- Headroom first: Master at 0 dB, tracks under it, loudest element leads, nothing in the red.
- High-pass what is not bass; make one small cut where pads pile up.
- Think in buses: drums as one, returns as shared space; keep the sub mono.

## Go deeper

[12-finishing.md](12-finishing.md). Reference listening: play a track in the user's genre at the same volume and compare bass level and brightness; Claude cannot hear it, the user reports and Claude adjusts.
