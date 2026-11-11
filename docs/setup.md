# Installation and operating modes

## CLI + skill

Create a virtual environment at a stable location. Install `.[dev,mp3,plot,mcp]`; add `windows` for process capture, `pitch` for librosa, or `asr` for local faster-whisper. These extras are optional to keep startup and installation costs reasonable.

Run the skill installer **using that environment's Python**:

```text
python scripts/install_skill.py
```

It copies only the skill and writes a local runtime pointer. It does not edit Codex configuration, register a server automatically, install plugins into Live, or replace an existing skill. To use another agent, point it to `skills/ableton-mix/SKILL.md` and install the CLI in its environment.

## Optional MCP bridge

Register the environment's absolute `ableton-agent-mcp` executable as a stdio MCP server in your agent's configuration. Example **conceptual JSON** (adapt keys to your host):

```json
{
  "command": "ABSOLUTE_PATH_TO_VENV/Scripts/ableton-agent-mcp.exe",
  "args": [],
  "env": {
    "ABLETON_AGENT_ROOTS": "ABSOLUTE_PROJECT_ROOT",
    "ABLETON_AGENT_WRITE": "0"
  }
}
```

Multiple roots use the platform path separator (`;` on Windows, `:` on Unix). Read paths and output paths both stay within those roots. Enable `ABLETON_AGENT_WRITE=1` only for a session authorized to edit the set. Writes also require a local journal directory. Server configuration is not itself user authorization to edit unrelated projects.

The bridge tools are `project_audit`, `audio_analyze`, `audio_compare`, `live_snapshot`, `live_read`, `plan_word_echo`, and `live_apply_parameters`. No cloud service is required. CLI exposes additional optional heavy analysis to keep the always-visible MCP surface small.

## LiveMCP additive extension

The observed upstream layout has `server.py`, `handlers/__init__.py`, `get_all_write_handlers()` and `_run_on_main_thread`. Other forks need a reviewed adapter; matching a name alone does not prove compatibility.

1. Run `python scripts/stage_extension.py EXISTING_LiveMCP NEW_STAGING_DIRECTORY`.
2. Review the staged diff: only `handlers/agent_extension.py`, appended registration and a hash manifest should be new/changed. All extension handlers go in the upstream **write registry** solely to use its main-thread dispatcher; six of the seven commands are read-only.
3. Save your work and close Live. Keep a full copy of the original Remote Script directory.
4. Replace the installed `LiveMCP` directory with the staged copy using your normal filesystem permissions. Do not overlay a currently loaded script.
5. Start Live with its existing control-surface configuration. Run `ableton-agent live-call aa_capabilities` and a small `live-snapshot --limit 4`.
6. If startup or capabilities fail, close Live and restore the original directory. Do not keep patching a running script.

The extension intentionally does not patch existing `get_track_info` or `get_mixer_state`; use `aa_track`/`aa_snapshot` to avoid unsafe `arm` access on groups and returns. It does not implement saving, opening or Collect All. It rejects writes to automated parameters; write an envelope with suitable native tooling instead.

## Passive audio capture

```text
ableton-agent capture --pid TARGET_PID --seconds 30 --output captures/review.wav
```

Windows build 20348+, `comtypes`, compatible render path. Captures the target and children, never microphone input by configuration. Start the intended section in Live yourself or use authorized transport commands. The command does not change transport. For automated capture, collect transport telemetry and validate it with `transport_check`, then align the captured audio against a known musical segment. Capture duration is not a proof of song position.

If a driver bypasses the Windows audio engine, use a native Live export. Do not alter the user's drivers to make a measurement tool work.
