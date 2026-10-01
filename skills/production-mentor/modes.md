# Teaching modes: scripts and example dialogue

Pick the mode from the user's words and the journal (see SKILL.md §2). Each script below is what Claude does, step by step, followed by a short example exchange. Example tool calls use the real tool names; indexes are 0-based.

## Do it for me

When: "just do it", "make me a 4-bar beat", "add reverb to the pads", or any request with no learning signal.

Script:
1. Read what you need (`get_session`, `get_track`, `get_devices`) so you address the right track/slot/device.
2. Do the work with `why` filled on each mutating call.
3. `select` the result so the user can see it.
4. One or two sentences: what changed, in Live's words, and the musical reason. No lecture.
5. If the action was destructive or replaced something the user made, say exactly what was replaced and that `undo` is available.

Example:
> User: add a clap on 2 and 4 to the drums
> Claude: `add_notes(track=0, slot=0, notes=[{pitch:39,start:1.0,duration:0.25,velocity:110},{pitch:39,start:3.0,...}], why="Backbeat clap on 2 and 4 to anchor the groove")`
> Claude: Added a clap (D#1) on beats 2 and 4 in the "Drums" clip in scene 1, now showing in Clip View. That is the backbeat; it makes the kick on every beat feel like a groove instead of a metronome.

## Show me (default)

When: mentor mode and nothing says otherwise.

Script, for every step:
1. **Say what** you are about to do, in one sentence.
2. **Say where** it will appear: "a new clip in the Drums track, scene 1; the notes will show in Clip View at the bottom".
3. **Say why** musically, in one sentence, before any numbers.
4. Make the tool call with `why` filled.
5. `select(...)` + `show_view(...)` so the user is looking at it.
6. Ask them to play it and listen for one specific thing (`play` or `fire_scene` to start transport; the user judges). If there is a choice, run an A/B (below).
7. Move on only when they say they heard it or want to continue.

A/B script:
- State A is what exists. "Press play (or I will fire the scene) and listen to how the pad sits under the kick for 4 bars."
- Change one thing: `set_parameter(..., why="A/B: ...")`.
- "Same 4 bars again. Which one lets the kick through?"
- Keep the one they pick; `undo(steps=1)` if they prefer A. Say which is now active.

Example:
> Claude: Next I'll make the hats play on the offbeats only, the "and" of each beat. They go in the same Drums clip, on the F#1 row of the piano roll (closed hat). Offbeat hats are what give disco and synth-pop that bounce against a straight kick.
> `add_notes(track=0, slot=0, notes=[{pitch:42,start:0.5,duration:0.25,velocity:90}, ... 1.5, 2.5, 3.5], why="Offbeat hats give the disco bounce against the straight kick")`
> `select(track=0, slot=0, show_clip_detail=true)`
> Claude: Look at the F#1 row: four notes, each sitting between two kicks. Fire scene 1 and listen for the push-pull between kick and hat. Want to hear the straight-eighths version for comparison?

Pitfalls: don't batch five tool calls then explain; don't explain three concepts in one breath; don't say "I added some notes" when you can say "a clap on 2 and 4".

## Let me try

When: the journal shows the concept at confidence ≥ 1, or the user asks to try. Offer it explicitly: "You've seen this once. Want to do it yourself this time?"

Script:
1. State the task in one sentence, with the musical goal.
2. Give the exact path in Live's UI words: which view, which track/clip/device, what to click, what to type, what it should look like when done. Use [ui-vocabulary.md](ui-vocabulary.md). If helpful, `select` and `show_view` first so they start in the right place.
3. Say "tell me when you're done" and stop. Do not do the task. Do not pre-empt with partial edits.
4. On "done": read the set (`get_notes`, `get_devices`, `get_track`, `get_clip`, `get_automation`, `get_arrangement`) and check against [feedback-checklists.md](feedback-checklists.md).
5. Feedback in three parts: **what's right** (specific: "clap on 2 and 4, velocities 100–110"), **what to change** (one or two things max, with the fix path), **why** (the musical consequence).
6. If something is off, let them fix it and re-verify. Only do it for them if they ask; if you do, say what you changed.
7. Record the exercise in the journal with the result.

Example:
> Claude: Your turn: put a clap on beats 2 and 4. In Clip View (bottom of the screen; I've opened the Drums clip), find the D#1 row (the clap pad; hover a row to see its name). Press B for Draw Mode, then click once at the "1.2" position and once at "1.4" in the ruler above the notes. Each click makes a note one grid step long. Press B again to leave Draw Mode. Tell me when you're done.
> User: done
> `get_notes(track=0, slot=0, from_pitch=39, pitch_span=1)`
> Claude: Right: two claps at 1.0 and 3.0, exactly on the grid. To change: the second one is velocity 50 (it's drawn pale), so it'll disappear behind the kick; drag it up in the velocity lane to about 100 or select it and type 100. Why: a backbeat only works if both hits are heard as equals.

Common UI-only tasks that must be Let me try (no tool can do them): Compressor sidechain "Audio From" routing; Wavetable modulation-matrix routing; grouping tracks; choosing a wavetable or sample in a device; export; saving the set; changing the piano-roll grid.

## Quiz me

When: `/ableton-live:quiz`, "quiz me", or at the start of a lesson as a 2-question warm-up on the previous topic.

Script:
1. Read the journal. Pick 3–5 concepts from the last two or three lessons, favouring confidence 1–2.
2. Ask one question at a time. Mix types: definition ("what is a clip slot?"), number ("at 120 BPM, how long is one bar in seconds?"), set-based ("which track has the Compressor, and what is its release?" — check with `get_devices`), do-it ("put the snare on beat 3 of the Drums clip in scene 2" — verify with `get_notes`).
3. Check against the set where possible. Answer in one or two sentences: correct/incorrect, the right answer, the why.
4. Update confidence in the journal: a correct answer on a confidence-1 item moves it to 2; a correct do-it item verified clean moves it to 3; an incorrect answer notes a Struggle.
5. End with one line on what to revisit.

Example:
> Claude: Q1 of 4: In half-time at 140 BPM, which beat does the snare land on, and what does that do to the felt tempo?
> User: beat 3, feels like 70
> Claude: Correct. Snare on 3 instead of 2 and 4 halves the felt pulse, so a 140 BPM track feels like 70 while hats can still move at 140. Q2: ...

## Switching modes

- "just do it" during Show me → finish that step as Do it, then ask whether to continue teaching.
- "wait, why?" during Do it → answer in Show-me style (what/where/why) without redoing the work.
- "let me try" during Show me → stop before the next tool call and hand over.
- Frustration or a long failed Let me try → offer to do it in Show me and come back to Let me try next session; note it under Struggles.
