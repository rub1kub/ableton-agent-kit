import base64
import importlib.util
import json
import subprocess
import sys
from pathlib import Path

import pytest

from ableton_agent.common import sha256


def test_cli_report(tone, tmp_path):
    output = tmp_path / "report.json"
    r = subprocess.run([sys.executable, "-m", "ableton_agent.cli", "audio-analyze", str(tone),
                        "--bpm", "120", "--out", str(output)], capture_output=True, text=True)
    assert r.returncode == 0, r.stderr
    assert json.loads(r.stdout)["report"] == str(output)
    assert json.loads(output.read_text())["metrics"]["sample_rate"] == 24000


def test_mcp_path_roots(monkeypatch, tmp_path):
    from ableton_agent.mcp_server import allowed
    monkeypatch.setenv("ABLETON_AGENT_ROOTS", str(tmp_path / "root"))
    assert allowed(tmp_path / "root/report.json").name == "report.json"
    with pytest.raises(ValueError):
        allowed(tmp_path / "root/../outside.json")


def test_release_roundtrip(tone, tmp_path):
    pytest.importorskip("mutagen")
    pytest.importorskip("imageio_ffmpeg")
    from mutagen.mp3 import MP3
    from mutagen.wave import WAVE
    from ableton_agent.release import package, wav_audio_hash
    from ableton_agent.audio import ffmpeg_binary
    cover = tmp_path / "cover.png"
    cover.write_bytes(base64.b64decode("iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/x8AAwMCAO+jRZkAAAAASUVORK5CYII="))
    before = sha256(tone)
    destination = tmp_path / "release"
    package(tone, cover, destination, {"title": "Тест", "artist": "Test Artist", "lyrics": "Synthetic test", "language": "eng"})
    assert sha256(tone) == before
    assert wav_audio_hash(tone) == wav_audio_hash(destination / "track.wav")
    assert MP3(destination / "track.mp3").tags["TIT2"].text == ["Тест"]
    assert WAVE(destination / "track.wav").tags.getall("APIC")[0].data == cover.read_bytes()
    subprocess.run([ffmpeg_binary(), "-v", "error", "-i", str(destination / "track.mp3"),
                    "-f", "null", "-"], check=True, capture_output=True)


def test_staging_keeps_source(tmp_path):
    script = Path(__file__).resolve().parents[1] / "scripts/stage_extension.py"
    spec = importlib.util.spec_from_file_location("stage_extension", script)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    source = tmp_path / "source"
    (source / "handlers").mkdir(parents=True)
    (source / "handlers/__init__.py").write_text("def get_all_write_handlers():\n    return {}\n")
    (source / "server.py").write_text("def _run_on_main_thread():\n    pass\n")
    before = sha256(source / "handlers/__init__.py")
    result = module.stage(source, tmp_path / "staged")
    assert sha256(source / "handlers/__init__.py") == before and not result["installed"]
    assert (tmp_path / "staged/handlers/agent_extension.py").exists()
    with pytest.raises(ValueError):
        module.stage(source, source / "nested")
