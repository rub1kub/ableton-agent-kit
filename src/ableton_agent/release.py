"""Release packaging with explicit credits and bit-identical WAV sample chunks."""
import hashlib
import shutil
import struct
from pathlib import Path

from .audio import encode_mp3
from .common import sha256, write_new, json_text


def wav_audio_hash(path):
    chunks = []
    with Path(path).open("rb") as f:
        head = f.read(12)
        if head[:4] != b"RIFF" or head[8:] != b"WAVE":
            raise ValueError("Only RIFF WAV is supported; RF64 needs a separate workflow")
        size = Path(path).stat().st_size
        while f.tell() + 8 <= size:
            name, length = struct.unpack("<4sI", f.read(8))
            if f.tell() + length > size:
                raise ValueError("Truncated WAV chunk")
            if name in (b"fmt ", b"data"):
                digest, remaining = hashlib.sha256(), length
                while remaining:
                    block = f.read(min(1024 * 1024, remaining))
                    digest.update(block)
                    remaining -= len(block)
                chunks.append((name.decode(), length, digest.hexdigest()))
            else:
                f.seek(length, 1)
            if length % 2:
                f.seek(1, 1)
    if not any(c[0] == "data" for c in chunks):
        raise ValueError("WAV has no sample data")
    return chunks


def package(source, cover, destination, metadata):
    from mutagen.wave import WAVE
    from mutagen.mp3 import MP3
    from mutagen.id3 import TIT2, TPE1, TPE2, TALB, TDRC, TCON, TBPM, TKEY, TLAN, USLT, APIC, TRCK
    source, cover, destination = Path(source), Path(cover), Path(destination)
    if destination.exists():
        raise ValueError("Release folder must be new")
    if not metadata.get("title") or not metadata.get("artist"):
        raise ValueError("Title and artist are required")
    if cover.stat().st_size > 10 * 1024 * 1024:
        raise ValueError("Use a cover no larger than 10 MiB")
    art = cover.read_bytes()
    if art.startswith(b"\x89PNG\r\n\x1a\n"):
        mime, suffix = "image/png", ".png"
    elif art.startswith(b"\xff\xd8\xff"):
        mime, suffix = "image/jpeg", ".jpg"
    else:
        raise ValueError("Cover must be PNG or JPEG")
    original_hash, samples = sha256(source), wav_audio_hash(source)
    destination.mkdir(parents=True)
    wav, mp3 = destination / "track.wav", destination / "track.mp3"
    shutil.copy2(source, wav)
    encode_mp3(source, mp3)
    tags = {"title": TIT2, "artist": TPE1, "album_artist": TPE2, "album": TALB,
            "year": TDRC, "genre": TCON, "bpm": TBPM, "key": TKEY, "language": TLAN, "track": TRCK}
    for audio in (WAVE(wav), MP3(mp3)):
        if audio.tags is None:
            audio.add_tags()
        for field, cls in tags.items():
            if field in metadata:
                audio.tags.delall(cls.__name__)
                audio.tags.add(cls(encoding=1, text=[str(metadata[field])]))
        audio.tags.delall("APIC")
        audio.tags.add(APIC(encoding=1, mime=mime, type=3, desc="Front cover", data=art))
        if metadata.get("lyrics"):
            audio.tags.delall("USLT")
            audio.tags.add(USLT(encoding=1, lang=metadata.get("language", "und"), desc="", text=metadata["lyrics"]))
        audio.save(v2_version=3)
    if sha256(source) != original_hash or wav_audio_hash(wav) != samples:
        raise RuntimeError("Source or WAV audio payload changed unexpectedly")
    for audio in (WAVE(wav), MP3(mp3)):
        if audio.tags["TIT2"].text[0] != metadata["title"] or audio.tags.getall("APIC")[0].data != art:
            raise RuntimeError("Metadata roundtrip mismatch")
    write_new(destination / ("cover" + suffix), art)
    if metadata.get("lyrics"):
        write_new(destination / "lyrics.txt", metadata["lyrics"])
    report = {"metadata": metadata, "source_unchanged": True, "wav_samples_bit_identical": True,
              "mp3_bitrate_kbps": 320, "normalization_applied": False,
              "files": {p.name: sha256(p) for p in destination.iterdir() if p.is_file()}}
    write_new(destination / "release.json", json_text(report))
    return {"directory": str(destination), **{k: v for k, v in report.items() if k != "metadata"}}
