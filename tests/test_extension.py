import time
from types import SimpleNamespace as NS

import pytest
from conftest import extension_module


class Param:
    def __init__(self, name="Gain", value=0.5, fail=None):
        self.name, self._value, self.fail = name, value, fail
        self.min, self.max, self.is_enabled, self.is_quantized, self.automation_state = 0, 1, True, False, 0

    @property
    def value(self):
        return self._value

    @value.setter
    def value(self, value):
        if self.fail == value:
            raise RuntimeError("simulated setter failure")
        self._value = value

    def __str__(self):
        return str(self.value)


class Track:
    def __init__(self, name="LEAD", group=False):
        self.name, self.is_foldable, self.can_be_armed = name, group, not group
        self.mute, self.solo = False, False
        self.mixer_device = NS(volume=Param(), panning=Param())
        self.devices = [NS(name="Utility", class_name="StereoGain", is_active=True,
                           parameters=[Param(), Param("Width")])]
        self.arrangement_clips, self.take_lanes = [], []

    @property
    def arm(self):
        if not self.can_be_armed:
            raise RuntimeError("Non-armable track")
        return False


@pytest.fixture
def env():
    ext = extension_module()
    song = NS(tracks=[Track(), Track("VOCALS", True)], return_tracks=[Track("Reverb", True)],
              master_track=Track("Main", True), record_mode=False, is_playing=False,
              tempo=120, signature_numerator=4, signature_denominator=4, current_song_time=0)
    song.undo = []
    song.begin_undo_step = lambda: song.undo.append("begin")
    song.end_undo_step = lambda: song.undo.append("end")
    cs = NS(song=lambda: song, application=lambda: NS())
    return ext, song, cs


def edit(pi=0, value=0.7):
    return {"scope": "track", "index": 0, "expected_track_name": "LEAD", "device_index": 0,
            "expected_device_name": "Utility", "parameter_index": pi,
            "expected_parameter_name": "Gain" if pi == 0 else "Width", "expected_value": 0.5, "value": value}


def plan(edits):
    return {"deadline_unix_s": time.time() + 20, "edits": edits}


def test_groups_returns_master_and_pages(env):
    ext, _, cs = env
    first = ext.snapshot(cs, {"limit": 2})
    assert first["total"] == 4 and first["next_offset"] == 2
    assert first["tracks"][1]["arm"] is None
    last = ext.snapshot(cs, {"offset": 2, "limit": 2})
    assert last["next_offset"] is None and len(last["tracks"]) == 2


def test_batch_and_undo(env):
    ext, song, cs = env
    result = ext.set_parameters(cs, plan([edit()]))
    assert result["applied"] == 1 and not result["saved"]
    assert song.tracks[0].devices[0].parameters[0].value == 0.7
    assert song.undo == ["begin", "end"]


@pytest.mark.parametrize("field,new", [("expected_track_name", "wrong"), ("expected_device_name", "wrong"),
                                      ("expected_parameter_name", "wrong"), ("expected_value", 0.1),
                                      ("value", 2), ("value", float("nan"))])
def test_preconditions_no_partial_write(env, field, new):
    ext, song, cs = env
    second = edit(1)
    second[field] = new
    with pytest.raises(ValueError):
        ext.set_parameters(cs, plan([edit(), second]))
    assert song.tracks[0].devices[0].parameters[0].value == 0.5
    assert not song.undo


def test_expired_automated_recording_and_duplicates(env):
    ext, song, cs = env
    with pytest.raises(ValueError):
        ext.set_parameters(cs, {"deadline_unix_s": time.time() - 1, "edits": [edit()]})
    with pytest.raises(ValueError, match="Duplicate"):
        ext.set_parameters(cs, plan([edit(), edit()]))
    song.tracks[0].devices[0].parameters[0].automation_state = 1
    with pytest.raises(ValueError, match="Automated"):
        ext.set_parameters(cs, plan([edit()]))
    song.record_mode = True
    with pytest.raises(ValueError, match="recording"):
        ext.set_parameters(cs, plan([edit()]))


def test_rollback(env):
    ext, song, cs = env
    song.tracks[0].devices[0].parameters[1].fail = 0.7
    with pytest.raises(RuntimeError, match=r"rollback failures: \[\]"):
        ext.set_parameters(cs, plan([edit(), edit(1)]))
    assert [p.value for p in song.tracks[0].devices[0].parameters] == [0.5, 0.5]
    assert song.undo == ["begin", "end"]
