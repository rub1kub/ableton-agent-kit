"""Create an additive LiveMCP installation copy without changing the active script."""
import argparse
import ast
import hashlib
import json
import shutil
from pathlib import Path

MARKER = "# ableton-agent-kit additive registration"
REGISTRATION = '''
# ableton-agent-kit additive registration
_aa_original_write_handlers = get_all_write_handlers

def get_all_write_handlers():
    from .agent_extension import HANDLERS
    handlers = _aa_original_write_handlers()
    overlap = set(handlers).intersection(HANDLERS)
    if overlap:
        raise ValueError("Agent extension command collision: %s" % sorted(overlap))
    handlers.update(HANDLERS)
    return handlers
'''


def stage(source, output):
    source, output = Path(source).resolve(), Path(output).resolve()
    if output.exists() or output.is_relative_to(source) or source.is_relative_to(output):
        raise ValueError("Output must be a new directory outside the source tree")
    registry = source / "handlers/__init__.py"
    server = source / "server.py"
    text = registry.read_text(encoding="utf-8")
    server_text = server.read_text(encoding="utf-8")
    if MARKER in text:
        raise ValueError("Source is already patched; use an unmodified backup")
    functions = {n.name for n in ast.parse(text).body if isinstance(n, ast.FunctionDef)}
    if "get_all_write_handlers" not in functions or "_run_on_main_thread" not in server_text:
        raise ValueError("Unsupported LiveMCP layout; inspect its dispatcher manually")
    ast.parse(text + REGISTRATION)
    shutil.copytree(source, output, ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".git"))
    (output / "handlers/__init__.py").write_text(text + REGISTRATION, encoding="utf-8")
    extension = Path(__file__).resolve().parents[1] / "extensions/livemcp/agent_extension.py"
    shutil.copy2(extension, output / "handlers/agent_extension.py")
    manifest = {"source_registry_sha256": hashlib.sha256(registry.read_bytes()).hexdigest(),
                "extension_sha256": hashlib.sha256(extension.read_bytes()).hexdigest(),
                "installed": False, "reload_required": True}
    (output / "agent-extension-manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    return manifest


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    print(json.dumps(stage(args.source, args.output), indent=2))
