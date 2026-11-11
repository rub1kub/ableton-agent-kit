# Ableton MCP versus the installed LiveMCP

Research snapshot: 2026-11-11. **Names alone do not identify a server.** The website `abletonmcp.com` links to `wstierhout/ableton-live-mcp`; `ahujasid/ableton-mcp` is a different, older project with several forks.

## Decision for this workflow

For a Live 12.2.2 vocal-editing workflow, **evaluate the typed wstierhout backend as the preferred general control backend**, with selected tool groups and this toolkit's audio/skill layer. Its main-thread reads, batch operations, state comparison, rack access and version-matched installer address concrete friction in the observed legacy setup.

Do **not** assume migration would have solved the music automatically. The observed local LiveMCP already has 59 read and 141 write socket commands, including arrangement audio creation and take lanes. Those 200 socket commands are not directly comparable to 156 client-facing MCP tools. Several painful failures came from our workflow (muted copied tracks, timing, missing media, insufficient rendered verification), not simply from a small command count.

CanArslanDev's fork is especially interesting for a later audio-aware workflow: render analysis, stem capture, reference comparison, snapshots and project memory are integrated. However its README requires Live 12.3 for `add_device`/`apply_device_chain`, some automation is real-time recording, and its companion SDK renderer targets Live 12.4.5+ Suite and is explicitly not yet run in Live by its authors. It is **not** a verified drop-in replacement for 12.2.2.

No native migration or comparative listening benchmark is claimed here. The current working installation remains a fallback until a disposable-set acceptance test passes.

## Capability matrix

| Requirement | Observed local LiveMCP | wstierhout 1.8.1 | CanArslanDev 2.3.0 | Agent Kit contribution |
|---|---|---|---|---|
| Compact orientation | Multiple individual getters | Session snapshot + session diff | Overview + memory + snapshots | Paginated legacy extension; saved reports |
| Fewer visible tools | Depends on host | `ABLETON_TOOLSETS` by domain | Default compact profile; full optional | Seven-tool optional bridge; progressive skill references |
| LOM thread discipline | Reads on socket thread; writes scheduled | All LOM access scheduled; timeout cancellation | Read source/doctor before use; generic LOM surface | Additive legacy handlers scheduled on main thread |
| Group/return inspection | Observed unguarded arm access can fail | Explicit group/rack and return tools | Generic object + overview | Guarded arm query, role-aware inventory |
| Batch changes | No batch found in inspected registry | Batch in one round trip | `run_batch` | Strict expected-identity/value parameter batch |
| Arrangement vocals | Audio creation, take lanes, clip commands | Placement, deletion, clip audio tools | Broader LOM and arrangement helpers | Conservative saved-copy edits and load checks |
| Audio-track automation | Not equivalent to arbitrary envelope authoring | `write_automation` addresses a Session clip | Workarounds; audio/return automation can require recording | Workflow distinguishes native envelope vs offline edit |
| “Hear” the result | Meters/control; separate capture needed | `record_section` records temporary track; file analysis | `render_and_analyze`, `mix_doctor`, analyzer | Process loopback; metrics, plots, alignment and explicit uncertainty |
| Does mix diagnosis measure audio? | Meter/state queries alone do not | `analyze_mix` explicitly state-only | `mix_doctor` captures stems and computes measures | Separate band-overlap proxy from actual perceptual diagnosis |
| Save/open/Collect All | Missing in observed registry | `try_save_project` conditional on `song.save_project` | No general native export API; document limitations | Explicit manual handoff; partial media collector labeled honestly |
| Native device loading version | Browser loading already used | Browser-based tools in inspected release | Some convenience loading requires 12.3 | Discover availability; no invented plugin capabilities |
| Privacy/security | Loopback, no auth observed | Loopback by default; no remote eval | Local session-token mechanism; generic LOM access | Local-only evidence; allowlist, journals, roots and write opt-in |

## Source verification, not marketing counts

Inspected revisions:

- [wstierhout `55abd3a`](https://github.com/wstierhout/ableton-live-mcp/tree/55abd3a38a74c39f6f2fc0d1d90107d06ec5f952): README, project metadata, dispatcher, tool groups, arrangement/audio/analysis implementations and tests. Static extraction found 156 decorated MCP definitions and 118 socket handlers. These are definitions, not a live capability test.
- [CanArslanDev `e65141b`](https://github.com/CanArslanDev/ableton-live-mcp/tree/e65141b411746841746b553e3e8dbd6ab44442e8): README limitations, mix-and-master skill, dependency versions, audio and mix analysis implementations/tests. Uses a different MCP SDK major and should be isolated in its own environment.
- [ahujasid `9dddc7b`](https://github.com/ahujasid/ableton-mcp/tree/9dddc7bd5b95412510fdeb745949e3bf23f3fd8a): original project lineage and public interface. Not assumed to have fork features.
- Local legacy script: parsed its handlers without executing them. Upstream provenance remains unestablished; no private installation code is redistributed.

`record_section` in the inspected wstierhout revision records by adding/arming a temporary track. Its `finally` block deletes that track, but the inspected implementation does not fully restore transport/record state on every earlier failure or preserve every user's armed-track condition. Therefore it is **not** the default unattended measurement path in this skill. Prefer passive process capture/native export until a guarded recording workflow is tested.

`try_save_project` checks whether `song.save_project` exists; a named save tool is not proof of successful saving in the user's Live build. Similarly, “write automation” can mean replacing a Session clip envelope, not drawing arbitrary audio-track Arrangement automation. Read the actual schema and implementation before choosing it.

## Migration plan

1. Preserve installed Remote Script and client configuration. Identify the exact running bridge version and protocol; do not identify it by port alone.
2. Install the chosen pinned server into a **separate environment**. Keep its matching Remote Script version. Do not combine the two forks' Python dependencies in the toolkit environment.
3. Use only one active bridge on port 9877, or configure distinct ports on both ends. A second bridge binding to the same port is not a successful installation.
4. For wstierhout, start with `ABLETON_TOOLSETS=session,tracks,devices,arrangement,analysis`. Add browser/clips/audio only when needed. Check the actual tools/list; these profiles reduce choices, not the capabilities of Live itself.
5. Re-run the disposable-set acceptance gate in [verification.md](verification.md): groups, returns, rack parameters, one guarded edit, undo, transport, native media/clip load and actual audio.
6. Use the selected backend's own connected tools for control. Agent Kit's direct `LiveClient` speaks the **legacy newline protocol only**; do not send its payloads to an incompatible server. `backend-plan` maps an observed tool list to tasks without connecting or mutating anything.
7. Keep a rollback path. Do not upgrade Live, change drivers or overwrite projects merely to enable a fork's optional features.

The recommendation is based on source inspection and workflow fit, not an assertion that an untested backend already works on the user's machine.
