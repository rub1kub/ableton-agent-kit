import json
import numpy as np
import soundfile as sf
import pytest

from ableton_agent.listening import ab_pack
from ableton_agent.audio import metrics
from ableton_agent import als


def test_blind_pack_matches_loudness_without_source_changes(tone, tmp_path):
    y, sr = sf.read(tone, always_2d=True)
    candidate = tmp_path / "quiet.wav"
    sf.write(candidate, y * 0.3, sr, subtype="FLOAT")
    destination = tmp_path / "ab"
    original = tone.read_bytes()
    ab_pack(tone, candidate, destination, 0, 1)
    a, _ = sf.read(destination / "A.wav", always_2d=True)
    b, _ = sf.read(destination / "B.wav", always_2d=True)
    assert abs(metrics(a, sr)["integrated_lufs"] - metrics(b, sr)["integrated_lufs"]) < 0.01
    key = json.loads((destination / "answer-key.json").read_text())
    assert {key["A"], key["B"]} == {"candidate", "reference"}
    assert tone.read_bytes() == original
    with pytest.raises(ValueError):
        ab_pack(tone, candidate, destination)


def test_pack_common_headroom(tone, tmp_path):
    y, sr = sf.read(tone, always_2d=True)
    loud = tmp_path / "loud.wav"
    sf.write(loud, y * 14, sr, subtype="FLOAT")
    ab_pack(loud, tone, tmp_path / "ab", 0, 1)
    for label in ("A", "B"):
        x, _ = sf.read(tmp_path / "ab" / (label + ".wav"))
        assert np.max(np.abs(x)) < 0.9


def test_native_group_empty_slot_placeholder_is_valid(make_set):
    import gzip
    import xml.etree.ElementTree as ET
    p, root = make_set()
    group = ET.SubElement(root.find("LiveSet/Tracks"), "GroupTrack", Id="99")
    ET.SubElement(group, "ClipSlotList")
    p.write_bytes(gzip.compress(ET.tostring(root)))
    assert als.audit(p)["static_ok"]
