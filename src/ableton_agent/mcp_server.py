"""Optional stdio MCP bridge. Reads by default; paths restricted to explicit roots."""
import os
from pathlib import Path

from .common import json_text, write_new


def allowed(path):
    p = Path(path).resolve()
    roots = [Path(r).resolve() for r in os.environ.get("ABLETON_AGENT_ROOTS", str(Path.cwd())).split(os.pathsep) if r]
    if not any(p.is_relative_to(root) for root in roots):
        raise ValueError("Path is outside ABLETON_AGENT_ROOTS")
    return p


def main():
    from mcp.server.fastmcp import FastMCP
    from mcp.types import ToolAnnotations
    from .live import LiveClient, parameter_plan
    from .als import audit
    from .audio import analyze, compare
    from .music import echo_plan
    server = FastMCP("Ableton Agent Kit")

    @server.tool(annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False))
    def project_audit(path: str, report_path: str) -> dict:
        """Audit an ALS and write detailed private evidence; no project modification."""
        result = audit(allowed(path))
        write_new(allowed(report_path), json_text(result))
        return {"report": report_path, "static_ok": result["static_ok"],
                "errors": result["errors"], "warnings": result["warnings"],
                "native_load_verified": False}

    @server.tool(annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False))
    def audio_analyze(path: str, report_path: str, bpm: float | None = None) -> dict:
        """Analyze loudness, stereo, gap candidates and optional grid; no subjective verdict."""
        result = analyze(allowed(path), bpm)
        write_new(allowed(report_path), json_text(result))
        return {"report": report_path, "metrics": result["metrics"], "gap_candidates": len(result["gap_candidates"])}

    @server.tool(annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False, idempotentHint=True))
    def audio_compare(reference: str, candidate: str) -> dict:
        """Compare levels and propose level matching; does not process either file."""
        return compare(allowed(reference), allowed(candidate))

    @server.tool(annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False, idempotentHint=True))
    def live_snapshot(offset: int = 0, limit: int = 32) -> dict:
        """Compact paginated native state, robust to group/return arm properties."""
        return LiveClient().snapshot(offset, limit)

    @server.tool(annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False, idempotentHint=True))
    def live_read(command: str, params: dict | None = None) -> dict:
        """Read-only allowlisted LiveMCP query. Use bounded aa_ queries for large sets."""
        result = LiveClient().call(command, params)
        if len(json_text(result)) > 24000:
            return {"error": "Response too large; use paginated aa_ queries or CLI --out"}
        return {"result": result}

    @server.tool(annotations=ToolAnnotations(readOnlyHint=True, destructiveHint=False, idempotentHint=True))
    def plan_word_echo(word_end_s: float, word_duration_s: float, next_phrase_s: float,
                       bpm: float, repeats: int = 2, allow_overlap: bool = False) -> dict:
        """Fit whole-word answers into a gap or explicitly permit artistic overlap."""
        return echo_plan(word_end_s, word_duration_s, next_phrase_s, bpm, repeats, allow_overlap)

    @server.tool(annotations=ToolAnnotations(readOnlyHint=False, destructiveHint=False, idempotentHint=False))
    def live_apply_parameters(edits: list[dict], journal_directory: str) -> dict:
        """Explicit identity/value-guarded write. Requires server ABLETON_AGENT_WRITE=1."""
        if os.environ.get("ABLETON_AGENT_WRITE") != "1":
            raise PermissionError("Write tools disabled; enable ABLETON_AGENT_WRITE=1 for authorized editing")
        return LiveClient(journal_dir=allowed(journal_directory)).call(
            "aa_set_parameters", parameter_plan(edits), allow_write=True)

    server.run(transport="stdio")


if __name__ == "__main__":
    main()
