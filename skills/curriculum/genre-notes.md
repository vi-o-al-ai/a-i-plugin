# Genre notes

Conventions, not rules. Use these for defaults when a lesson or study needs a stylistic choice. Both summaries describe the style in general; they do not state facts about any specific song and never include lyrics. "Empire of the Sun-style" and "Subtronics-style" mean "typical of records in that lane", reconstructed from genre knowledge.

## Synth-pop / indie dance (Empire of the Sun-style)

| Aspect | Convention |
|---|---|
| Tempo | 115–125 BPM, 4/4. 120 is the safe default; 118 feels laid back, 124 feels like a club edit. |
| Drums | Four-on-the-floor kick (every beat), clap or snare on 2 and 4 (often clap layered with a soft snare), closed hats on offbeat 8ths for the disco bounce or straight 8ths/16ths for drive, open hat on the "and" of 4 or every offbeat in choruses, occasional tom fills and reversed cymbals into choruses. Drum sounds: 808/909-style electronic kits, bright claps, sometimes a live-sounding kit layered in. Intros often start with hats or percussion only. |
| Bass | Mid-register synth bass (MIDI 36–50), saw or pulse through a low-pass filter, sometimes a slight pluck envelope. Rhythms: octave bounce (root, root+12 on the offbeat), 8th-note pulses on the kick, or disco walking lines. A clean sine sub under it in the choruses. Mono. Lightly sidechained to the kick. |
| Harmony | Major keys, or relative-minor verses resolving to major choruses. Four-chord loops: I–V–vi–IV, vi–IV–I–V, I–vi–IV–V, IV–I–V–vi. One chord per bar; pre-choruses often double the rate (two per bar) to lift. Add9 and sus2 colours on pads; 7ths sparingly. Choruses frequently move the bass to the IV or vi to "open up". |
| Sound palette | Bright analog-style leads (saw with a little detune, short attack, filter mostly open, light chorus), plucky arpeggios in 8ths or 16ths (Arpeggiator → Drift/Analog pluck, delay on a send), lush pads (slow attack, detuned saws, chorus, long reverb, sidechained so they breathe), layered vocals with heavy reverb and delay, occasional guitar-like plucks, shimmering FX (risers, reverse reverb, white-noise sweeps). Everything glossy and wide except kick, sub and lead vocal. |
| Arrangement | Intro 8 → Verse 16 → Pre 8 → Chorus 16 → Verse 8–16 → Pre 8 → Chorus 16 → Bridge/breakdown 8 → Final chorus 16 → Outro 4–8. Energy rises into each chorus and drops hard at the bridge. Choruses add the lead hook, open hats and a wider stereo image; verses strip the lead and often the clap. See `templates/synth-pop-structure.md`. |
| Mixing habits | Kick and bass centred and tight; pads and arps wide; sidechain pump audible but musical (release lands before the next kick); long reverbs on returns, kept out of the low end with a high-pass on the return; vocals bright and forward; master not crushed, the energy comes from arrangement contrast. |
| What to borrow | The feeling of lift into choruses: pre-chorus harmonic rhythm doubles, a riser plus snare build, then the chorus lands with everything plus one new element (hook lead or open hats). |

## Riddim / dubstep (Subtronics-style)

| Aspect | Convention |
|---|---|
| Tempo | 140 BPM, 4/4, felt as half-time (70 BPM pulse). Some tracks sit at 145–150; 140 is the default. |
| Drums | Kick on beat 1, snare on beat 3 (the half-time backbeat), very sparse extra kicks (the "and" of 2 or 4 once per two bars), snare usually layered (acoustic crack + clap + short noise), hats on 8ths or triplets, often quiet; percussion fills and snare rolls (16ths or triplets, rising velocity) at the end of 8- and 16-bar phrases. Drums are loud, short and dry; the snare is the loudest element after the sub. |
| Bass | Two layers: a clean sine sub (MIDI 24–40, typically 28–40, mono, no effects, carries the fundamental) and the "mid" or "growl" bass (MIDI 40–55, high-passed around 80–100 Hz) that carries character. Riddim rhythms are repetitive, bouncy, triplet-heavy (eighth-note triplets, quarter-note triplets, dotted patterns), often two-bar phrases with the second bar as a response (different sound or pitch). Pitches move little: root, minor third, fifth, flat seventh; the groove and sound changes carry interest. Wobbles: tempo-synced LFO on a filter cutoff at 1/4, 1/8, 1/8T, 1/16 with rate changes per bar. Growls: FM, wavetable position movement, formant-like filters, heavy saturation, OTT, resampling and re-processing. |
| Harmony | Minor keys (F minor, E minor, G minor, A minor are common). Often just the root as a drone plus a two-chord movement (i–VI, i–VII, i–iv) in intros and breakdowns. Drops are frequently monophonic: bass against the root. Melodic breakdowns use i–VI–III–VII or i–VII–VI pads and plucks. |
| Sound palette | Growl/wobble/"screech" basses, metallic and vocal-formant textures, laser and zap FX, risers (noise + pitch), impacts and sub drops at the drop, vocal chops and shouts as rhythmic elements, orchestral or synth pads in breakdowns, sparse arps. Humour and call-and-response between two bass sounds is characteristic of riddim. |
| Arrangement | Intro 16 → Build 16 → Drop 32 (16 + 16 with a switch-up) → Breakdown 16 → Build 8 → Drop 32 → Outro 4–8. Builds end with a snare roll, a riser and a silent last beat (or a vocal shout) before the drop. Second drops reuse the first drop's material with new bass patterns or sounds. See `templates/riddim-dubstep-structure.md`. |
| Mixing habits | Sub in mono, alone below ~90 Hz; mid bass high-passed and often mono below 200 Hz; kick short so it does not fight the sub (or sidechained to it); snare loud and centred; drops very loud relative to breakdowns, often limited hard; OTT and saturation everywhere on the mid bass; reverb mostly on breakdown elements, drops kept dry and tight. |
| What to borrow | Space and contrast: one kick, one snare, one bass phrase that leaves gaps; a second bar that answers the first; the drop hits because the build removed everything first. |

## Shared habits worth teaching

- Phrases of 4, 8 and 16 bars; something changes at every 4-bar boundary, something bigger at every 8.
- One new element per section; one element removed per transition.
- Builds are additive (hats, riser, snare roll, filter opening); drops are subtractive first (silence or kick only) then everything at once.
- Keep the low end to one instrument at a time: kick and sub share it by timing (sidechain) or by range (kick above 60 Hz, sub below).
- Loop early, arrange early: a finished 2:30 sketch beats a perfect 8-bar loop.

## Numbers to reach for

| | Synth-pop 120 BPM | Riddim 140 BPM |
|---|---|---|
| Beat length | 0.5 s | 0.4286 s |
| Bar length | 2.0 s | 1.714 s |
| 16-bar section | 32 s | 27.4 s |
| Sidechain release | 150–250 ms | 80–120 ms |
| Delay sync | 1/8 dotted, 1/4 | 1/8, 1/8T |
| Reverb decay (pads) | 2.5–4 s | 3–6 s (breakdowns only) |
| Sub register | MIDI 24–40 (typically 28–40), an octave under the mid bass | MIDI 24–40 (typically 28–40) |
| Mid bass register | MIDI 36–50 | MIDI 40–55 |
| Lead register | MIDI 67–84 | MIDI 60–79 (breakdown melodies) |
