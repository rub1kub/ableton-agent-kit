"""Bounded LiveMCP transport. Reads never imply permission to mutate a set."""
import hashlib
import json
import socket
import time
import uuid
from pathlib import Path

from .common import json_text, write_new

READ_COMMANDS = frozenset({
    "get_session_info", "get_song_time", "get_record_mode", "get_view_state", "get_session_metadata",
    "get_arrangement_length", "get_arrangement_clips", "get_track_info", "get_track_routing",
    "get_return_tracks", "get_return_track_devices", "get_device_parameters", "get_return_device_parameters",
    "get_master_mixer_state", "get_master_device_parameters", "get_all_track_meters", "get_take_lanes",
    "aa_capabilities", "aa_snapshot", "aa_track", "aa_clips", "aa_parameters", "aa_meters",
})
# Hardware, file saving, deletion, record mode and arbitrary Python are intentionally absent.
WRITE_COMMANDS = frozenset({
    "stop_playback", "start_playback", "set_song_time", "set_selected_track",
    "set_track_volume", "set_track_pan", "set_track_mute", "set_track_solo", "set_track_send",
    "set_device_parameter", "set_return_device_parameter", "set_master_device_parameter",
    "aa_set_parameters",
})


class LiveError(RuntimeError):
    pass


class LiveClient:
    def __init__(self, port=9877, timeout=18, max_response=8 * 1024 * 1024, journal_dir=None):
        self.port = int(port)
        self.timeout = float(timeout)
        self.max_response = int(max_response)
        self.journal_dir = Path(journal_dir) if journal_dir else None

    def call(self, command, params=None, *, allow_write=False):
        is_write = command in WRITE_COMMANDS
        if command not in READ_COMMANDS and not is_write:
            raise ValueError("Command outside the explicit project-only allowlist")
        if is_write and not allow_write:
            raise PermissionError("Mutation requires allow_write=True or CLI --write")
        if is_write and self.journal_dir is None:
            raise ValueError("Mutations require a local journal directory")
        request_id = uuid.uuid4().hex
        request = {"id": request_id, "type": command, "params": params or {}}
        wire = json.dumps(request, allow_nan=False).encode("utf-8") + b"\n"
        if len(wire) > 65536:
            raise ValueError("Request exceeds 64 KiB")
        if is_write:
            write_new(self.journal_dir / (request_id + ".request.json"), json_text(request))
        try:
            with socket.create_connection(("127.0.0.1", self.port), timeout=self.timeout) as sock:
                sock.settimeout(self.timeout)
                sock.sendall(wire)
                with sock.makefile("rb") as stream:
                    raw = stream.readline(self.max_response + 1)
            if len(raw) > self.max_response or not raw.endswith(b"\n"):
                raise LiveError("Oversized or incomplete LiveMCP response")
            response = json.loads(raw)
            if response.get("id", request_id) != request_id:
                raise LiveError("Response ID mismatch")
            if response.get("status") != "success":
                raise LiveError(str(response.get("error", "Unknown LiveMCP error")))
            result = response.get("result")
        except (OSError, ValueError, LiveError) as exc:
            if is_write:
                write_new(self.journal_dir / (request_id + ".error.json"), json_text({
                    "error": str(exc), "outcome": "unconfirmed; inspect state before any retry"}))
            raise LiveError(f"{command}: {exc}" + ("; write outcome unconfirmed, do not retry blindly" if is_write else "")) from exc
        if is_write:
            write_new(self.journal_dir / (request_id + ".result.json"), json_text(result))
        return result

    def snapshot(self, offset=0, limit=32):
        try:
            return self.call("aa_snapshot", {"offset": offset, "limit": limit})
        except LiveError as exc:
            # A disconnected/failed server is not evidence that the extension is absent.
            if "Unknown command" not in str(exc):
                raise
            info = self.call("get_session_info")
            return {"extension_available": False, "native_session": info,
                    "limitation": "Install the extension for safe group/return inventory and bounded detailed queries."}


def fingerprint(data):
    return hashlib.sha256(json.dumps(data, sort_keys=True, ensure_ascii=False, allow_nan=False).encode()).hexdigest()


def parameter_plan(edits, ttl_s=30):
    """Native extension checks every identity and expected value before writing."""
    if not 0 < ttl_s <= 120:
        raise ValueError("Plan lifetime must be 0..120 seconds")
    return {"edits": edits, "deadline_unix_s": time.time() + ttl_s}


def transport_check(samples, bpm, tolerance_s=0.8):
    """Validate a capture's monotonic transport against wall time; never repair history."""
    failures = []
    for a, b in zip(samples, samples[1:]):
        wall = b["wall_s"] - a["wall_s"]
        song = (b["beat"] - a["beat"]) * 60 / bpm
        if wall <= 0 or song < 0 or abs(song - wall) > tolerance_s or not b.get("playing", True):
            failures.append({"from": a, "to": b, "transport_delta_s": song, "wall_delta_s": wall})
    return {"valid": len(samples) >= 2 and not failures, "samples": len(samples), "discontinuities": failures}
