import gzip
import xml.etree.ElementTree as ET

import pytest

from ableton_agent import als
from ableton_agent.common import sha256


def save(path, root):
    path.write_bytes(gzip.compress(ET.tostring(root)))


def test_valid_fixture(make_set):
    p, _ = make_set()
    report = als.audit(p)
    assert report["static_ok"] and not report["native_load_verified"]
    assert len(report["tracks"][0]["clips"]) == 2


@pytest.mark.parametrize("mode,code", [("slots", "slot_count_mismatch"), ("target", "duplicate_target_ids"),
                                      ("envelope", "unresolved_envelope_targets"), ("next", "next_pointee_id_too_low")])
def test_structure_failures(make_set, mode, code):
    p, root = make_set()
    if mode == "slots":
        ET.SubElement(root.find(".//ClipSlotList"), "ClipSlot", Id="1")
    elif mode == "target":
        ET.SubElement(root.find("LiveSet"), "Pointee", Id="10")
    elif mode == "envelope":
        ET.SubElement(ET.SubElement(root.find("LiveSet"), "EnvelopeTarget"), "PointeeId", Value="999")
    else:
        root.find("LiveSet/NextPointeeId").set("Value", "5")
    save(p, root)
    assert code in [e["code"] for e in als.audit(p)["errors"]]


def test_order_and_missing(make_set):
    p, _ = make_set(unordered=True, missing=True)
    codes = {e["code"] for e in als.audit(p)["errors"]}
    assert {"unordered_arrangement_events", "missing_media"} <= codes


def test_revision_preserves_source_and_sorts(make_set, tmp_path):
    p, _ = make_set()
    digest = sha256(p)
    plan = {"source_sha256": digest, "operations": [
        {"action": "move_audio_clip", "track_id": "5", "expected_track_name": "LEAD", "clip_id": "12", "start_beats": 16},
        {"action": "set_clip_gain_db", "track_id": "5", "expected_track_name": "LEAD", "clip_id": "12", "gain_db": -6},
    ]}
    dest = tmp_path / "revision.als"
    als.revise(p, dest, plan)
    assert sha256(p) == digest
    clips = als.arrangement_clips(als.tracks(als.load(dest))[0])
    assert [float(c.get("Time")) for c in clips] == [8, 16]
    assert float(als.value(clips[1], "CurrentEnd")) == 20
    assert float(als.value(clips[1], "SampleVolume")) == pytest.approx(10 ** (-6 / 20))


def test_revision_rejects_stale_and_identity(make_set, tmp_path):
    p, _ = make_set()
    with pytest.raises(ValueError, match="Source changed"):
        als.revise(p, tmp_path / "new.als", {"source_sha256": "wrong"})
    with pytest.raises(ValueError, match="identity"):
        als.revise(p, tmp_path / "new.als", {"source_sha256": sha256(p), "operations": [
            {"action": "set_track_active", "track_id": 5, "expected_track_name": "OTHER", "active": False}]})
    assert not (tmp_path / "new.als").exists()


def test_no_overwrite(make_set):
    p, _ = make_set()
    with pytest.raises(ValueError, match="distinct"):
        als.revise(p, p, {"source_sha256": sha256(p)})


def test_collection(make_set, tmp_path, tone):
    p, _ = make_set()
    folder = tmp_path.parent / (tmp_path.name + "-portable")
    result = als.collect(p, folder)
    assert result["static_ok"] and result["audio_files"] == 1
    assert result["native_collect_all_performed"] is False
    media = list((folder / "Samples/Collected").iterdir())
    assert sha256(media[0]) == sha256(tone)
    with pytest.raises(ValueError, match="outside"):
        als.collect(p, tmp_path / "nested-project")


def test_piecewise_warp():
    c = ET.Element("AudioClip")
    ET.SubElement(c, "IsWarped", Value="true")
    markers = ET.SubElement(c, "WarpMarkers")
    for beat, sec in ((0, 0), (4, 2), (8, 5)):
        ET.SubElement(markers, "WarpMarker", BeatTime=str(beat), SecTime=str(sec))
    assert als.beat_to_source_seconds(c, 6) == 3.5
    with pytest.raises(ValueError):
        als.beat_to_source_seconds(c, 9)
    c.find("IsWarped").set("Value", "false")
    with pytest.raises(ValueError, match="Warp is off"):
        als.beat_to_source_seconds(c, 1)


def test_xml_entities_rejected(tmp_path):
    p = tmp_path / "evil.als"
    p.write_bytes(gzip.compress(b'<!DOCTYPE x [<!ENTITY e "abc">]><Ableton><LiveSet>&e;</LiveSet></Ableton>'))
    with pytest.raises(Exception):
        als.load(p)
