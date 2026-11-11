# Backend choice is a capability decision

“Ableton MCP” names several unrelated or forked servers. Identify the connected version, Remote Script and tools/list. Do not confuse raw socket commands with client-facing MCP tools or infer capabilities from port 9877.

## Preferred routes

- **wstierhout/ableton-live-mcp 1.8.1** is the first general-control candidate for the observed Live 12.2.2 workflow: typed tools, `get_session_snapshot`, `session_diff`, batch and `ABLETON_TOOLSETS`. Use connected native tools, current schemas and only the domains needed. The source was inspected; native operation on the user's build still needs acceptance testing.
- **CanArslanDev/ableton-live-mcp 2.3.0** offers integrated rendered analysis, snapshots, memory, mix diagnosis and reference comparison. It uses another SDK major and protocol. Some convenience device loading requires Live 12.3; its SDK renderer targets 12.4.5+ Suite and was described as not yet native-tested. Use it only when those capabilities/version requirements are verified, not because a demo lists more features.
- **Legacy LiveMCP + Agent Kit extension** remains a supported fallback. Use `aa_*` paginated queries and guarded parameter batches. The direct `ableton_agent.live.LiveClient` implements only this newline protocol; it is not a universal Ableton MCP client.
- **Original ahujasid/ableton-mcp** must be judged by its own current interface. Do not assign fork-only features to it.

`backend-plan tools.json --live-version 12.2.2` maps an observed unqualified tools/list to candidate tasks. It does not establish runtime support, activate a server or migrate the installation. Keep full raw inventories on disk; load only the relevant capability/schema into context.

## Important semantic differences

`analyze_mix` in the inspected wstierhout release is explicitly a **session/fader-state heuristic**, not audio analysis. `mix_doctor` in the expanded fork records stems and computes measurements. Neither is proof that the agent has heard the result or that a frequency collision is artistically bad.

`record_section` in the inspected wstierhout code creates an armed temporary recording track and runs transport. It is not a read-only export. Its error cleanup does not restore every transport/record/armed state; prefer passive capture or native export until a guarded workflow is tested. Recording-based diagnostics in any fork need inspection of routing and restoration before unattended use.

`write_automation` may address Session clip envelopes, while audio-track Arrangement automation may need real-time recording or another workflow. Never replace an entire envelope when the user requested only one phrase.

`try_save_project` is conditional on an API method existing. Check the actual result and file state. Do not assume save/open/Collect All exists because another backend has a similarly named tool.

## Migration and rollback

Use separate Python environments and matching server/Remote Script versions. Preserve the prior setup, close Live before replacing scripts, and avoid two listeners competing for one port. Do not change audio devices or hardware controller rows. Native tests belong in a disposable set; a source-code comparison is not permission to overwrite the active recording project.

The full pinned comparison and source notes are in the public repository's `docs/backend-comparison.md` and `docs/research.md`. The decision can change with a new tested release; keep version facts separate from the user's musical goals.
