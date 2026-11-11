# Free plugins: useful roles and actual control

Use this reference when choosing an installed external processor, inspecting its parameters or troubleshooting an empty Configure panel. Installation alone does not prove that Live has scanned or loaded it. Read the local installation manifest if one is available; otherwise discover the browser item and version first.

## The tested starting palette

These versions passed a one-second synthetic DSP test in Pedalboard 0.9.26 on Windows x64. Counts below belong to that separate host, **not** Live's exposed parameter list. No claim of native Live loading follows from them.

| Plugin | Role | Offline parameters | Main operating detail |
|---|---|---:|---|
| TDR Nova 2.2.3 | Dynamic EQ, de-essing, resonances | 76 | More than Live's usual 64-parameter automatic threshold; expose the relevant band controls before automation. Diagnose the resonance before choosing its frequency. |
| TDR Kotelnikov 1.6.7 | Transparent vocal/bus dynamics | 22 | Peak/RMS releases are separate. Match output loudness; verify Delta audition and Bypass are off for delivery. |
| Dragonfly Early Reflections 3.2.10 | Close spatial placement | 9 | Small amounts can give proximity without a long tail. |
| Dragonfly Hall 3.2.10 | Large, calm space | 20 | Use separate early/late levels; remove the dry component when used on a return. Keep diction with predelay and wet-path ducking. |
| Dragonfly Plate 3.2.10 | Vocal density and smooth tail | 11 | Prefer a modest send before lengthening the decay. |
| Dragonfly Room 3.2.10 | Short coherent ambience | 19 | Match room character across sections while varying send levels. |
| CHOWTapeModel 2.11.4 | Tape color, saturation, movement | 54 | Match input/output gain; start wow/flutter/noise subtle. Offline and real-time oversampling may differ. |
| ChowMatrix 1.3.0 | Pitched stereo answers and complex delay | 44 at default topology | Node creation/topology is not equivalent to scalar parameter control. A preset/topology change invalidates cached mappings. Start Insanity and feedback conservatively. |
| Surge XT Effects 1.3.4 | Filters, modulation, distortion, delay, creative FX | 13 in default mode | Changing FX type changes parameter meaning/names. Re-read immediately. Default output gain is not assumed transparent. |
| Surge XT 1.3.4 | Synth layers, basses, hooks, transitions | 775 | Live cannot expose this whole surface in 128 slots. Prefer a patch plus explicitly configured macros; preserve factory assets. |
| Voxengo SPAN 3.24 | Visual spectral/stereo/level inspection | 3 | GUI meters are not readable audio measurements through those three parameters. Use toolkit analysis for machine-readable evidence. |

Native Auto Shift, EQ Eight, Compressor, Auto Pan and Utility remain useful. External plugins are alternatives for a specific job, not mandatory inserts on every channel. Preserve user-approved timbre and tails.

## A reliable native workflow

1. Find the exact plugin in Live's browser, load it on a suitable scratch track, then query the loaded device. Record plugin/version, track identity, device name, parameter names, native bounds and display strings. Never infer the loaded instance from a filename alone.
2. If Live exposes only Device On, configure the required controls in its UI and save a native default/rack. Ableton documents `-_PluginAutoPopulateThreshold=128` in Options.txt as an **experimental** option: it requires restart and populates up to 128 controls. Preserve existing options and make its addition reversible. It is not a way to expose every Surge control. Do not change drivers or monitoring.
3. Make one small nonautomated edit and verify readback plus Undo in the scratch set. Ensure stereo routing, return dry/wet semantics and existing automation are preserved. Not all third-party GUI actions participate in Live Undo identically.
4. Re-query parameters after a preset, FX algorithm, node topology, plugin version or chain change. Cache only while identity and relevant state still match. Prefer names with verified indices; duplicate/truncated labels require disambiguation.
5. Process a short musical section, capture/export and loudness-match the comparison. Check consonants, mono, gain and tail overlap. An active meter or finite test output does not establish a good mix.

## Offline probing and processing

Install the toolkit's optional `plugins` extra. `plugin-probe "Plugin.vst3" --out local/plugin.json` loads **trusted installed native code** in a child process, fingerprints the bundle, discovers parameters and runs a quiet synthetic test without playing audio. A timeout stops the child. This is process isolation, not a security sandbox: only load user-authorized plugins from trusted sources.

On Windows x64, the probe resolves a bundle to its `Contents/x86_64-win/*.vst3` binary for Pedalboard. Keep the original bundle intact for Live. A failed offline host scan does not prove that the plugin fails in Live.

Read only the few relevant rows from the saved JSON. Pedalboard's `raw_value` is 0..1; its inferred labels/ranges can be inaccurate. Live's parameter mapping must be read separately. Do not send normalized values to a native Hz/dB parameter by assumption.

For an authorized offline experiment, use a separate plugin instance and new output file. Read/write a documented parameter, verify its display value, then render at the source sample rate with explicit headroom and enough tail. If processing chunks, reset only at the start so delay/reverb state survives. Preserve the dry original and report the exact parameters; the separate instance does not inherit the current Live preset, automation or tempo automatically.

## Musical combinations to try

- Clearer dense vocal: measured Nova dynamic cut/de-essing → moderate Kotelnikov control → quiet parallel tape color. Compare at matched loudness and keep only improvements.
- Spacious calm hook: intelligible dry center + dark ChowMatrix answers + Hall return. Duck the wet buses during words and let them recover into pauses; avoid an abrupt tail gate.
- Recognizable high ending: Auto Shift or an explicitly tuned vocal layer → short pitched delay → sparse Hall/Plate tail. Keep the entire word's tuning consistent; repeat full words only where they fit, preserving intentional overlaps.
- Glitch verse: automate a separate support layer with Live Auto Pan and an appropriate Surge FX mode. Preserve the lead's consonants and use phase/mono checks. Adding every available effect usually hides the rhythmic idea.

Official sources and licensing are listed in the repository's `docs/free-plugins.md`. Plugin binaries and preset libraries are not redistributed in the kit.
