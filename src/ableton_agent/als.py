"""Conservative inspection and narrow revision of gzip/XML Live Sets.

This is not an Ableton schema implementation. A passing audit does not prove
that Live will load a file; reopen a version and compare the native inventory.
"""
import copy
import gzip
import math
import shutil
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path, PureWindowsPath

from defusedxml import ElementTree as SafeET

from .common import finite, sha256, write_new, json_text

MAX_XML = 128 * 1024 * 1024
MIXER = "DeviceChain/Mixer"
EVENTS = "DeviceChain/MainSequencer/Sample/ArrangerAutomation/Events"


def value(node, path, default=None):
    found = node.find(path)
    return found.get("Value", default) if found is not None else default


def load(path):
    with gzip.open(path, "rb") as f:
        raw = f.read(MAX_XML + 1)
    if len(raw) > MAX_XML:
        raise ValueError("ALS decompressed XML exceeds 128 MiB limit")
    root = SafeET.fromstring(raw)
    if root.tag != "Ableton" or root.find("LiveSet") is None:
        raise ValueError("Not a recognized Ableton Live Set")
    return root


def tracks(root):
    return list(root.find("LiveSet/Tracks"))


def track_name(track):
    return value(track, "Name/EffectiveName", value(track, "Name/UserName", ""))


def arrangement_clips(track):
    return list(track.findall(EVENTS + "/AudioClip")) + list(
        track.findall("DeviceChain/MainSequencer/ClipTimeable/ArrangerAutomation/Events/MidiClip"))


def project_root(path):
    p = Path(path).resolve().parent
    for candidate in (p, *p.parents):
        if (candidate / "Ableton Project Info").is_dir():
            return candidate
    return p


def resolve_media(ref, base):
    relative = value(ref, "RelativePath", "")
    absolute = value(ref, "Path", "")
    candidates = []
    if relative and not PureWindowsPath(relative).is_absolute() and not Path(relative).is_absolute():
        # Windows paths also work when auditing a transported project on Linux.
        candidates.append(base / relative.replace("\\", "/"))
    if absolute:
        candidates.append(Path(absolute))
    return next((p.resolve() for p in candidates if p.is_file()), None)


def summary(root):
    rows = []
    for t in tracks(root):
        clips = arrangement_clips(t)
        rows.append({"id": t.get("Id"), "name": track_name(t), "kind": t.tag,
                     "active": value(t, MIXER + "/Speaker/Manual"),
                     "group_id": value(t, "TrackGroupId"),
                     "output": value(t, "DeviceChain/AudioOutputRouting/Target"),
                     "devices": [n.tag for n in t.findall("DeviceChain/DeviceChain/Devices/*")],
                     "clips": [{"id": c.get("Id"), "name": value(c, "Name"),
                                "start_beats": float(value(c, "CurrentStart", c.get("Time", 0))),
                                "end_beats": float(value(c, "CurrentEnd", 0))} for c in clips]})
    main = root.find("LiveSet/MainTrack")
    if main is None:
        main = root.find("LiveSet/MasterTrack")
    return {"creator": root.get("Creator"), "schema": root.get("MinorVersion"),
            "tempo": float(value(main, MIXER + "/Tempo/Manual", 120)) if main is not None else None,
            "tracks": rows}


def audit(path, root=None):
    path = Path(path)
    root = root if root is not None else load(path)
    base = project_root(path)
    errors, warnings = [], []
    scene_count = len(root.findall("LiveSet/Scenes/Scene"))
    for t in tracks(root):
        # Native Group/Return tracks can legitimately keep empty placeholder lists.
        # Scene slots belong to ordinary Audio/MIDI tracks, not every XML element named ClipSlotList.
        slot_lists = t.findall(".//ClipSlotList") if t.tag in ("AudioTrack", "MidiTrack") else []
        for slots in slot_lists:
            if len(slots) != scene_count:
                errors.append({"code": "slot_count_mismatch", "track": track_name(t),
                               "slots": len(slots), "scenes": scene_count})
        for events in t.findall(".//ArrangerAutomation/Events"):
            times = [float(c.get("Time", 0)) for c in events if c.tag in ("AudioClip", "MidiClip")]
            if not all(math.isfinite(n) for n in times) or times != sorted(times):
                errors.append({"code": "unordered_arrangement_events", "track": track_name(t)})
        for clip in arrangement_clips(t):
            a = float(value(clip, "CurrentStart", 0))
            b = float(value(clip, "CurrentEnd", 0))
            if not math.isfinite(a + b) or b <= a:
                errors.append({"code": "invalid_clip_bounds", "track": track_name(t), "clip": clip.get("Id")})
    ids = [n.get("Id") for n in root.iter() if n.get("Id") is not None and (
        n.tag.endswith(("AutomationTarget", "ModulationTarget")) or n.tag == "Pointee"
        or n.tag.startswith("ControllerTargets."))]
    duplicate = [i for i, count in Counter(ids).items() if count > 1]
    if duplicate:
        errors.append({"code": "duplicate_target_ids", "ids": duplicate[:30]})
    known = set(ids)
    missing = sorted({n.get("Value") for n in root.findall(".//EnvelopeTarget/PointeeId")
                      if n.get("Value") not in known})
    if missing:
        errors.append({"code": "unresolved_envelope_targets", "ids": missing[:30]})
    next_id = value(root.find("LiveSet"), "NextPointeeId")
    if next_id and ids and int(next_id) <= max(int(n) for n in ids):
        errors.append({"code": "next_pointee_id_too_low"})
    media = {}
    for ref in root.findall(".//SampleRef/FileRef"):
        source = resolve_media(ref, base)
        label = value(ref, "RelativePath") or value(ref, "Path") or "<empty>"
        if source:
            media[str(source)] = {"exists": True, "in_project": source.is_relative_to(base)}
        else:
            media[label] = {"exists": False}
    missing_media = [p for p, info in media.items() if not info["exists"]]
    if missing_media:
        errors.append({"code": "missing_media", "files": missing_media})
    external = [p for p, info in media.items() if info["exists"] and not info["in_project"]]
    if external:
        warnings.append({"code": "external_media", "count": len(external)})
    return {"schema_version": 1, "set_sha256": sha256(path), "static_ok": not errors,
            "native_load_verified": False, "errors": errors, "warnings": warnings,
            "scene_count": scene_count, "media": media, **summary(root)}


def revise(source, destination, plan):
    """Apply a hash-bound plan to a NEW version. No cloning or XML ID invention."""
    source, destination = Path(source).resolve(), Path(destination).resolve()
    if source == destination or destination.exists():
        raise ValueError("Destination must be a new, distinct file")
    if plan.get("source_sha256") != sha256(source):
        raise ValueError("Source changed since plan; re-read before editing")
    root = load(source)
    before = audit(source, root)
    if before["errors"]:
        raise ValueError("Source fails static audit; diagnose before revising")
    for op in plan.get("operations", []):
        matches = [t for t in tracks(root) if t.get("Id") == str(op.get("track_id"))]
        if len(matches) != 1 or track_name(matches[0]) != op.get("expected_track_name"):
            raise ValueError("Track identity mismatch")
        t = matches[0]
        action = op["action"]
        if action == "set_track_active":
            if not isinstance(op.get("active"), bool):
                raise ValueError("active must be boolean")
            node = t.find(MIXER + "/Speaker/Manual")
            if node is None:
                raise ValueError("Track activator not found")
            node.set("Value", str(op["active"]).lower())
        elif action in ("set_clip_gain_db", "move_audio_clip"):
            clips = [c for c in arrangement_clips(t) if c.tag == "AudioClip" and c.get("Id") == str(op.get("clip_id"))]
            if len(clips) != 1:
                raise ValueError("Audio clip identity ambiguous or absent")
            c = clips[0]
            if action == "set_clip_gain_db":
                gain = finite(op["gain_db"])
                if not -70 <= gain <= 24:
                    raise ValueError("Clip gain must be between -70 and +24 dB")
                c.find("SampleVolume").set("Value", str(10 ** (gain / 20)))
            else:
                start = finite(op["start_beats"])
                if start < 0:
                    raise ValueError("Negative arrangement position")
                delta = start - float(value(c, "CurrentStart"))
                for key in ("CurrentStart", "CurrentEnd"):
                    c.find(key).set("Value", str(float(value(c, key)) + delta))
                c.set("Time", str(start))
        else:
            raise ValueError(f"Unsupported revision operation: {action}")
    for events in root.findall(".//ArrangerAutomation/Events"):
        if all(c.tag in ("AudioClip", "MidiClip") for c in events):
            events[:] = sorted(events, key=lambda c: float(c.get("Time", 0)))
    # Keep media valid when the new version lives in a different folder.
    for ref in root.findall(".//SampleRef/FileRef"):
        resolved = resolve_media(ref, project_root(source))
        if resolved is not None and ref.find("Path") is not None:
            ref.find("Path").set("Value", str(resolved))
    after = audit(source, root)
    if after["errors"]:
        raise ValueError(f"Revision fails audit: {after['errors']}")
    write_new(destination, gzip.compress(ET.tostring(root, encoding="utf-8", xml_declaration=True), mtime=0))
    return {"path": str(destination), "sha256": sha256(destination), "operations": len(plan.get("operations", [])),
            "native_load_verified": False, "next": "Open the new version in Live and compare the native inventory."}


def collect(source, destination):
    """Portable copy of SampleRef audio, not a substitute for Live's full Collect All."""
    source, destination = Path(source).resolve(), Path(destination).resolve()
    if destination.exists():
        raise ValueError("Collection destination must not exist")
    if destination.is_relative_to(project_root(source)):
        raise ValueError("Collect into a separate folder outside the original project root")
    root = copy.deepcopy(load(source))
    refs = root.findall(".//SampleRef/FileRef")
    resolved = [(r, resolve_media(r, project_root(source))) for r in refs]
    if any(p is None for _, p in resolved):
        raise ValueError("Missing media: relink in Live before collecting")
    destination.mkdir(parents=True)
    manifest = []
    for ref, src in resolved:
        digest = sha256(src)
        relative = Path("Samples/Collected") / (digest[:20] + src.suffix.lower())
        target = destination / relative
        if not target.exists():
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, target)
        if sha256(target) != digest:
            raise OSError("Collected media hash mismatch")
        for key, val in (("Path", str(target)), ("RelativePath", relative.as_posix()), ("RelativePathType", "3")):
            node = ref.find(key)
            if node is None:
                node = ET.SubElement(ref, key)
            node.set("Value", val)
        manifest.append({"relative_path": relative.as_posix(), "sha256": digest})
    output = destination / source.name
    write_new(output, gzip.compress(ET.tostring(root, encoding="utf-8", xml_declaration=True), mtime=0))
    write_new(destination / "collection.json", json_text({"audio_files": manifest,
        "scope": "SampleRef audio only; presets, plugin libraries and packs not collected",
        "native_collect_all_performed": False}))
    return {"path": str(output), "audio_files": len({r["relative_path"] for r in manifest}),
            "static_ok": audit(output)["static_ok"], "native_collect_all_performed": False}


def beat_to_source_seconds(clip, beat):
    """Map local warped beat via piecewise markers. Unwarped needs explicit seconds."""
    if value(clip, "IsWarped") != "true":
        raise ValueError("Warp is off: sample/loop offsets are seconds, not beats")
    markers = sorted((float(n.get("BeatTime")), float(n.get("SecTime")))
                     for n in clip.findall("WarpMarkers/WarpMarker"))
    if len(markers) < 2 or any(b[0] <= a[0] or b[1] <= a[1] for a, b in zip(markers, markers[1:])):
        raise ValueError("Need at least two strictly increasing warp markers")
    beat = finite(beat, "beat")
    for a, b in zip(markers, markers[1:]):
        if a[0] <= beat <= b[0]:
            return a[1] + (beat - a[0]) * (b[1] - a[1]) / (b[0] - a[0])
    raise ValueError("Outside warp marker range; extrapolation intentionally disabled")
