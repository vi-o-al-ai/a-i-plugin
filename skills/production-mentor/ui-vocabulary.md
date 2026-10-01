# Live 12 UI vocabulary

Use Live's own names when telling the user where to look or click. Shortcuts are macOS first, Windows second (Cmd/Ctrl, Option/Alt). Where a shortcut may differ across versions, say "or use the View menu".

## Mapping tool addresses to what the user sees

| Tool field | In Live |
|---|---|
| `track` (0-based) | Track position left to right in Session View / top to bottom in Arrangement View. Live numbers from 1: tool index 2 = Live's track 3. Use the track name with the user. |
| `track_type="return"`, `track` | Return tracks A, B, C… (index 0 = A) to the right of the regular tracks (Session) or below them (Arrangement). |
| `track_type="master"` | The Master track, far right / bottom. |
| `slot`, `scene` (0-based) | Row in the Session grid. Scene 0 is the top row; scenes have names and launch buttons in the Master column. |
| `device_path="0"` | Leftmost device in Device View for that track; `"1"` is the next one right. `"0/1/2"` goes into a rack's chain 2, device 3. `"mixer"` is the track's fader, pan, sends and Track Activator. |
| `parameter` | The knob/switch label in Device View (hover shows the full name in the Status Bar at the bottom left). |
| `time` (arrangement) | Song beats from 0. Bar N starts at (N − 1) × 4 at 4/4. The Arrangement ruler shows bars; position 32.0 is bar 9. |
| `start` (note) | Position inside the clip. Clip View's ruler shows bar.beat; 1.3 means bar 1 beat 3 = 2.0 beats. |
| `pitch` | Row in the piano roll. Live labels 60 as C3 (middle C), 36 as C1. Drum Rack rows show pad names. |
| `volume` 0–1 | The track fader. 0.85 is the 0 dB mark; 1.0 is +6 dB (the top). |
| `color_index` 0–69 | Live's colour palette (right-click a track, clip or scene → colour swatches). Row 1 runs roughly red → orange → yellow → green → cyan → blue → purple → magenta → white at indexes 0–13, then darker/lighter rows; the response's `color` hex tells you what was set. |

## Main areas

| Name | What it is | Where / how to show |
|---|---|---|
| Session View | The grid of clip slots: tracks as columns, scenes as rows. For jamming and building loops. | Tab toggles Session/Arrangement. `show_view("Session")`. |
| Arrangement View | The timeline: tracks as lanes, time left to right. For building the song. | Tab. `show_view("Arranger")`. |
| Detail View | The bottom panel. Shows either Clip View or Device View for the selected clip/track. | Cmd/Ctrl+Option/Alt+L toggles it. Shift+Tab switches Clip View ↔ Device View. |
| Clip View | The clip's piano roll (MIDI Note Editor) with its loop brace, Scale controls, velocity lane, Envelopes box. | Double-click a clip. `show_view("Detail/Clip")` or `select(track, slot, show_clip_detail=true)`. |
| Device View | The track's device chain, left to right in signal order. | Double-click a track name. `show_view("Detail/DeviceChain")` or `select(track, device_path, show_device_detail=true)`. |
| Browser | Left sidebar: Sounds, Drums, Instruments, Audio Effects, MIDI Effects, Max for Live, Plug-Ins, Clips, Samples, Packs, User Library. Drag items onto a track. | Cmd/Ctrl+Option/Alt+B. `show_view("Browser")`. |
| Mixer section | Faders, pan, sends, Track Activator (the yellow number button), Solo (S), Arm (record button) at the bottom of Session tracks or right side of Arrangement tracks. | Cmd/Ctrl+Option/Alt+M; Sends Cmd/Ctrl+Option/Alt+S; Returns Cmd/Ctrl+Option/Alt+R; In/Out Cmd/Ctrl+Option/Alt+I. |
| Control Bar | Top strip: tempo (type a number), time signature, metronome, Play/Stop/Record, Arrangement position, loop switch and loop brace fields, quantization menu, Back to Arrangement (orange), Re-enable Automation (orange), CPU meter. | Always visible. |
| Status Bar | Bottom-left strip that describes whatever is under the mouse, including full parameter names. | Always visible. |

## Objects

| Name | What it is | Click path |
|---|---|---|
| Clip slot | One box in the Session grid. Holds one clip or is empty (a square stop button if the track has a clip playing elsewhere). | Double-click an empty slot on a MIDI track to create a 1-bar clip. |
| Scene | A row of slots plus its launch button in the Master column. Firing a scene fires every clip in the row. | Right-click a scene → Rename; Cmd/Ctrl+I inserts a scene. |
| Clip | A MIDI or audio loop. Has a name, colour, length, loop brace, launch quantization. | Select it; its settings appear in Clip View's left panel. |
| Loop brace | The bracket above the piano roll that marks the looped region. | Drag its ends; Cmd/Ctrl+L sets it to the selection. |
| Launch quantization | When a fired clip or scene actually starts (default: next bar). The Control Bar "Quantization" menu sets the global value. | Clip View → Launch panel. |
| Return track | A track that only receives what other tracks send to it. Hosts shared Reverb/Delay. | Cmd/Ctrl+Option/Alt+T creates one. |
| Send | The knob on each track (A, B…) deciding how much goes to each return. | Mixer section, below pan. |
| Master track | Where everything sums. Its fader is the final level. | Far right (Session) / bottom (Arrangement). |
| Group track | A folder track that sums its children (a bus). | Select tracks → Cmd/Ctrl+G. Not available through the tools; user does it. |
| Device | An instrument or effect in Device View. Title bar has the On/Off switch (yellow dot, left), the name, Hot-Swap and Save buttons (right). | Drag from Browser; or double-click in Browser to add to the selected track. |
| Rack | A device holding chains of devices with 8 Macro knobs. Instrument Rack, Audio Effect Rack, Drum Rack. | Unfold the chain list with the ▾ at the title bar's left edge. |
| Drum Rack pad | One of the 16 visible pads (128 total), each a chain with its own sample/instrument. Pad note name shows on the pad. | Drag a sample or instrument onto a pad. |
| Piano roll (MIDI Note Editor) | Where notes live. Rows are pitches, columns are time. | B toggles Draw Mode (click to add a note). Right-click the background → Fixed Grid → 1/16, 1/8T etc. Cmd/Ctrl+1/2 narrows/widens the grid; Cmd/Ctrl+3 toggles triplets. |
| Velocity lane | The strip under the notes with a vertical bar per note. | Drag a bar up/down; or select notes and type a value in the Note panel. |
| Fold button | Hides unused rows in the piano roll. | Top-left of the piano roll. |
| Scale (Live 12) | Clip-level Scale switch + root/scale choosers in Clip View; in-scale rows are highlighted; Fold then shows only scale notes. The set also remembers a current scale that new clips inherit (`set_scale`). | Clip View → Scale button next to the root/scale fields. |
| Envelopes box (Clip View) | Clip automation ("clip envelopes"). Pick a device and a parameter in the two choosers; draw points in the lane. | Clip View → the "E" (Envelopes) tab/box. `set_automation` writes here for session clips. |
| Automation Mode (Arrangement) | Shows parameter lanes in Arrangement View. | Press A. Pick parameter from the lane's two choosers. |
| Locator | A named marker on the Arrangement timeline. | Right-click the scrub area (above the tracks) → Add Locator; or the "Set" button next to the Arrangement position. `set_locator` writes these. |
| Back to Arrangement | Orange button in the Control Bar that lights up when Session clips are overriding the Arrangement. Click it to hear the Arrangement again. | Control Bar, right of the position display. |
| Re-enable Automation | Orange button that lights up when a parameter with automation was moved by hand. Click to let the automation take over again. | Control Bar. |
| Loop switch and brace (Arrangement) | Repeats a region of the timeline. | Control Bar loop button; drag the brace in the Arrangement ruler; Cmd/Ctrl+L on a selection. |

## Common click paths

- Create MIDI track: Cmd/Ctrl+Shift+T. Audio track: Cmd/Ctrl+T. Return: Cmd/Ctrl+Option/Alt+T.
- Rename anything: select it, Cmd/Ctrl+R, type, Enter. Colour: right-click → palette.
- Duplicate clip/scene/time: Cmd/Ctrl+D. Double a clip's loop content: the duplicate-loop button in Clip View (labelled "Dupl. Loop" or "×2" depending on version); Claude's `duplicate_clip_loop` does the same.
- Quantize notes: Cmd/Ctrl+U (settings: Cmd/Ctrl+Shift+U).
- Undo: Cmd/Ctrl+Z (Claude's `undo` does the same).
- Record a Session loop into Arrangement: Arrangement record button in the Control Bar, play the scenes, stop; or drag a clip from Session into an Arrangement lane.
- Export: File → Export Audio/Video (Cmd/Ctrl+Shift+R).
- Save set: Cmd/Ctrl+S. Ask the user to save before any Let-me-try that touches many things.

## Compressor sidechain (UI-only)

Device View → Compressor → click the ▸ at the far left of the device title bar to unfold the Sidechain section → turn on **Sidechain** → **Audio From**: choose the drum track → second chooser: a specific pad/chain ("Kick") or "Post Mixer" → optional **Gain**. Claude can set threshold/ratio/attack/release and read "S/C On" if exposed, but not the Audio From source.

## Wavetable modulation matrix (UI-only)

Device View → Wavetable → the **Matrix** tab (right side) → the row for LFO 1 (or Env 2) → click the cell under the destination ("Filter 1 Freq", "Osc 1 Pos") and drag up to set the amount. Claude sets LFO rate/shape and the filter itself, but cannot create the routing.

## Settings → Link, Tempo & MIDI (control surface; Preferences in older Live versions)

Live → Settings (macOS) or Options → Settings (Windows), Cmd/Ctrl+,. Tab **Link, Tempo & MIDI**. Under **Control Surface**, pick **ClaudeLive** in the first free row; leave Input and Output as "None". Live loads the script immediately; `ableton_status` should then show `connected: true`. If it says connection refused, the surface is not selected or Live is not running; if timeout, Live has a modal dialog open or is loading.
