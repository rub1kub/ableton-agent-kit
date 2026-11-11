"""Static inventory without importing/executing a third-party server."""
import argparse
import ast
import hashlib
import json
from pathlib import Path


def inspect(root):
    root = Path(root)
    read, write, mcp_tools = set(), set(), set()
    digest = hashlib.sha256()
    files = sorted(root.rglob("*.py"))
    if len(files) > 5000:
        raise ValueError("Select source only, excluding virtual environments")
    for path in files:
        if any(part in (".venv", "__pycache__", ".git") for part in path.parts):
            continue
        data = path.read_bytes()
        digest.update(path.relative_to(root).as_posix().encode() + b"\0" + data)
        tree = ast.parse(data)
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign) and isinstance(node.value, ast.Dict):
                names = {n.id for n in node.targets if isinstance(n, ast.Name)}
                keys = {k.value for k in node.value.keys if isinstance(k, ast.Constant) and isinstance(k.value, str)}
                if names & {"READ_HANDLERS", "_READONLY_COMMANDS"}:
                    read.update(keys)
                if names & {"WRITE_HANDLERS", "_MUTATING_COMMANDS"}:
                    write.update(keys)
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for dec in node.decorator_list:
                    f = dec.func if isinstance(dec, ast.Call) else dec
                    if isinstance(f, ast.Attribute) and f.attr == "tool":
                        mcp_tools.add(node.name)
    return {"source_tree_sha256": digest.hexdigest(), "read_commands": sorted(read),
            "write_commands": sorted(write), "mcp_tool_definitions": sorted(mcp_tools),
            "counts": {"read_commands": len(read), "write_commands": len(write), "mcp_tool_definitions": len(mcp_tools)},
            "executed": False, "limitation": "Static definitions, not necessarily registered or runtime-supported tools"}


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("source")
    p.add_argument("--out")
    args = p.parse_args()
    result = inspect(args.source)
    if args.out:
        with Path(args.out).open("x", encoding="utf-8") as f:
            json.dump(result, f, indent=2)
        print(json.dumps(result["counts"]))
    else:
        print(json.dumps(result, indent=2))
