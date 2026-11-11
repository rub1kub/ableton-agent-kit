"""Install just the skill. It uses the separately installed ableton-agent CLI."""
import argparse
import json
import os
import shutil
import sys
from pathlib import Path


def install(destination=None):
    source = Path(__file__).resolve().parents[1] / "skills/ableton-mix"
    codex = Path(os.environ.get("CODEX_HOME", str(Path.home() / ".codex")))
    destination = Path(destination) if destination else codex / "skills/ableton-mix"
    if destination.exists():
        raise ValueError("Skill already exists; compare changes before replacing it")
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(source, destination)
    (destination / "runtime.json").write_text(json.dumps({"python": sys.executable}, indent=2), encoding="utf-8")
    return destination


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--destination", type=Path)
    args = parser.parse_args()
    print(install(args.destination))
