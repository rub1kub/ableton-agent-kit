"""Content-addressed analysis cache; file identity, options, code and libraries matter."""
import hashlib
import importlib.metadata
import json
from pathlib import Path

from .common import sha256, atomic_replace, json_text


def cached_analysis(source, directory, options=None):
    from . import audio
    options = options or {}
    before = sha256(source)
    versions = {name: importlib.metadata.version(name) for name in ("numpy", "scipy", "soundfile", "pyloudnorm")}
    identity = {"source_sha256": before, "options": options, "libraries": versions,
                "implementation_sha256": sha256(audio.__file__), "cache_schema": 1}
    key = hashlib.sha256(json.dumps(identity, sort_keys=True).encode()).hexdigest()
    target = Path(directory) / (key + ".json")
    if target.exists():
        try:
            entry = json.loads(target.read_text(encoding="utf-8"))
            if entry["identity"] == identity and entry["report"]["source_sha256"] == before:
                return entry["report"], {"hit": True, "key": key}
        except (ValueError, KeyError, TypeError):
            pass
    report = audio.analyze(source, **options)
    if sha256(source) != before or report["source_sha256"] != before:
        raise RuntimeError("Audio changed during analysis; report not cached")
    atomic_replace(target, json_text({"identity": identity, "report": report}))
    return report, {"hit": False, "key": key}
