"""Audio evidence, not an automatic taste score. All times are seconds."""
import math
import subprocess
from pathlib import Path

import numpy as np
import soundfile as sf
from scipy import signal
import pyloudnorm as pyln

from .common import clean, finite, sha256


def db(amplitude):
    return 20 * math.log10(max(float(amplitude), 1e-12))


def ffmpeg_binary():
    import shutil
    found = shutil.which("ffmpeg")
    if found:
        return found
    try:
        import imageio_ffmpeg
        return imageio_ffmpeg.get_ffmpeg_exe()
    except ImportError as exc:
        raise RuntimeError("Install ffmpeg or ableton-agent-kit[mp3]") from exc


def read_audio(path, max_seconds=1800):
    """Decode at original sample rate. Never normalize audio on ingestion."""
    try:
        info = sf.info(path)
        if info.duration > max_seconds or info.channels > 2 or info.frames * info.channels > 32_000_000:
            raise ValueError("Use a mono/stereo excerpt within 30 minutes and 32 million channel samples")
        y, sr = sf.read(path, dtype="float64", always_2d=True)
    except sf.LibsndfileError as exc:
        raise ValueError("Cannot decode this file; export PCM WAV/FLAC first") from exc
    if not len(y) or not np.isfinite(y).all():
        raise ValueError("Empty or non-finite audio")
    return y, int(sr)


def metrics(y, sr):
    y = np.asarray(y, dtype=float)
    if y.ndim == 1:
        y = y[:, None]
    if y.ndim != 2 or y.shape[1] not in (1, 2) or not len(y) or sr <= 0 or not np.isfinite(y).all():
        raise ValueError("Need finite, nonempty mono/stereo samples and positive rate")
    rms = float(np.sqrt(np.mean(y * y)))
    peak = float(np.max(np.abs(y)))
    mono = y.mean(axis=1)
    # This oversampling estimate is deliberately NOT called a certified true-peak measurement.
    oversampled = oversampled_peak(y)
    correlation = None
    if y.shape[1] == 2 and np.all(np.std(y, axis=0) > 1e-10):
        correlation = float(np.corrcoef(y.T)[0, 1])
    loudness = None
    if len(y) / sr >= 0.4 and peak > 1e-10:
        loudness = float(pyln.Meter(sr).integrated_loudness(y))
    result = {"duration_s": len(y) / sr, "sample_rate": sr, "channels": y.shape[1],
              "integrated_lufs": loudness, "sample_peak_dbfs": db(peak),
              "oversampled_peak_dbfs_estimate": db(oversampled), "oversampling_factor": 4,
              "rms_dbfs": db(rms), "crest_db": db(peak / rms) if rms else None,
              "mono_rms_delta_db": db(np.sqrt(np.mean(mono * mono)) / rms) if rms else None,
              "stereo_correlation": correlation, "samples_at_or_above_full_scale": int(np.sum(np.abs(y) >= 1)),
              "silent": peak < 1e-8}
    return clean(result)


def oversampled_peak(y, chunk_size=262144):
    """Bound peak-analysis memory with overlap around polyphase filter boundaries."""
    peak = 0.0
    for start in range(0, len(y), chunk_size):
        end = min(len(y), start + chunk_size)
        lo, hi = max(0, start - 64), min(len(y), end + 64)
        up = signal.resample_poly(y[lo:hi], 4, 1, axis=0)
        valid = up[(start - lo) * 4:(end - lo) * 4]
        peak = max(peak, float(np.max(np.abs(valid))))
    return peak


def envelope(y, sr, window_s=0.02):
    """Stereo energy preserves anti-phase events that a mono sum could erase."""
    n = max(1, round(sr * window_s))
    chunks = [y[i:i + n] for i in range(0, len(y), n)]
    rms = np.array([np.sqrt(np.mean(c * c)) for c in chunks])
    return np.arange(len(rms)) * n / sr, rms


def intervals(mask, times, end_s, minimum_s):
    edges = np.diff(np.r_[False, mask, False].astype(int))
    result = []
    for start, end in zip(np.flatnonzero(edges == 1), np.flatnonzero(edges == -1)):
        a, b = float(times[start]), float(times[end]) if end < len(times) else end_s
        if b - a >= minimum_s:
            result.append({"start_s": a, "end_s": b, "duration_s": b - a})
    return result


def analyze(path, bpm=None, sections=None):
    y, sr = read_audio(path)
    times, rms = envelope(y, sr)
    reference = float(np.percentile(rms, 80))
    threshold = max(reference * 10 ** (-24 / 20), 10 ** (-65 / 20))
    gaps = intervals(rms < threshold, times, len(y) / sr, 0.06)
    # Energy onsets are candidates; not an asserted beat tracker or transient slicer.
    onset = np.maximum(0, np.diff(np.log(np.maximum(rms, 1e-9)), prepend=0))
    peaks, _ = signal.find_peaks(onset, prominence=0.35, distance=3)
    transients = times[peaks]
    report = {"schema_version": 1, "source_sha256": sha256(path), "metrics": metrics(y, sr),
              "bands": spectral_bands(y, sr),
              "gap_candidates": gaps, "gap_threshold_dbfs": db(threshold),
              "transient_candidates_s": transients.tolist(),
              "evidence": "decoded file; no claim of subjective listening", "sections": []}
    if bpm is not None:
        bpm = finite(bpm, "bpm")
        if not 20 <= bpm <= 400:
            raise ValueError("BPM outside supported 20..400 range")
        pulse = 60 / bpm
        report["grid"] = {"bpm_assumed": bpm, "quarter_s": pulse, "eighth_s": pulse / 2,
                          "dotted_eighth_s": pulse * 0.75, "sixteenth_s": pulse / 4,
                          "bars_4_4": len(y) / sr / (4 * pulse),
                          "onset_offset_to_nearest_sixteenth_ms":
                          (1000 * ((transients + pulse / 8) % (pulse / 4) - pulse / 8)).tolist(),
                          "warning": "Offsets do not prove tempo: syncopation and soft attacks need musical review."}
    for section in sections or []:
        a, b = finite(section["start_s"]), finite(section["end_s"])
        if not 0 <= a < b <= len(y) / sr + 1e-6:
            raise ValueError(f"Section outside file: {section.get('name')}")
        report["sections"].append({"name": section["name"], "start_s": a, "end_s": b,
                                   "metrics": metrics(y[round(a * sr):round(b * sr)], sr)})
    return report


def spectral_bands(y, sr):
    """Welch band power uses independent channels; bands are diagnostics, not EQ targets."""
    freqs, psd = signal.welch(y, sr, axis=0, nperseg=min(4096, len(y)))
    power = psd.mean(axis=1)
    df = freqs[1] - freqs[0] if len(freqs) > 1 else sr
    total = max(float(np.sum(power) * df), 1e-24)
    rows = []
    for low, high in ((20, 80), (80, 250), (250, 500), (500, 2000), (2000, 5000), (5000, 10000), (10000, 20000)):
        effective = min(high, sr / 2)
        if effective <= low:
            continue
        p = float(np.sum(power[(freqs >= low) & (freqs < effective)]) * df)
        rows.append({"low_hz": low, "high_hz": effective, "power_fraction": p / total, "rms_dbfs": db(math.sqrt(p))})
    return rows


def masking_proxy(vocal_path, accompaniment_path, aligned=False):
    """Time/band overlap screen, NOT a psychoacoustic audibility or intelligibility model."""
    if not aligned:
        raise ValueError("Provide aligned exports and acknowledge aligned=True / --aligned")
    vocal, sr = read_audio(vocal_path)
    other, other_sr = read_audio(accompaniment_path)
    if sr != other_sr or len(vocal) != len(other):
        raise ValueError("Aligned stems must share sample rate and exact sample count")
    times, vrms = envelope(vocal, sr, 0.1)
    active = vrms > max(10 ** (-60 / 20), float(np.max(vrms)) * 10 ** (-30 / 20))
    rows = []
    for low, high in ((100, 250), (250, 500), (500, 1000), (1000, 2000), (2000, 4000), (4000, 8000)):
        high = min(high, sr * 0.45)
        if high <= low:
            continue
        sos = signal.butter(3, (low, high), fs=sr, btype="bandpass", output="sos")
        _, v = envelope(signal.sosfilt(sos, vocal, axis=0), sr, 0.1)
        _, b = envelope(signal.sosfilt(sos, other, axis=0), sr, 0.1)
        valid = active & (v > 10 ** (-60 / 20))
        difference = 20 * np.log10(np.maximum(b, 1e-12) / np.maximum(v, 1e-12))
        candidates = valid & (difference >= -3)
        rows.append({"band_hz": [low, high], "active_frames": int(valid.sum()),
                     "competition_fraction": float(candidates.sum() / valid.sum()) if valid.any() else None,
                     "median_other_minus_vocal_db": float(np.median(difference[valid])) if valid.any() else None,
                     "candidate_intervals": intervals(candidates, times, len(vocal) / sr, 0.2)[:40]})
    return {"bands": rows, "alignment": "asserted by caller, not independently proven",
            "model": "band-energy overlap proxy", "diagnosis": False,
            "warning": "No masking threshold, speech recognition or perceptual guarantee. Audition candidates; do not auto-EQ."}


def compare(a, b):
    """Report raw levels and gain needed for level-matched listening; no file changes."""
    ya, sa = read_audio(a)
    yb, sb = read_audio(b)
    ma, mb = metrics(ya, sa), metrics(yb, sb)
    gain = None
    if ma["integrated_lufs"] is not None and mb["integrated_lufs"] is not None:
        gain = ma["integrated_lufs"] - mb["integrated_lufs"]
    return {"reference": ma, "candidate": mb, "candidate_match_gain_db": gain,
            "aligned": False, "audio_changed": False,
            "next": "Align corresponding musical sections and audition at the stated gain; metrics do not rank taste."}


def align(reference, candidate, sr, max_lag_s=5):
    """Estimate global offset. Positive lag means candidate is delayed."""
    a = np.asarray(reference).mean(axis=1) if np.asarray(reference).ndim == 2 else np.asarray(reference)
    b = np.asarray(candidate).mean(axis=1) if np.asarray(candidate).ndim == 2 else np.asarray(candidate)
    if not len(a) or not len(b) or not np.isfinite(a).all() or not np.isfinite(b).all():
        raise ValueError("Empty or invalid alignment signal")
    step = max(1, int(sr // 4000))
    a = signal.resample_poly(a, 1, step)
    b = signal.resample_poly(b, 1, step)
    a, b = a - a.mean(), b - b.mean()
    if np.linalg.norm(a) < 1e-8 or np.linalg.norm(b) < 1e-8:
        raise ValueError("Cannot align silence")
    corr = signal.correlate(b, a, method="fft")
    lags = signal.correlation_lags(len(b), len(a))
    valid = np.abs(lags) <= max_lag_s * sr / step
    index = np.flatnonzero(valid)[np.argmax(corr[valid])]
    return {"candidate_delay_s": float(lags[index] * step / sr),
            "normalized_correlation": float(corr[index] / (np.linalg.norm(a) * np.linalg.norm(b))),
            "resolution_s": step / sr,
            "warning": "Repeated music may give an ambiguous offset; verify a second independent region."}


def figure(path, output):
    """Standalone waveform, spectrogram and stereo-balance overview."""
    if Path(output).exists():
        raise ValueError("Plot output already exists")
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    y, sr = read_audio(path)
    times, energy = envelope(y, sr)
    fig, ax = plt.subplots(3, 1, figsize=(15, 9), constrained_layout=True)
    stride = max(1, len(y) // 100000)
    ax[0].plot(np.arange(0, len(y), stride) / sr, y[::stride], lw=0.35)
    ax[0].set(ylabel="Amplitude", title="Decoded audio — waveform, spectrum, stereo energy")
    # Power spectrum uses channels independently, not cancellation-prone mono summing.
    specs = [signal.spectrogram(y[:, ch], sr, nperseg=2048, noverlap=1024) for ch in range(y.shape[1])]
    f, t, _ = specs[0]
    power = np.mean([s[2] for s in specs], axis=0)
    ax[1].pcolormesh(t, f, 10 * np.log10(np.maximum(power, 1e-12)), shading="auto", vmin=-100, vmax=-25)
    ax[1].set(yscale="log", ylim=(40, min(18000, sr / 2)), ylabel="Hz")
    if y.shape[1] == 2:
        _, left = envelope(y[:, :1], sr)
        _, right = envelope(y[:, 1:], sr)
        balance = (right - left) / np.maximum(right + left, 1e-10)
        ax[2].plot(times, balance, lw=0.7)
        ax[2].set(ylim=(-1, 1), ylabel="L −1 / R +1")
    else:
        ax[2].plot(times, 20 * np.log10(np.maximum(energy, 1e-12)))
        ax[2].set(ylabel="RMS dBFS (mono)")
    ax[2].set(xlabel="Time (s)")
    fig.savefig(output, dpi=140)
    plt.close(fig)
    return {"path": str(output)}


def encode_mp3(source, destination):
    destination = Path(destination)
    if destination.exists():
        raise ValueError("MP3 output already exists")
    subprocess.run([ffmpeg_binary(), "-v", "error", "-n", "-i", str(source), "-map", "0:a:0",
                    "-map_metadata", "-1", "-c:a", "libmp3lame", "-b:a", "320k", str(destination)], check=True)
    return {"path": str(destination), "bitrate_kbps": 320, "normalization": False}
