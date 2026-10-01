# Drum Rack (`DrumGroupDevice`)

A rack with one chain per pad; each pad usually holds a Simpler (or Drum Sampler / Operator) plus
effects. The rack itself only exposes macros; the sound lives in the chains.

## Load a kit or an empty rack

- Empty rack: `load_device(name="Drum Rack", track=i, category="drums")` (or `"instruments"`).
- A kit: `browse(query="Kit", categories=["drums"])` → pick an `is_loadable` item → `load_device(uri=...)`.
  Kits with "808", "909", "Techno", "Trap" in the name suit these genres. Say which kit you loaded.
- Live 12 also ships **Drum Sampler** pads inside many kits; its parameters differ from Simpler — read them.

## Read the pads before writing notes

`get_devices(track=i, device_path="0")` → `DeviceDetail` with
`drum_pads: [{note, name, has_chain}]` and `chains: [{index, name, devices}]`.

- Write MIDI only to pads with `has_chain: true`; use `note` as the pitch and `name` to pick kick/snare/hat.
- A chain's devices are addressed `"<rack>/<chain index>/<device index>"`, e.g. the kick pad's
  Simpler at chain 3 → `device_path="0/3/0"`. Chain index ≠ pad note; map via `chains[].name` matching `drum_pads[].name`.
- `depth` controls how deep `get_devices` recurses; the default 2 reaches pad devices.

## What you can set

| Where | Parameters | Use |
|---|---|---|
| Rack (`"0"`) | `Macro 1` … `Macro 16` (only if mapped) | Kit-level knobs some presets expose (Tune, Decay, Drive) |
| Pad Simpler (`"0/<c>/0"`) | see [simpler.md](simpler.md): `Transpose`, `Detune`, `Ve Attack`, `Ve Decay`, `Ve Release`, `Filter Freq`, `Volume`, `Pan`, `Start`, `End` | Tune the kick, shorten the hat, soften the clap |
| Pad effects (`"0/<c>/1"`…) | Whatever is there (Saturator, EQ…) | Drive one pad without affecting the rest |
| Chain mixer | Not exposed as a device in v1 | Ask the user for chain volume/pan/send, or use the pad device's `Volume`/`Pan` |

**Not settable in v1:** pad note assignments, choke groups, in/out note mapping, loading a sample
onto a pad. Tell the user: "Drag the sample onto pad C1" or "set both hats to Choke 1 in the pad's
chain list" and re-read afterwards.

## Recipes

### Tune the kick to the key
1. Find the kick chain; read its Simpler `Transpose`/`Detune`.
2. The kick's pitch should sit on the root or 5th. For F minor set `Transpose` so the fundamental
   lands near F (listen; usually ±2 semitones). Explain: "a kick in key stops fighting the sub".
3. For dubstep keep the kick short: `Ve Decay` 150–250 ms, `Ve Sustain` 0.

### Tighter hats
`Ve Decay` 60–120 ms on the closed hat; open hat 300–500 ms. If open and closed hats overlap,
ask the user to put them in the same choke group.

### Layered snare for the drop
Write the clap pad and the snare pad on the same `start` (see `midi-writing/drums.md`); pan them
±10 opposite; add a Saturator on the snare chain (`"0/<c>/1"`) with Drive 6 dB.

### Kick as sidechain source
The kick is inside the rack, so the Compressor's "Audio From" must point at the drum **track**
with the kick's **chain** selected ("Post FX" on that chain). The user picks this in the dropdown
(not settable via API); you set threshold/ratio/attack/release ([../effects/compressor.md](../effects/compressor.md)).

## Verify
After any by-hand change (choke, pad move, kit swap), `get_devices` again: chain indices shift.
