"""Level-matched blinded listening copies. No claim of a scientific listening trial."""
import secrets
from pathlib import Path

import numpy as np
import soundfile as sf

from .audio import read_audio, metrics
from .common import finite, write_new, json_text, sha256


def ab_pack(reference, candidate, destination, start_s=0, duration_s=12):
    destination = Path(destination)
    if destination.exists():
        raise ValueError("A/B output directory must be new")
    start, duration = finite(start_s), finite(duration_s)
    if start < 0 or not 0.4 <= duration <= 60:
        raise ValueError("Use a positive 0.4..60-second excerpt")
    a, sa = read_audio(reference)
    b, sb = read_audio(candidate)
    if sa != sb or a.shape[1] != b.shape[1]:
        raise ValueError("Prepare matching sample rates/channels before this comparison")
    lo, hi = round(start * sa), round((start + duration) * sa)
    if hi > min(len(a), len(b)):
        raise ValueError("Excerpt exceeds a source file")
    a, b = a[lo:hi].copy(), b[lo:hi].copy()
    ma, mb = metrics(a, sa), metrics(b, sb)
    if ma["integrated_lufs"] is None or mb["integrated_lufs"] is None:
        raise ValueError("Cannot loudness-match silence or ungated material")
    match_db = ma["integrated_lufs"] - mb["integrated_lufs"]
    if abs(match_db) > 30:
        raise ValueError("Level difference exceeds 30 dB; verify matching content")
    b *= 10 ** (match_db / 20)
    # Apply common attenuation, never asymmetric peak normalization, if matching exceeds -1 dBFS.
    peak = max(np.max(np.abs(a)), np.max(np.abs(b)))
    common_gain = min(1.0, 10 ** (-1 / 20) / max(peak, 1e-12))
    a, b = a * common_gain, b * common_gain
    flip = secrets.randbelow(2)
    items = [("reference", a), ("candidate", b)]
    if flip:
        items.reverse()
    destination.mkdir(parents=True)
    for label, (_, audio) in zip(("A", "B"), items):
        sf.write(destination / (label + ".wav"), audio, sa, subtype="PCM_24")
    key = {"A": items[0][0], "B": items[1][0], "candidate_match_gain_db": match_db,
           "common_attenuation_db": float(20 * np.log10(common_gain)), "start_s": start,
           "duration_s": duration, "reference_sha256": sha256(reference), "candidate_sha256": sha256(candidate),
           "alignment_verified": False, "scientific_trial": False}
    write_new(destination / "answer-key.json", json_text(key))
    write_new(destination / "listen.txt", "Compare A and B before opening answer-key.json.\n"
              "Keep playback level fixed. Rate diction, groove, harshness, depth and transition continuity separately.\n"
              "These copies are level matched, not time aligned. Check corresponding musical content first.\n")
    return {"directory": str(destination), "files": ["A.wav", "B.wav"], "level_matched": True,
            "identity_key": "answer-key.json (open after listening)", "alignment_verified": False}
