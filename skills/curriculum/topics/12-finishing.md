# 12 · Finishing

**Goal.** Call a track done, run a finishing pass, export a WAV through Live's UI, and understand loudness well enough not to chase it. End with a file on disk and a "Finished track #1" line in the journal.

**Prerequisites.** 09–11: an arranged, roughly mixed track.

**Terms.** Done, finishing pass, limiter and ceiling, export/render, peak vs loudness (LUFS), dither.

## When is it done?

Done means: every section in the map has content; it starts and ends on purpose; a listener can hum the hook; nothing clips. Not done means "not perfect". Rule for this user: finish the track at the planned length, export it, and start the next one; perfection comes from the fourth track, not the fourth month on the first.

## Plan (15–20 min)

1. **Show me · completeness read-back (3 min).** `get_arrangement()`: every locator from the template has clips in the roles the map lists; no accidental empty bars (a role missing for a whole section that should have it); `get_transport().song_length` ≈ the template total. Report as a checklist. `show_view("Arranger")`.
2. **Show me · the finishing pass (4 min).** `get_session()`: `solo` false, `mute` as intended, tracks named, nothing above 0.85, Master at 0.85. Session clips: anything still playing (`playing_slot_index ≥ 0`)? `stop` them so the Arrangement plays; remind about Back to Arrangement. Any `automation_state: "overridden"`? Tell the user to click Re-enable Automation. Remove or deactivate scratch tracks ("Tour", "Grid") only with the user's say-so (`delete_track(confirm=True)` after asking) or `set_track(mute=true)` instead.
3. **Show me · a safety limiter (2 min).** `load_device(name="Limiter", track=0, track_type="master")`; read params; Ceiling −1.0 dB, Gain 0 dB, why="A limiter at −1 dB catches stray peaks; it is a seatbelt, not a loudness tool". Ask the user to play the loudest section and report whether the gain-reduction meter moves more than a little; if it does, lower track levels, not the ceiling.
4. **Show me · loudness, the idea (2 min).** Peak = the tallest spike (what clips). Loudness = how loud it feels over time (measured in LUFS). Streaming services turn tracks down to roughly −14 LUFS, so a crushed master gains nothing there. Beginner target: peaks at −1 dB, a mix that sounds balanced at the same volume as a reference track; leave mastering for later. Claude cannot measure LUFS; a free loudness meter plug-in or Live's meters plus the user's ears is the check.
5. **Let me try · export (5 min, UI-only).** Task: "In Arrangement View press Cmd/Ctrl+A to select everything (the render length follows the selection), then File → Export Audio/Video (Cmd/Ctrl+Shift+R). Set: Rendered Track = Master; Render Start/Length = whole song (check they match the locators); Sample Rate 44100 or 48000; Bit Depth 24 (or 16 with Dither = Triangular); File Type WAV; Normalize Off; Convert to Mono Off; Encode MP3 on if you want a phone copy. Click Export, name it `<title>-v1.wav`, save it where you'll find it. Tell me the path when it's done." Verify: use Glob/Read on the user's path to confirm the file exists and its size is plausible (a 3:30 24-bit stereo 44.1 kHz WAV is ~55 MB). Feedback right / change / why ("Normalize off keeps the level you mixed; 24-bit keeps headroom for later mastering").
6. **Show me · listen outside Live (1 min).** Ask the user to play the export on headphones and a phone speaker and note one thing to fix next time (usually bass level). Write it under Struggles or Next up.
7. **Recap and journal (2 min).** Append "Finished track #1: <title>, <genre>, <length>" to Exercises completed. Next up: the other genre's template from 09, or `/ableton-live:study` on a reference in the same genre.

## Exercise (Let me try)

Save the set with a version name (File → Save Live Set As… `<title>-v1.als`) and, in a copy, bounce a 30-second chorus/drop excerpt (set the Arrangement loop brace around it with Cmd/Ctrl+L and export the loop) to share. Verify the files exist.

## Verification

- `get_arrangement()`: every section populated as planned; `song_length` ≈ template total.
- Master chain: Limiter present, Ceiling ≤ −1 dB; Master volume 0.85.
- No solos; no session clips playing; no overridden automation.
- Exported WAV exists at the path the user gave, size plausible.
- Journal has the "Finished track" line and a Next up.

## Recap

- Done = every section filled, starts and ends on purpose, no clipping, exported.
- Limiter at −1 dB as a seatbelt; loudness is a later skill; streaming normalizes anyway.
- Export WAV 24-bit, Normalize off; listen on a phone; write down one fix for track #2.

## Go deeper

Start track #2 with the other template ([09-arrangement-structure.md](09-arrangement-structure.md)); run `/ableton-live:study` on a reference track to compare structures; `/ableton-live:review` on the finished set for a full right / change / why pass.
