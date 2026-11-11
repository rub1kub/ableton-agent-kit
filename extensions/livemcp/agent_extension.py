"""Original additive LiveMCP handlers; no upstream code is redistributed.

Register ALL these handlers in the upstream WRITE registry so every LOM access
runs on Live's main thread. Commands beginning aa_ do not replace upstream APIs.
This module uses only the Python standard library available inside Live.
"""
import math
import time

VERSION = "0.1.0"


def safe(obj, name, default=None):
    try:
        return getattr(obj, name)
    except Exception:
        return default


def page(params, maximum=128):
    offset, limit = int(params.get("offset", 0)), int(params.get("limit", 32))
    if offset < 0 or not 1 <= limit <= maximum:
        raise ValueError("Invalid pagination")
    return offset, limit


def locate(song, params):
    scope = params.get("scope", "track")
    index = int(params.get("index", 0))
    pool = {"track": list(song.tracks), "return": list(song.return_tracks),
            "master": [song.master_track]}.get(scope)
    if pool is None or not 0 <= index < len(pool):
        raise ValueError("Invalid track scope/index")
    return pool[index]


def parameter_info(p, index):
    return {"index": index, "name": p.name, "value": p.value, "min": p.min, "max": p.max,
            "display": str(p), "quantized": bool(p.is_quantized), "enabled": bool(p.is_enabled),
            "automation_state": int(safe(p, "automation_state", 0))}


def track_info(song, track, scope, index):
    parent = safe(track, "group_track")
    mixer = track.mixer_device
    can_arm = bool(safe(track, "can_be_armed", False))
    output = safe(track, "output_routing_type")
    return {"scope": scope, "index": index, "name": track.name,
            "kind": "group" if safe(track, "is_foldable", False) else scope,
            "parent": safe(parent, "name"), "mute": bool(safe(track, "mute", False)),
            "solo": bool(safe(track, "solo", False)), "can_arm": can_arm,
            "arm": bool(track.arm) if can_arm else None,
            "volume": parameter_info(mixer.volume, 0), "pan": parameter_info(mixer.panning, 0),
            "output": safe(output, "display_name"),
            "devices": [{"index": i, "name": d.name, "class_name": d.class_name,
                         "active": bool(safe(d, "is_active", True))} for i, d in enumerate(track.devices)],
            "arrangement_clip_count": len(safe(track, "arrangement_clips", [])),
            "take_lane_count": len(safe(track, "take_lanes", []))}


def capabilities(cs, params):
    return {"extension_version": VERSION, "commands": sorted(HANDLERS),
            "save_set": False, "open_set": False, "collect_all_and_save": False,
            "all_lom_on_main_thread": True, "parameter_writes": "compare-and-set with rollback attempt",
            "rack_chain_parameters": False, "max_parameter_edits": 32}


def snapshot(cs, params):
    song = cs.song()
    offset, limit = page(params)
    items = [("track", i, t) for i, t in enumerate(song.tracks)]
    items += [("return", i, t) for i, t in enumerate(song.return_tracks)]
    items += [("master", 0, song.master_track)]
    app = cs.application()
    return {"extension_available": True, "version": [safe(app, "get_major_version", lambda: None)(),
                                                      safe(app, "get_minor_version", lambda: None)(),
                                                      safe(app, "get_bugfix_version", lambda: None)()],
            "set_name": safe(song, "name"), "tempo": song.tempo,
            "signature": [song.signature_numerator, song.signature_denominator],
            "transport": {"beat": song.current_song_time, "playing": bool(song.is_playing),
                          "recording": bool(song.record_mode)},
            "offset": offset, "total": len(items),
            "next_offset": offset + limit if offset + limit < len(items) else None,
            "tracks": [track_info(song, t, scope, i) for scope, i, t in items[offset:offset + limit]]}


def one_track(cs, params):
    song = cs.song()
    return track_info(song, locate(song, params), params.get("scope", "track"), int(params.get("index", 0)))


def clips(cs, params):
    track = locate(cs.song(), params)
    offset, limit = page(params)
    items = list(safe(track, "arrangement_clips", []))
    return {"total": len(items), "next_offset": offset + limit if offset + limit < len(items) else None,
            "clips": [{"index": i, "name": c.name, "start_beats": c.start_time, "end_beats": c.end_time,
                       "muted": bool(c.muted), "audio": bool(c.is_audio_clip)}
                      for i, c in enumerate(items) if offset <= i < offset + limit]}


def parameters(cs, params):
    track = locate(cs.song(), params)
    index = int(params["device_index"])
    if not 0 <= index < len(track.devices):
        raise ValueError("Device index out of range")
    device = track.devices[index]
    offset, limit = page(params)
    return {"track": track.name, "device": device.name, "class_name": device.class_name,
            "total": len(device.parameters),
            "next_offset": offset + limit if offset + limit < len(device.parameters) else None,
            "parameters": [parameter_info(p, i) for i, p in enumerate(device.parameters)
                           if offset <= i < offset + limit]}


def meters(cs, params):
    song = cs.song()
    offset, limit = page(params)
    pool = list(song.tracks) + list(song.return_tracks) + [song.master_track]
    return {"beat": song.current_song_time, "playing": bool(song.is_playing),
            "total": len(pool), "offset": offset,
            "meters": [{"index_all": i, "name": t.name, "left": safe(t, "output_meter_left"),
                        "right": safe(t, "output_meter_right"), "level": safe(t, "output_meter_level")}
                       for i, t in enumerate(pool) if offset <= i < offset + limit]}


def set_parameters(cs, params):
    deadline = float(params.get("deadline_unix_s", 0))
    if not math.isfinite(deadline) or not time.time() < deadline <= time.time() + 120:
        raise ValueError("Expired or invalid plan deadline")
    edits = params.get("edits", [])
    if not 1 <= len(edits) <= 32:
        raise ValueError("Plan needs 1..32 parameter edits")
    song = cs.song()
    if song.record_mode:
        raise ValueError("Refusing parameter batch during recording")
    pending, seen = [], set()
    for edit in edits:
        track = locate(song, edit)
        if track.name != edit["expected_track_name"]:
            raise ValueError("Track identity changed")
        di, pi = int(edit["device_index"]), int(edit["parameter_index"])
        identity = (edit.get("scope", "track"), int(edit.get("index", 0)), di, pi)
        if identity in seen:
            raise ValueError("Duplicate parameter in batch")
        seen.add(identity)
        if not 0 <= di < len(track.devices):
            raise ValueError("Device no longer exists")
        device = track.devices[di]
        if device.name != edit["expected_device_name"] or not 0 <= pi < len(device.parameters):
            raise ValueError("Device identity changed")
        param = device.parameters[pi]
        if param.name != edit["expected_parameter_name"] or not param.is_enabled:
            raise ValueError("Parameter identity changed or disabled")
        expected, new = float(edit["expected_value"]), float(edit["value"])
        if not math.isfinite(expected) or not math.isfinite(new) or not param.min <= new <= param.max:
            raise ValueError("Non-finite or out-of-range value")
        if abs(param.value - expected) > 1e-6:
            raise ValueError("Value changed since plan")
        if int(safe(param, "automation_state", 0)) != 0:
            raise ValueError("Automated parameter: edit its envelope rather than override it")
        if param.is_quantized and new != round(new):
            raise ValueError("Quantized parameter needs an integer value")
        pending.append((param, param.value, new))
    changed = []
    song.begin_undo_step()
    try:
        for param, old, new in pending:
            changed.append((param, old))
            param.value = new
            if abs(param.value - new) > 1e-6:
                raise RuntimeError("Parameter readback mismatch")
    except Exception as exc:
        failures = []
        for param, old in reversed(changed):
            try:
                param.value = old
                if abs(param.value - old) > 1e-6:
                    raise RuntimeError("Restore readback mismatch")
            except Exception as restore_error:
                failures.append(str(restore_error))
        raise RuntimeError("Batch failed: %s; rollback failures: %s" % (exc, failures))
    finally:
        song.end_undo_step()
    return {"applied": len(pending), "values": [parameter_info(p, i) for i, (p, _, _) in enumerate(pending)],
            "saved": False}


HANDLERS = {"aa_capabilities": capabilities, "aa_snapshot": snapshot, "aa_track": one_track,
            "aa_clips": clips, "aa_parameters": parameters, "aa_meters": meters,
            "aa_set_parameters": set_parameters}
