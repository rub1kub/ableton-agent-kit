import numpy as np
import soundfile as sf
import pytest

from ableton_agent.cache import cached_analysis
from ableton_agent.backends import plan_backend
from ableton_agent.audio import masking_proxy


def test_cache_invalidates_content_options(tone, tmp_path):
    cache = tmp_path / "cache"
    _, first = cached_analysis(tone, cache, {"bpm": 120})
    _, second = cached_analysis(tone, cache, {"bpm": 120})
    _, third = cached_analysis(tone, cache, {"bpm": 130})
    assert not first["hit"] and second["hit"] and not third["hit"]
    y, sr = sf.read(tone)
    sf.write(tone, y * 0.5, sr)
    _, fourth = cached_analysis(tone, cache, {"bpm": 120})
    assert not fourth["hit"] and first["key"] != fourth["key"]


def test_backend_only_observed_tools():
    report = plan_backend(["get_session_snapshot", "describe_capabilities", "record_section"], "12.2.2")
    assert report["families_inferred_from_names"] == ["wstierhout-style typed Ableton MCP"]
    assert report["candidate_tools_by_task"]["batch_edit"] == []
    assert report["candidate_tools_by_task"]["rendered_audio"] == ["record_section"]
    assert not report["backend_native_verified"]


def test_masking_proxy_requires_alignment(tone):
    with pytest.raises(ValueError, match="aligned"):
        masking_proxy(tone, tone)


def test_masking_proxy_detects_overlap(tone, tmp_path):
    y, sr = sf.read(tone)
    other = tmp_path / "other.wav"
    sf.write(other, y * 2, sr)
    result = masking_proxy(tone, other, True)
    band = next(b for b in result["bands"] if b["band_hz"] == [250, 500])
    assert band["competition_fraction"] > 0.9
    assert band["median_other_minus_vocal_db"] == pytest.approx(6.02, abs=0.1)
    assert not result["diagnosis"]
    sf.write(other, np.zeros_like(y[:-1]), sr)
    with pytest.raises(ValueError, match="sample count"):
        masking_proxy(tone, other, True)
