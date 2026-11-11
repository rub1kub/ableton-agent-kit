---
name: ableton-mix
description: Prepare, edit, mix and verify Ableton Live projects using Ableton MCP, local audio analysis and reversible project tools. Use for vocal timing/tuning, creative effects, arrangement, missing media and delivery; preserve the user's musical intent and recordings.
---

# Ableton Mix

Work from the actual set, source audio and the user's approvals. A convincing mix requires musical decisions and rendered evidence; neither a waveform nor a key label tells you everything about the sound.

## Start cheaply

1. Identify the task and protected choices: approved hook, long tail, vocal timbre, stereo movement, dry originals. Keep these as concrete invariants in a small local brief. Do not make the user repeat established preferences.
2. Find the toolkit with `ableton-agent --version` or run `scripts/run.py doctor` from this skill. Discover the control backend before probing Live: this toolkit's `doctor --live` and direct `live-*` commands target the legacy protocol only. The installer writes a local `runtime.json`; it is not portable to another machine.
3. Identify the connected backend from its actual tools/capabilities; read [backends.md](references/backends.md) if it is unfamiliar. Inspect live state and the saved set separately. Use the backend's compact overview; for the legacy extension use `live-snapshot --limit 16 --out ...`. `als-audit SET --out ...` inspects the saved file. If Live has unsaved edits, a disk hash cannot capture them. Ask for the necessary save once; continue independent source analysis meanwhile.
4. Preserve the existing version before editing. Work in a new set or native Undo-bounded edits. Never overwrite raw recordings, replace originals with processed audio, or change drivers/hardware inputs/monitoring as a side effect.

## Read only the relevant reference

| Task | Reference |
|---|---|
| Select Ableton MCP versus legacy LiveMCP; avoid incompatible commands | [backends.md](references/backends.md) |
| Turn a complaint into an evidence-based mix experiment | [diagnosis.md](references/diagnosis.md) |
| Prepare recording, route tracks, structure a session | [session.md](references/session.md) |
| Control Live, find inaudible effects, use safe parameter batches | [live.md](references/live.md) |
| Inspect/revise `.als`, relink media, preserve takes | [projects.md](references/projects.md) |
| Analyze waveform, gaps, pitch, loudness, capture and compare | [evidence.md](references/evidence.md) |
| Vocal editing, tuning, gain, EQ, dynamics | [vocals.md](references/vocals.md) |
| Choose and control free VST3s; expose/cache parameters; use an offline host | [plugins.md](references/plugins.md) |
| Echo, pitched answers, stereo movement, filters and transitions | [effects.md](references/effects.md) |
| Collect, export, tag WAV/MP3, deliver | [delivery.md](references/delivery.md) |
| Recognize and recover demonstrated failure modes | [troubleshooting.md](references/troubleshooting.md) |

## Make changes that can be assessed

For each pass, state the audible problem, affected time range, intended change and evidence needed. Fix source/timing/gain issues before compensating with additional processing. Preserve desired overlaps and stylistic exaggeration; do not impose dry, centered or natural vocals when the user wants a creative effect.

Separate the intelligible central performance from optional width/motion layers when helpful. Treat copied layers as artificial support, not independent recorded doubles. Fit word repeats into actual gaps; allow overlap when explicitly desired. Tonality analysis proposes candidates: inspect stable vowels and musical phrases before tuning. No blanket pitch snapping of consonants or guessed key changes.

Use native operations where available. Offline editing is a fallback for a saved copy; it needs structural checks **and** a native reopen check. The toolkit's limited revision commands do not claim full arrangement authoring. Use the connected backend's tools or controlled UI for unsupported operations, with the same preservation rules.

## Verify and report honestly

Check the full signal path and rendered result, not just parameter values. Verify clip positions after native loading, track/parent activators, routing, effect enable states and missing media. Compare approved and changed sections at matched loudness. Use mono, peaks, band balance and stereo motion as diagnostics; these do not replace diction/groove review.

State what was done, where it is saved, what was actually measured or heard, and remaining limitations. Do not claim physical listening, native saving, Collect All, automatic key certainty or a final master without evidence. Stop transport when finished with an authorized playback test and preserve the user's requested selection. If the user prefers manual save/open, keep that workflow.

## Keep the next turn small

Store locally: current set hash/version, track identities, protected regions, operation plan/journal, report paths and unresolved questions. Paginate inventories, request one device at a time, and diff snapshots. Do not dump every parameter, model output or audio array into context. Reuse evidence only while its file hashes and relevant live state remain valid.
