# Worked outlines at Skeleton level

Two generic skeletons, described as "typical of the style". They make no claims about any specific song; use them when the user wants to study a track in one of these lanes and Claude's song-specific memory is low, or as the default shape before the user corrects bar counts by listening. Tool sequences follow `fidelity-levels.md` Level 1.

Colour indexes are approximate Live palette positions; check the returned `color` hex.

## A · Empire of the Sun-style synth-pop (120 BPM, D major, 108 bars ≈ 3:36)

Typical traits: four-on-the-floor with offbeat hats, octave-bounce synth bass over a sine sub, major four-chord loop, lush sidechained pad, 16th-note arp, bright lead hook that only appears in choruses, big lift via a pre-chorus whose chords change twice as fast.

| Scene idx | Scene / locator name | Bars | Locator time (beats) | Time | Roles with placeholder clips (length in beats) | Energy |
|---|---|---|---|---|---|---|
| 0 | Intro | 1–8 | 0 | 0:00 | Chords (32), Arp (32), FX (32); Drums hats-only from bar 5 (one 16-beat clip at 16) | 3 |
| 1 | Verse 1 | 9–24 | 32 | 0:16 | Drums (64), Sub (64), Bass (64), Chords (64), Vocal/Hook placeholder (64) | 5 |
| 2 | Pre 1 | 25–32 | 96 | 0:48 | Drums (32), Bass (32), Chords double-rate (32), FX riser (32), Vocal (32) | 6 |
| 3 | Chorus 1 | 33–48 | 128 | 1:04 | Drums+open hats (64), Sub (64), Bass (64), Chords (64), Arp (64), Lead (64), Vocal (64) | 9 |
| 4 | Verse 2 | 49–56 | 192 | 1:36 | Drums (32), Sub (32), Bass (32), Chords (32), Arp counter (32), Vocal (32) | 6 |
| 5 | Pre 2 | 57–64 | 224 | 1:52 | as Pre 1 + Drums roll variation (32) | 7 |
| 6 | Chorus 2 | 65–80 | 256 | 2:08 | as Chorus 1 + Lead harmony (64) | 9 |
| 7 | Bridge | 81–88 | 320 | 2:40 | Chords (32), Arp (32), FX sweep down/up (32); no Drums/Bass | 4 |
| 8 | Final Chorus | 89–104 | 352 | 2:56 | everything, Lead +12 in bars 97–104 (64) | 10 |
| 9 | Outro | 105–108 | 416 | 3:28 | Chords (16), Arp (16), FX (16) | 2 |
| — | End | — | 432 | 3:36 | locator only | — |

Key calls: `set_transport(tempo=120)`, `set_scale(root_note="D", scale_name="Major")`. Role tracks and colours: Drums 14, Sub 1, Bass 15, Chords 9, Arp 7, Lead 3, Vocal/Hook placeholder 5, FX 11.

Locators: `set_locator(time=t, name=n)` for each row above, then `set_locator(time=432, name="End")`.

Placeholders: for each row, `create_clip(track=<role>, slot=<scene idx>, length=<beats>, name="<Role> – <Section>")`, `set_clip(... color_index=<role colour>)`, `add_clip_to_arrangement(track, slot=<scene idx>, time=<locator time>)`. The Intro drums placeholder is 16 beats placed at 16 (bar 5).

Brief notes to pre-fill (all "reconstructed from the style"): chords Verse I–V–vi–IV (D–A–Bm–G), Pre IV–V ×4 at two per bar, Chorus I–V–vi–IV with the bass moving to IV at bar 41 for lift, Bridge vi–IV–vi–IV; hook rhythm a 2-bar phrase repeated with a bar-4 change; what to listen for: when the clap first appears, whether hats are on the beat or off it, the pad "breathing" with the kick, what disappears in the bridge.

Follow-ups: `/ableton-live:lesson 02-drums-four-on-the-floor`, `/ableton-live:lesson 05-chords-and-keys`, `/ableton-live:lesson 08-sidechain-and-space`.

## B · Subtronics-style riddim (140 BPM, F minor, 124 bars ≈ 3:33)

Typical traits: half-time drums (kick 1, snare 3), two bass characters trading 2-bar phrases (wobble call, growl answer) over a clean sine sub, mostly on the root with moves to the minor third and flat seventh, a melodic breakdown with pads, builds that end in a snare roll and a silent beat, a second drop that re-arranges the first.

| Scene idx | Scene / locator name | Bars | Locator time (beats) | Time | Roles with placeholder clips (length in beats) | Energy |
|---|---|---|---|---|---|---|
| 0 | Intro | 1–16 | 0 | 0:00 | Pad drone (64), FX stabs (64), Drums hats-only (64), Sub hint bars 13–16 (16 at 48) | 3 |
| 1 | Build 1 | 17–32 | 64 | 0:27 | Drums snare-on-3 (64), FX riser (64), Pad (64); last beat silent | 6→8 |
| 2 | Drop 1 A | 33–48 | 128 | 0:55 | Drums (64), Sub (64), Wobble (64), Growl (64), FX lasers (64) | 10 |
| 3 | Drop 1 B | 49–64 | 192 | 1:22 | Drums variation (64), Sub (64), Wobble switch-up (64), Growl (64) | 10 |
| 4 | Breakdown | 65–80 | 256 | 1:50 | Pad progression (64), Pluck melody (64), Drums soft from bar 73 (32 at 288), Vocal placeholder (64) | 4 |
| 5 | Build 2 | 81–88 | 320 | 2:17 | Drums roll (32), FX riser (32), Pad (32); last beat silent | 8 |
| 6 | Drop 2 A | 89–104 | 352 | 2:31 | Drums (64), Sub (64), Growl leads (64), Wobble answers (64), FX (64) | 10 |
| 7 | Drop 2 B | 105–120 | 416 | 2:58 | Drums double-time hats bars 117–120 (64), Sub (64), Wobble (64), Growl (64) | 10 |
| 8 | Outro | 121–124 | 480 | 3:26 | Sub tail (16), Pad (16), FX hit (16) | 2 |
| — | End | — | 496 | 3:33 | locator only | — |

Key calls: `set_transport(tempo=140)`, `set_scale(root_note="F", scale_name="Minor")`. Role tracks and colours: Drums 14, Sub 1, Wobble 15, Growl 12, Pad 9, Pluck 7, Vocal placeholder 5, FX 11.

Locators: one per row plus `set_locator(time=496, name="End")`. Placeholders as in A; the Breakdown drums placeholder is 32 beats placed at 288 (bar 73); the Intro sub hint is 16 beats at 48 (bar 13).

Brief notes to pre-fill (all "reconstructed from the style"): Intro and drops on i (F) with bass moving to bIII (Ab) and bVII (Eb) at phrase ends; Breakdown i–VI–III–VII (Fm–Db–Ab–Eb) one per bar; drop bass rhythm = eighth-note triplet cells, bar 1 call (wobble, LFO 1/8T), bar 2 answer (growl stabs), sub on phrase roots only; what to listen for: the snare landing on 3, how little the kick plays, the exact beat the drop goes silent before, which bass sound "talks" first, what the second drop changes.

Follow-ups: `/ableton-live:lesson 03-drums-half-time-140`, `/ableton-live:lesson 07-wobble-and-growl-bass`, `/ableton-live:lesson 10-transitions-and-automation`.

## Using these as a starting point for a real song

1. Present the matching outline as "a typical shape for this style".
2. Ask the user to listen to the actual song once with a timer and call out where each section starts (mm:ss). Convert: bars = seconds × BPM / 240 for 4/4 at that BPM. Adjust the table.
3. Lay out the corrected table with Level 1 calls, then write the brief with the user's timings marked "user-timed" (high confidence) and everything else "reconstructed".
