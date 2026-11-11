import gzip
import xml.etree.ElementTree as ET
from pathlib import Path

import numpy as np
import pytest
import soundfile as sf


@pytest.fixture
def tone(tmp_path):
    sr = 24000
    x = 0.1 * np.sin(2 * np.pi * 440 * np.arange(sr * 2) / sr)
    p = tmp_path / "tone.wav"
    sf.write(p, np.column_stack((x, x)), sr, subtype="PCM_24")
    return p


@pytest.fixture
def make_set(tmp_path, tone):
    def build(name="test.als", unordered=False, missing=False):
        root = ET.Element("Ableton", Creator="Synthetic test fixture", MinorVersion="12.0_0")
        live = ET.SubElement(root, "LiveSet")
        ET.SubElement(live, "NextPointeeId", Value="11")
        ET.SubElement(ET.SubElement(live, "Scenes"), "Scene", Id="0")
        track = ET.SubElement(ET.SubElement(live, "Tracks"), "AudioTrack", Id="5")
        ET.SubElement(ET.SubElement(track, "Name"), "EffectiveName", Value="LEAD")
        dc = ET.SubElement(track, "DeviceChain")
        mix = ET.SubElement(dc, "Mixer")
        ET.SubElement(ET.SubElement(mix, "Speaker"), "Manual", Value="true")
        ET.SubElement(mix, "AutomationTarget", Id="10")
        ET.SubElement(ET.SubElement(dc, "ClipSlotList"), "ClipSlot", Id="0")
        seq = ET.SubElement(dc, "MainSequencer")
        events = ET.SubElement(ET.SubElement(ET.SubElement(seq, "Sample"), "ArrangerAutomation"), "Events")
        for i, time in enumerate((8, 0) if unordered else (0, 8)):
            c = ET.SubElement(events, "AudioClip", Id=str(12 + i), Time=str(time))
            for tag, val in (("Name", "phrase"), ("CurrentStart", time), ("CurrentEnd", time + 4),
                             ("SampleVolume", 1), ("IsWarped", "false")):
                ET.SubElement(c, tag, Value=str(val))
            ref = ET.SubElement(ET.SubElement(c, "SampleRef"), "FileRef")
            ET.SubElement(ref, "Path", Value=str(tmp_path / "missing.wav" if missing else tone))
            ET.SubElement(ref, "RelativePath", Value="missing.wav" if missing else "tone.wav")
            ET.SubElement(ref, "RelativePathType", Value="3")
        path = tmp_path / name
        path.write_bytes(gzip.compress(ET.tostring(root)))
        return path, root
    return build


def extension_module():
    import importlib.util
    path = Path(__file__).resolve().parents[1] / "extensions/livemcp/agent_extension.py"
    spec = importlib.util.spec_from_file_location("agent_extension", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
