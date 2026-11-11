"""CLI prints compact status; detailed reports live in local files via --out."""
import argparse
import importlib.util
import json
import sys
from pathlib import Path

from . import __version__
from .common import json_text, write_new, diff


def read_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8-sig"))


def parser():
    p = argparse.ArgumentParser(prog="ableton-agent")
    p.add_argument("--version", action="version", version=__version__)
    sub = p.add_subparsers(dest="command", required=True)
    doctor = sub.add_parser("doctor", help="Local optional dependencies and TCP availability")
    doctor.add_argument("--live", action="store_true")
    audit = sub.add_parser("als-audit")
    audit.add_argument("path")
    audit.add_argument("--out")
    revise = sub.add_parser("als-revise", help="Hash-bound limited edit plan, always a new version")
    revise.add_argument("source")
    revise.add_argument("destination")
    revise.add_argument("--plan", required=True)
    collect = sub.add_parser("als-collect", help="Copy SampleRef audio; not native Collect All")
    collect.add_argument("source")
    collect.add_argument("destination")
    analyze = sub.add_parser("audio-analyze")
    analyze.add_argument("path")
    analyze.add_argument("--bpm", type=float)
    analyze.add_argument("--sections", help="JSON array: name/start_s/end_s")
    analyze.add_argument("--out")
    analyze.add_argument("--cache", help="Local content-addressed analysis cache directory")
    masking = sub.add_parser("masking-proxy")
    masking.add_argument("vocal")
    masking.add_argument("accompaniment")
    masking.add_argument("--aligned", action="store_true")
    masking.add_argument("--out")
    backend = sub.add_parser("backend-plan")
    backend.add_argument("tools", help="JSON tools/list result or array, unqualified names")
    backend.add_argument("--live-version")
    backend.add_argument("--out")
    compare = sub.add_parser("audio-compare")
    compare.add_argument("reference")
    compare.add_argument("candidate")
    compare.add_argument("--out")
    ab = sub.add_parser("ab-pack")
    ab.add_argument("reference")
    ab.add_argument("candidate")
    ab.add_argument("destination")
    ab.add_argument("--start", type=float, default=0)
    ab.add_argument("--duration", type=float, default=12)
    plot = sub.add_parser("audio-plot")
    plot.add_argument("path")
    plot.add_argument("output")
    for command in ("pitch", "key"):
        cmd = sub.add_parser(command)
        cmd.add_argument("path")
        cmd.add_argument("--start", type=float, default=0)
        cmd.add_argument("--end", type=float)
        cmd.add_argument("--out")
    asr = sub.add_parser("transcribe")
    asr.add_argument("path")
    asr.add_argument("--model", required=True, help="Existing local model directory; no download")
    asr.add_argument("--language")
    asr.add_argument("--out", required=True)
    echo = sub.add_parser("echo-plan")
    echo.add_argument("--word-end", type=float, required=True)
    echo.add_argument("--word-duration", type=float, required=True)
    echo.add_argument("--next-phrase", type=float, required=True)
    echo.add_argument("--bpm", type=float, required=True)
    echo.add_argument("--repeats", type=int, default=2)
    echo.add_argument("--allow-overlap", action="store_true")
    snapshot = sub.add_parser("live-snapshot")
    snapshot.add_argument("--offset", type=int, default=0)
    snapshot.add_argument("--limit", type=int, default=32)
    snapshot.add_argument("--out")
    call = sub.add_parser("live-call")
    call.add_argument("name")
    call.add_argument("--params", help="JSON file; avoids shell quoting mistakes")
    call.add_argument("--write", action="store_true")
    call.add_argument("--journal")
    call.add_argument("--out")
    capture = sub.add_parser("capture", help="Passive Windows process capture; does not move transport")
    capture.add_argument("--pid", type=int, required=True)
    capture.add_argument("--seconds", type=float, required=True)
    capture.add_argument("--output", required=True)
    delta = sub.add_parser("diff")
    delta.add_argument("before")
    delta.add_argument("after")
    delta.add_argument("--out")
    release = sub.add_parser("release")
    release.add_argument("source")
    release.add_argument("--cover", required=True)
    release.add_argument("--metadata", required=True)
    release.add_argument("--destination", required=True)
    return p


def run(args):
    c = args.command
    if c == "doctor":
        result = {"version": __version__, "python": sys.version.split()[0], "platform": sys.platform,
                  "optional": {m: importlib.util.find_spec(m) is not None for m in
                               ("mcp", "librosa", "matplotlib", "faster_whisper", "mutagen", "imageio_ffmpeg", "comtypes")}}
        if args.live:
            from .live import LiveClient
            try:
                result["live"] = LiveClient(timeout=3).snapshot(limit=1)
            except Exception as exc:
                result["live"] = {"available": False, "error": str(exc)}
        return result
    if c.startswith("als-"):
        from . import als
        if c == "als-audit":
            return als.audit(args.path)
        if c == "als-revise":
            return als.revise(args.source, args.destination, read_json(args.plan))
        return als.collect(args.source, args.destination)
    if c.startswith("audio-"):
        from . import audio
        if c == "audio-analyze":
            options = {"bpm": args.bpm, "sections": read_json(args.sections) if args.sections else None}
            if args.cache:
                from .cache import cached_analysis
                result, cache = cached_analysis(args.path, args.cache, options)
                return {**result, "cache": cache}
            return audio.analyze(args.path, **options)
        if c == "audio-compare":
            return audio.compare(args.reference, args.candidate)
        return audio.figure(args.path, args.output)
    if c == "masking-proxy":
        from .audio import masking_proxy
        return masking_proxy(args.vocal, args.accompaniment, args.aligned)
    if c == "ab-pack":
        from .listening import ab_pack
        return ab_pack(args.reference, args.candidate, args.destination, args.start, args.duration)
    if c == "backend-plan":
        from .backends import plan_backend
        inventory = read_json(args.tools)
        return plan_backend(inventory.get("tools", []) if isinstance(inventory, dict) else inventory, args.live_version)
    if c in ("pitch", "key", "transcribe", "echo-plan"):
        from . import music
        if c == "pitch":
            return music.pitch_report(args.path, args.start, args.end)
        if c == "key":
            return music.key_candidates(args.path, args.start, args.end)
        if c == "transcribe":
            return music.transcribe(args.path, args.model, args.language)
        return music.echo_plan(args.word_end, args.word_duration, args.next_phrase, args.bpm, args.repeats, args.allow_overlap)
    if c.startswith("live-"):
        from .live import LiveClient
        client = LiveClient(journal_dir=getattr(args, "journal", None))
        if c == "live-snapshot":
            return client.snapshot(args.offset, args.limit)
        return client.call(args.name, read_json(args.params) if args.params else {}, allow_write=args.write)
    if c == "capture":
        import soundfile as sf
        from .windows_capture import ProcessCapture, SAMPLE_RATE
        output = Path(args.output)
        if output.exists() or output.with_suffix(".capture.json").exists():
            raise ValueError("Capture output already exists")
        output.parent.mkdir(parents=True, exist_ok=True)
        with ProcessCapture(args.pid) as capture:
            y, report = capture.record(args.seconds, lambda elapsed: print(f"Captured {elapsed:.0f}s", file=sys.stderr))
        if not len(y):
            raise RuntimeError("No audio packets: target may be silent or use an unsupported audio path")
        sf.write(output, y, SAMPLE_RATE, subtype="PCM_16")
        write_new(output.with_suffix(".capture.json"), json_text(report))
        return {"output": str(output), **report}
    if c == "diff":
        return diff(read_json(args.before), read_json(args.after))
    if c == "release":
        from .release import package
        return package(args.source, args.cover, args.destination, read_json(args.metadata))
    raise ValueError("Unknown command")


def main():
    for stream in (sys.stdout, sys.stderr):
        if hasattr(stream, "reconfigure"):
            stream.reconfigure(encoding="utf-8")
    args = parser().parse_args()
    try:
        result = run(args)
        if getattr(args, "out", None):
            write_new(args.out, json_text(result))
            compact = {"report": args.out}
            for field in ("static_ok", "errors", "warnings", "metrics", "candidate_match_gain_db"):
                if field in result:
                    compact[field] = result[field]
            print(json_text(compact))
        else:
            encoded = json_text(result)
            if len(encoded) > 24000:
                raise ValueError("Report exceeds compact output budget; rerun with --out where supported")
            print(encoded)
        return 2 if isinstance(result, dict) and result.get("static_ok") is False else 0
    except (ValueError, OSError, RuntimeError, ImportError) as exc:
        print(json_text({"error": str(exc), "type": type(exc).__name__}), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
