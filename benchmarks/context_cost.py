"""Reproducible synthetic context-size comparison, not a real-project cost claim."""
import argparse
import json
from pathlib import Path


def benchmark():
    import tiktoken
    encoder = tiktoken.get_encoding("cl100k_base")
    full = {"tracks": [{"name": f"Track {i}", "mute": False, "devices": [
        {"index": j, "name": f"Device {j}", "parameters": [
            {"index": k, "name": f"Parameter {k}", "value": 0.5, "min": 0, "max": 1, "display": "50 %"}
            for k in range(50)]} for j in range(8)]} for i in range(24)]}
    compact = {"tracks": [{"name": t["name"], "mute": t["mute"],
                "devices": [{"index": d["index"], "name": d["name"]} for d in t["devices"]]}
                for t in full["tracks"]]}
    target = full["tracks"][3]["devices"][2]
    def size(obj):
        return len(encoder.encode(json.dumps(obj, ensure_ascii=False, separators=(",", ":"))))
    root = Path(__file__).resolve().parents[1]
    entry = (root / "skills/ableton-mix/SKILL.md").read_text(encoding="utf-8")
    refs = list((root / "skills/ableton-mix/references").glob("*.md"))
    all_refs = "\n".join(p.read_text(encoding="utf-8") for p in refs)
    return {"benchmark": "synthetic orientation and one-device inspection", "tokenizer": "cl100k_base",
            "scope": "24 tracks, 8 devices each, 50 parameters each; NOT measured model billing or a real song",
            "question": "Find track/device names and inspect one selected device; other parameter values are unnecessary",
            "eager_full_state_tokens": size(full),
            "compact_inventory_plus_selected_device_tokens": size(compact) + size(target),
            "skill_entry_tokens": len(encoder.encode(entry)),
            "entry_plus_all_references_tokens": len(encoder.encode(entry + all_refs)),
            "limitations": "Pagination adds some framing. Savings depend on task; eventually inspecting every parameter reduces the advantage."}


if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--out")
    args = p.parse_args()
    result = benchmark()
    if args.out:
        with Path(args.out).open("x", encoding="utf-8") as f:
            json.dump(result, f, indent=2)
    print(json.dumps(result, indent=2))
