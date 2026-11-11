import numpy as np
import pytest
import soundfile as sf

from ableton_agent.audio import metrics, analyze, align, compare
from ableton_agent.music import echo_plan
from ableton_agent.common import json_text


def test_tone_metrics(tone):
    y, sr = sf.read(tone, always_2d=True)
    report = metrics(y, sr)
    assert report["sample_peak_dbfs"] == pytest.approx(-20, abs=0.01)
    assert report["rms_dbfs"] == pytest.approx(-23.0103, abs=0.01)
    assert report["stereo_correlation"] == pytest.approx(1)
    assert report["mono_rms_delta_db"] == pytest.approx(0)


def test_antiphase_and_silence(tone):
    y, sr = sf.read(tone, always_2d=True)
    y[:, 1] *= -1
    report = metrics(y, sr)
    assert report["stereo_correlation"] == pytest.approx(-1)
    assert report["mono_rms_delta_db"] <= -200
    silent = metrics(np.zeros((sr, 2)), sr)
    assert silent["integrated_lufs"] is None and silent["silent"]
    assert "NaN" not in json_text(silent) and "Infinity" not in json_text(silent)


@pytest.mark.parametrize("samples", [np.array([]), np.array([np.nan]), np.ones((30, 3))])
def test_invalid_audio(samples):
    with pytest.raises(ValueError):
        metrics(samples, 44100)


def test_gaps_and_sections(tmp_path):
    sr = 24000
    rng = np.random.default_rng(42)
    y = rng.normal(0, 0.04, (sr * 3, 2))
    y[sr:sr + sr // 4] = 0
    p = tmp_path / "gap.wav"
    sf.write(p, y, sr)
    r = analyze(p, 120, [{"name": "part", "start_s": 0, "end_s": 1}])
    assert any(abs(g["start_s"] - 1) < 0.04 and g["duration_s"] > 0.2 for g in r["gap_candidates"])
    assert r["grid"]["sixteenth_s"] == 0.125
    assert r["sections"][0]["metrics"]["duration_s"] == 1


def test_alignment():
    rng = np.random.default_rng(12)
    a = rng.normal(size=8000)
    b = np.r_[np.zeros(800), a]
    r = align(a, b, 8000, 1)
    assert r["candidate_delay_s"] == pytest.approx(0.1, abs=0.001)
    assert r["normalized_correlation"] > 0.98


def test_equal_loudness_comparison(tone, tmp_path):
    y, sr = sf.read(tone, always_2d=True)
    quieter = tmp_path / "quieter.wav"
    sf.write(quieter, y * 0.5, sr, subtype="FLOAT")
    r = compare(tone, quieter)
    assert r["candidate_match_gain_db"] == pytest.approx(6.0206, abs=0.02)


def test_echo_fit_and_intent():
    short = echo_plan(10, 0.3, 10.5, 120)
    assert len(short["answers"]) == 1
    assert short["answers"][0]["end_s"] < 10.5
    overlap = echo_plan(10, 0.5, 10.1, 120, allow_overlap=True)
    assert len(overlap["answers"]) == 2 and overlap["answers"][0]["overlaps_next_phrase"]
    tight = echo_plan(10, 0.5, 10.1, 120)
    assert not tight["answers"] and tight["fallback"]


def test_invalid_echo():
    with pytest.raises(ValueError):
        echo_plan(1, -1, 2, 120)


def test_chunked_oversampling_matches_whole():
    from scipy.signal import resample_poly
    from ableton_agent.audio import oversampled_peak
    x = np.random.default_rng(4).normal(0, 0.1, (20000, 2))
    x[4095] = 0.9
    expected = np.max(np.abs(resample_poly(x, 4, 1, axis=0)))
    assert oversampled_peak(x, chunk_size=4096) == pytest.approx(expected, abs=1e-12)
