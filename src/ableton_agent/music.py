"""Optional pitch/ASR helpers and explicit, revisable musical planning."""
import math
import numpy as np
from .audio import read_audio
from .common import finite

NOTE_NAMES = ("C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B")
SCALES = {"minor": (0, 2, 3, 5, 7, 8, 10), "major": (0, 2, 4, 5, 7, 9, 11)}


def pitch_report(path, start_s=0, end_s=None, fmin=65, fmax=1000):
    import librosa
    y, sr = read_audio(path)
    end_s = len(y) / sr if end_s is None else finite(end_s)
    if not 0 <= start_s < end_s <= len(y) / sr or end_s - start_s > 60:
        raise ValueError("Analyze a valid monophonic excerpt up to 60 seconds")
    mono = y[round(start_s * sr):round(end_s * sr)].mean(axis=1)
    mono = librosa.resample(mono, orig_sr=sr, target_sr=16000)
    f0, voiced, probability = librosa.pyin(mono, sr=16000, fmin=fmin, fmax=fmax,
                                         frame_length=2048, hop_length=256)
    rows = []
    for i, freq in enumerate(f0):
        if voiced[i] and probability[i] >= 0.8 and np.isfinite(freq):
            midi = 69 + 12 * math.log2(float(freq) / 440)
            rows.append({"time_s": start_s + i * 256 / 16000, "hz": float(freq),
                         "midi": midi, "confidence": float(probability[i])})
    return {"algorithm": "librosa.pyin", "confidence_threshold": 0.8, "voiced_frames": rows,
            "warning": "Monophonic evidence only; rap consonants and pitch-shifted/polyphonic layers can invalidate F0."}


def key_candidates(path, start_s=0, end_s=None):
    import librosa
    y, sr = read_audio(path)
    end_s = len(y) / sr if end_s is None else finite(end_s)
    if not 0 <= start_s < end_s <= len(y) / sr:
        raise ValueError("Invalid analysis interval")
    mono = y[round(start_s * sr):round(end_s * sr)].mean(axis=1)
    if np.max(np.abs(mono)) < 1e-7:
        return {"candidates": [], "warning": "Silence or phase cancellation: cannot infer a key"}
    mono = librosa.resample(mono, orig_sr=sr, target_sr=22050)
    harmonic = librosa.effects.harmonic(mono)
    chroma = librosa.feature.chroma_stft(y=harmonic, sr=22050).mean(axis=1)
    profiles = {"major": np.array([6.35, 2.23, 3.48, 2.33, 4.38, 4.09, 2.52, 5.19, 2.39, 3.66, 2.29, 2.88]),
                "minor": np.array([6.33, 2.68, 3.52, 5.38, 2.60, 3.53, 2.54, 4.75, 3.98, 2.69, 3.34, 3.17])}
    rows = []
    if np.std(chroma) < 1e-8:
        return {"candidates": [], "warning": "Insufficient tonal contrast"}
    for mode, profile in profiles.items():
        for root in range(12):
            rows.append({"key": NOTE_NAMES[root] + " " + mode,
                         "profile_correlation": float(np.corrcoef(chroma, np.roll(profile, root))[0, 1])})
    rows.sort(key=lambda r: r["profile_correlation"], reverse=True)
    return {"candidates": rows[:5], "chroma": chroma.tolist(),
            "warning": "Heuristic ranking, not calibrated confidence or a chord map. Check bass, melody, sections and ears."}


def echo_plan(word_end_s, word_duration_s, next_phrase_s, bpm, repeats=2, allow_overlap=False):
    """Plan whole-word answers; never time-compress or cut a word implicitly."""
    end, duration, next_phrase, tempo = map(finite, (word_end_s, word_duration_s, next_phrase_s, bpm))
    if end < 0 or duration <= 0 or next_phrase < end or not 20 <= tempo <= 400 or not 0 <= repeats <= 8:
        raise ValueError("Invalid echo plan inputs")
    tick = 60 / tempo / 4
    spacing = max(tick, math.ceil(duration / tick) * tick)
    answers = []
    for i in range(repeats):
        a = end + tick + i * spacing
        b = a + duration
        if b > next_phrase - 0.035 and not allow_overlap:
            break
        answers.append({"start_s": a, "end_s": b, "gain_db_relative": -8 - i * 3,
                        "pan": -0.65 if i % 2 == 0 else 0.65,
                        "overlaps_next_phrase": b > next_phrase,
                        "pitch_policy": "reuse an approved whole-word effect or retune the entire word"})
    return {"answers": answers, "fallback": None if answers else "simultaneous quiet side accent",
            "allow_overlap": allow_overlap, "advisory_only": True}


def transcribe(path, model_path, language=None):
    """Local model only: no download/upload or assumption that ASR is the lyric authority."""
    from faster_whisper import WhisperModel
    from pathlib import Path
    if not Path(model_path).is_dir():
        raise ValueError("Supply an existing local faster-whisper model directory")
    model = WhisperModel(str(model_path), device="cpu", compute_type="int8", local_files_only=True)
    segments, info = model.transcribe(str(path), language=language, word_timestamps=True)
    words = [{"start_s": w.start, "end_s": w.end, "text": w.word, "probability": w.probability}
             for segment in segments for w in (segment.words or [])]
    return {"language": info.language, "words": words,
            "warning": "Tentative timing. Supplied lyrics override ASR; inspect low confidence and tuned vocals."}
