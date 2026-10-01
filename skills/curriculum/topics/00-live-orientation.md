# 00 · Live orientation

**Goal.** The user can name every main area of Live 12, knows where a sound goes from a MIDI note to the speakers, and has made one clip play on one track with one effect.

**Prerequisites.** Live 12 open with a set (empty is fine); `ableton_status` returns `connected: true`. If not, fix Settings → Link, Tempo & MIDI → Control Surface: ClaudeLive (Preferences in older Live versions) first (see `production-mentor/ui-vocabulary.md`).

**Terms introduced (define once).** Session View, Arrangement View, Detail View (Clip View / Device View), clip slot, scene, return track, master, Browser, signal flow.

## Plan (15–20 min)

1. **Show me · what is in the set (2 min).** `ableton_status`, then `get_session()`. Say what it found in Live's words: "4 tracks, 8 scenes, 2 return tracks, the Master". `show_view("Session")`. Explain: Session View is a grid; columns are tracks (instruments), rows are scenes (sections). A clip slot is one box: the place a loop lives.
2. **Show me · Session vs Arrangement (3 min).** `show_view("Arranger")`: same tracks, now as lanes with time left to right; this is where the song gets built. Back with `show_view("Session")`. One sentence: "Session is for finding loops, Arrangement is for finishing songs. We will use both."
3. **Show me · a track and its signal flow (4 min).** `create_midi_track(name="Tour", why="A scratch track to learn the signal path")`. `select(track=<new>)`, `show_view("Detail/DeviceChain")`: an empty device chain. `load_device(name="Drift", track=<new>, why="A stock synth to turn MIDI into sound")`. Point at it: "Device View shows the chain left to right. MIDI notes come in from the left, Drift turns them into audio, anything to the right of Drift changes that audio, then it hits the track's fader (the Mixer section), then the Master." Verify `get_devices(track)` shows Drift at path `"0"`.
4. **Show me · a clip and a note (3 min).** `create_clip(track, slot=0, length=4.0, name="Tour clip", why="One bar to hear the path end to end")`. `add_notes(track, slot=0, notes=[{pitch:60,start:0.0,duration:1.0,velocity:100}], why="One middle C")`. `select(track, slot=0, show_clip_detail=true)`: "This is Clip View, the piano roll. Rows are pitches, columns are time; this note is C3 on beat 1." `fire_clip(track, slot=0)`; ask them to confirm they hear it; `stop`.
5. **Let me try · add an effect from the Browser (4 min).** Task: "Open the Browser (Cmd/Ctrl+Option/Alt+B), click Audio Effects, find Reverb, drag it onto the Tour track's Device View to the right of Drift. Tell me when it's there." Verify: `get_devices(track)` → Drift at `"0"`, Reverb at `"1"`. Feedback: right (order), change (if Reverb landed before Drift: drag it right of Drift), why (effects after the instrument process its sound; before it they get no audio).
6. **Show me · returns, sends and master (2 min).** `get_session(include_returns=true)`; `select(track=0, track_type="return")`. "Return A is a track that only hears what other tracks send to it; the send knob on each track decides how much. Master is where everything sums; its fader is the last thing before your speakers." If there are no returns: `create_return_track(name="A Reverb")` and say what appeared.
7. **Recap and journal (1 min).**

## Exercise (Let me try)

Rename the Tour track to "My First Track" (click the name, Cmd/Ctrl+R, type, Enter) and set its colour (right-click the name → a colour). Verify with `get_track(track)` → `name`, `color`.

## Verification

- `get_devices(track)`: exactly one instrument (Drift, `type: "instrument"`) followed by Reverb (`type: "audio_effect"`), both `is_active`.
- `get_notes(track, slot=0)`: one note, pitch 60, start 0.0.
- `get_track(track).name == "My First Track"`.
- `get_session().return_tracks` has at least one entry.

## Recap

- Session = grid of loops; Arrangement = timeline of the song; Detail View at the bottom shows the clip (notes) or the device chain (sound).
- Signal flow: MIDI note → instrument → audio effects → track fader → sends/returns → Master.
- A clip slot is one loop; a scene is a row of them that launches together.

## Go deeper

Next: [01-tempo-grid-and-clips.md](01-tempo-grid-and-clips.md). Vocabulary reference: `production-mentor/ui-vocabulary.md`. Optional: `/ableton-live:explain` with any object selected to hear it described in these terms.
