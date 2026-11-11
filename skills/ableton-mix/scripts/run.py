"""Launch the toolkit using the environment selected by the local installer."""
import json
import subprocess
import sys
from pathlib import Path

runtime = Path(__file__).resolve().parents[1] / "runtime.json"
python = json.loads(runtime.read_text(encoding="utf-8"))["python"] if runtime.exists() else sys.executable
raise SystemExit(subprocess.call([python, "-m", "ableton_agent.cli", *sys.argv[1:]]))
