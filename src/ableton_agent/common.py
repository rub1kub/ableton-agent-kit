"""Bounded, deterministic reports; never serialize NaN or Infinity."""
import hashlib
import json
import math
import os
import tempfile
from pathlib import Path


def sha256(path):
    h = hashlib.sha256()
    with Path(path).open("rb") as f:
        for block in iter(lambda: f.read(1024 * 1024), b""):
            h.update(block)
    return h.hexdigest()


def clean(value):
    if isinstance(value, dict):
        return {str(k): clean(v) for k, v in value.items()}
    if isinstance(value, (list, tuple)):
        return [clean(v) for v in value]
    if isinstance(value, float) and not math.isfinite(value):
        return None
    if isinstance(value, Path):
        return str(value)
    return value


def json_text(value):
    return json.dumps(clean(value), ensure_ascii=False, indent=2, allow_nan=False)


def write_new(path, content):
    """Exclusive creation; never silently overwrite an existing artifact."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    with p.open("xb") as f:
        f.write(content.encode("utf-8") if isinstance(content, str) else content)


def atomic_replace(path, content):
    """For explicitly replaceable caches only, not user projects."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    fd, tmp = tempfile.mkstemp(dir=p.parent)
    try:
        with os.fdopen(fd, "wb") as f:
            f.write(content.encode("utf-8") if isinstance(content, str) else content)
        os.replace(tmp, p)
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)


def finite(value, name="value"):
    n = float(value)
    if not math.isfinite(n):
        raise ValueError(f"{name} must be finite")
    return n


def diff(a, b, path="", limit=100):
    """Bounded semantic JSON diff; truncation is explicit."""
    changes = []
    def walk(x, y, p):
        if len(changes) > limit:
            return
        if isinstance(x, dict) and isinstance(y, dict):
            for k in sorted(x.keys() | y.keys()):
                if k not in x or k not in y:
                    changes.append({"path": p + "/" + k, "before": x.get(k), "after": y.get(k)})
                else:
                    walk(x[k], y[k], p + "/" + k)
        elif x != y:
            changes.append({"path": p, "before": x, "after": y})
    walk(a, b, path)
    return {"changes": changes[:limit], "truncated": len(changes) > limit}
