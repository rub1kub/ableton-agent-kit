# LiveMCP control and signal-path diagnosis

Use `doctor --live`, then `live-snapshot` or `aa_capabilities`. The toolkit client connects only to `127.0.0.1:9877`, uses newline JSON, bounded responses and no blind mutation retries. The optional bridge exposes a small tool surface. Full CLI help is available with `ableton-agent --help`.

## Read in pages

Extension queries: `aa_snapshot`, `aa_track`, `aa_clips`, `aa_parameters`, `aa_meters`. Track selector is `{scope: "track"|"return"|"master", index: N}`. `offset` and `limit` bound lists; follow `next_offset`. Master index is zero. Query `aa_parameters` for one top-level `device_index`; rack-chain traversal is not currently implemented.

The extension uses the upstream main-thread dispatcher for reads as well as writes. A legacy `get_track_info`/`get_mixer_state` may access `arm` on a group and fail. Do not interpret that exception as an empty project; use `aa_` inspection or a narrower supported query.

Treat indices as temporary. Reconfirm names after inserts/reorders, and do not reuse device/parameter indices from another set. `str(parameter)` is the display value, while its numeric `value` may be normalized. A mixer value of 0.85 and an XML linear gain of 0.85 do not mean the same thing. Read min/max/display instead of applying a universal conversion.

## Safe parameter batches

Each edit includes scope/index, `expected_track_name`, `device_index`, `expected_device_name`, `parameter_index`, `expected_parameter_name`, `expected_value` and `value`. Build the plan immediately before applying with `parameter_plan()`; its deadline prevents stale queued writes. All preconditions are checked before any change. Automated parameters are rejected instead of silently overriding automation. Use an envelope workflow for those.

```python
from ableton_agent.live import LiveClient, parameter_plan
client = LiveClient(journal_dir="local/journal")
# edits come from an actual fresh aa_parameters query, not a copied preset.
result = client.call("aa_set_parameters", parameter_plan(edits), allow_write=True)
```

Rollback is attempted if a setter/readback fails, and failures are reported. It is not a database transaction and cannot undo arbitrary external user activity. A transport timeout has an uncertain outcome; inspect the state and journal before doing anything else. Do not repeat a write merely because the response was lost.

The client additionally permits a small list of explicit transport/mixer commands behind `--write --journal ...`. Those legacy commands lack the extension's identity guards; inspect immediately before/after. No hardware setup, remote eval, recording toggle, deletion, save or open command is invented.

## Why an effect may be silent

Check in this order: clip exists at the expected native position → clip not muted → track active → parent group active → current solo context → device active → correct parameter/sends → output routing → return active → master path → actual meter/render. A copied muted spare track stays muted unless explicitly changed. A visible offline XML clip can disappear after a native load when events are unordered.

Do not compensate for a routing/mute problem with +12 dB. Measure the effect layer in context first. Temporary solo/mute/send overrides need exact state restoration in `finally`, including failures. Do not blindly “re-enable all automation” when the user already had intentional overrides.

## Saving and UI fallback

Current extension capabilities explicitly report save/open/Collect All unavailable. If the host has another supported capability, use it; otherwise ask the user for the precise native action, once, and continue independent work. Respect a manual save/open preference.

An observed Windows Live installation crashed during accessibility-tree interrogation. For a similar environment, prefer the connector and filesystem inspection, then screenshot-only computer use if needed. Do not turn that incident into a universal ban on UI automation. Never bypass an explicit user stop.
