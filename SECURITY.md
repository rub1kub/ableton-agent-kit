# Local trust boundary

The tools operate on files and a local LiveMCP TCP endpoint. They do not upload audio. The optional stdio MCP server restricts file paths to `ABLETON_AGENT_ROOTS` (current working directory by default) and disables parameter writes unless `ABLETON_AGENT_WRITE=1`.

LiveMCP itself is a trusted local control surface, not a secure multi-user service. The underlying server may expose commands beyond this toolkit's allowlist. Keep its listener on loopback, do not forward port 9877, and do not expose it to a network. The extension does not add authentication to upstream LiveMCP.

Project operations create new outputs. File hashes prevent edits based on stale disk versions; they cannot detect unsaved edits held only in Live. Parameter writes journal the request and outcome, require expected identities and values, and reject automated parameters. A timeout means an uncertain outcome, not proof of failure. Inspect state before retrying.

Audio capture includes the target process tree. Use the correct PID and an authorized recording. ASIO/exclusive paths may not be captured by WASAPI; silence is not proof the mix is silent. Never change devices to work around this without user direction.

Reports can contain track names, file paths and timing. Keep them local. `.gitignore` is a convenience, not a privacy audit. Before publishing, inspect tracked files and staged diffs.

Please report vulnerabilities through GitHub's private security reporting if enabled. Do not post tokens, private projects or audio in public issues.
