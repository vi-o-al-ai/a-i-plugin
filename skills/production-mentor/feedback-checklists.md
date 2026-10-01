# Read-back checklists

Use these after a Let-me-try step, in `/ableton-live:review`, and after Claude's own Show-me steps. Read first, judge second. Report as **what's right / what to change / why**, at most two changes at a time.

Units: times in beats (1 bar in 4/4 = 4.0; beat 1 = 0.0, beat 2 = 1.0, "and of 2" = 1.5, a 16th = 0.25, an eighth-triplet = 0.333…). Pitches are MIDI numbers; Live labels 60 as C3. Volumes are normalized 0–1 with 0.85 ≈ 0 dB.

## Drums

Read: `get_notes(track, slot)`; pad names from `get_devices(track, device_path="0")` → `drum_pads` (`note`, `name`, `has_chain`). Clip length from `get_clip` or `notes.clip_length`.

Four-on-the-floor (synth-pop / disco, 110–125 BPM), per bar:
- Kick (usually 36) at 0.0, 1.0, 2.0, 3.0. Velocities 110–127, even.
- Snare or clap (38 / 39) at 1.0 and 3.0. Velocity 100–120.
- Closed hat (42): straight 8ths (every 0.5) or offbeats only (0.5, 1.5, 2.5, 3.5). Offbeats are the disco feel. Velocity 70–100, accents on the offbeat for bounce or on the downbeat for drive; variation of ±15 is good.
- Open hat (46) optional on 3.5 or on every offbeat at lower velocity. If open and closed hat share an offset, the open hat should be alone or choked (Drum Rack choke group — UI).
- 4-bar clips: bars 1–3 near-identical, bar 4 has a variation (dropped kick on 3.5–4.0, snare fill, open hat).

Half-time (riddim / dubstep, 140 BPM), per bar:
- Kick at 0.0 only, velocity 120–127. At most one extra kick per two bars (1.5 or 3.5 in bars 2 or 4). No kick at 2.0.
- Snare (38, often layered with clap 39) at 2.0 only. Nothing on 1.0 or 3.0.
- Hats: on beats 2 and 4 (1.0, 3.0), or on the offbeats (0.5, 1.5, 2.5, 3.5), or straight 8ths at 70–90, or triplets (0.333 steps) on beats 2 and 4 only — any of these passes; very sparse is fine. Space is the point.
- Bar 4 (or 8): snare roll into the next phrase (3.0, 3.25, 3.5, 3.75 or 3.0, 3.333, 3.667) with velocities rising 80 → 120.

Always check:
- Each pitch used is a pad with `has_chain: true`. A note on an empty pad is silent.
- No note `start >= clip_length` (never plays) and no duplicate (same pitch, same start).
- Starts on the grid: multiples of 0.25, or of 0.333 for triplets, within ±0.02 unless swing was intended (`quantize_notes` with `swing`).
- Drum durations short (≤ 0.5); long durations are harmless for one-shots but hide the grid visually.

Feedback template: "Right: kick on all four beats, clap on 2 and 4. Change: the hats are on the beats, move them to the offbeats (select the F#1 row, drag right by one 8th). Why: on the beat they double the kick; between the beats they create the bounce."

## Chords

Read: `get_notes(track, slot)`; key from `get_session()` → `scale.root_note`, `scale.scale_intervals`.

- In key: `(pitch - root_note) % 12` is in `scale_intervals` for every note. Allowed exceptions: a deliberate borrowed chord the user named.
- Chord shape: 3–4 notes starting at the same time. Adjacent voices ≥ 3 semitones apart; no two notes 1 semitone apart below MIDI 60.
- Register: chord tones between MIDI 48 and 79 for pads; leads above 67; nothing below 48 in a chord track (that is the bass's job).
- Durations fill the slot (4.0 for one chord per bar) or are deliberately short stabs (≤ 0.5) on a rhythm; not an accidental 0.9 of a bar.
- Harmonic rhythm: changes on bar lines (every 4.0) or every 2 bars; a progression of 4 chords over 4 bars is the default.
- Voice leading: between consecutive chords, each voice moves ≤ 4 semitones and common tones stay. If every voice jumps the same way, suggest an inversion.
- Progression names, for feedback: compute scale degrees of the roots and name them (I–V–vi–IV in major; i–VI–III–VII in minor).

## Bass (sub and mid)

Read: `get_notes(track, slot)`; chord roots from the chord clip; kick positions from the drum clip.

- Monophonic: sort by start; for each note, `start + duration <= next.start` (allow 0.01). Overlaps smear the sub.
- Register: sub MIDI 24–40 (Live labels C0–E1; roughly 33–82 Hz), typically 28–40. Mid bass MIDI 36–55. Flag a sub note below 24 or above 40.
- In key, as for chords. Roots on chord changes: the note starting at each chord's start time should be the chord root (or 5th by intent).
- Rhythm against the kick. Synth-pop: notes on the kicks (0, 1, 2, 3) or on the offbeats between them (0.5, 1.5…); the octave pop on 3.5 is idiomatic. Riddim: triplet groups (0, 0.333, 0.667), rests around the snare at 2.0 or a hit exactly with it; a 2-bar call then a 2-bar response.
- Sub and mid bass on separate tracks play the same pitch class, sub one octave lower; the mid bass has a high-pass (EQ Eight Low Cut ~80–100 Hz).
- Note length: sub notes often slightly short of the next (duration 0.9 × gap) so each attack is clean; a legato sub is fine if the instrument is mono.

## Melody and lead

- In key; range ≤ 1.5 octaves within one phrase; mostly steps (≤ 2 semitones) with one or two leaps that resolve by step.
- Rhythm has a repeating 1- or 2-bar motif; a 4-bar hook repeats with one change in bar 4.
- Lands on chord tones at bar starts; passing notes between.
- Not fighting the bass rhythm: lead notes mostly where the bass rests, or longer.

## Devices and parameters

Read: `get_devices(track, include_params=true)` (chain), `get_devices(track, device_path, include_params=true)` (one device, with `parameters`, `chains`, `drum_pads`).

- Order: MIDI effects (Arpeggiator, Scale, Chord) before the instrument; audio effects after it. Within audio effects: Utility/EQ → dynamics (Compressor, OTT) → saturation/distortion → modulation → time effects (reverb, delay) last. Reverb/Delay usually on returns, not on the track.
- Exactly one instrument per track unless inside an Instrument Rack (`is_rack`).
- `is_active: true` on every device meant to be heard; a bypassed device shows `is_active: false`.
- Parameter values: compare the `display` string to the target ("1.20 kHz", "-18.0 dB", "4.00 : 1"). For quantized parameters read `value_items` and quote the chosen item. When a value was `clamped: true` in a set result, say so.
- Mono for bass: look for a parameter named like "Voices", "Voice Mode", "Polyphony", "Mono" and check its `display`; if none is exposed, ask the user to confirm the voice mode in the UI.
- Not settable through parameters (user does it in the UI; verify by asking): sidechain Audio From, Wavetable's modulation matrix, wavetable/sample selection, Operator algorithm picture (the "Algorithm" parameter usually exists; the picture is the UI), Drum Rack choke groups, rack macro mappings.

## Mixer

Read: `get_track(track)` → `volume.value/display`, `pan`, `sends`, `mute`, `solo`; `get_session()` for all tracks, returns and master.

- Track volumes ≤ 0.85 (0 dB); a typical starting balance has drums and bass loudest, pads and FX 6–12 dB under. Read `display` to speak in dB.
- Master volume at 0.85; it is not a loudness knob.
- Pan: kick, snare, sub, bass centred (`pan.value` within ±0.05). Pads, arps and hats may be spread.
- Sends: 0.0 on drums and sub unless intended; pads and leads 0.2–0.4 to reverb; delay sends lower.
- `mute`/`solo` all false at the end of a lesson; a left-on solo is the most common "why can't I hear anything".
- Returns carry Reverb/Delay at 100 % wet.

## Clips, scenes and arrangement

Read: `get_clip`, `get_session()` → `scenes`, `get_arrangement()`.

- Clip `loop_end - loop_start` is a whole number of bars (4.0, 8.0, 16.0); `looping: true` for session loops.
- Scenes named for sections (Intro, Verse, Chorus…) in order; no empty scene between used ones unless intended.
- Arrangement: locator `time` values are multiples of 4.0 and ascending; each section has the planned clips with `start_time` equal to the section start and no gaps between repeated placements (`end_time` of one = `start_time` of the next); `song_length` matches the plan within a bar.
- Remind: session clips override the arrangement until "Back to Arrangement" is clicked.

## Automation

Read: `get_automation(track, slot, device_path, parameter)` → `exists`, `points`.

- `exists: true`; first and last point values match the intent (riser: low → high; a drop: high value held then a step down at the drop).
- Direction and span: a filter sweep that moves 200 Hz → 8 kHz over 8 bars has points at time 0 and 32.
- `automation_state` on the parameter: `playing` means the envelope is live; `overridden` means someone touched the knob and the envelope is bypassed until Re-enable Automation (the orange button in the Control Bar) is clicked.
