import pytest
from ableton_agent.plugins import fingerprint, probe, module_path


def test_plugin_fingerprint_tracks_bundle_changes(tmp_path):
    bundle = tmp_path/'Example.vst3'
    binary = bundle/'Contents/x86_64-win/Example.vst3'
    binary.parent.mkdir(parents=True)
    binary.write_bytes(b'fixture v1')
    first = fingerprint(bundle)
    assert first['files'] == 1
    assert module_path(bundle, 'win32') == binary
    assert module_path(bundle, 'darwin') == bundle
    binary.write_bytes(b'fixture v2')
    assert fingerprint(bundle)['sha256'] != first['sha256']
    with pytest.raises(ValueError):
        fingerprint(tmp_path/'missing.vst3')
    with pytest.raises(ValueError):
        fingerprint(tmp_path)
    with pytest.raises(ValueError):
        module_path(tmp_path, 'win32')


def test_invalid_plugin_timeout_never_loads_binary(tmp_path):
    fake = tmp_path/'NeverLoad.vst3'
    fake.write_bytes(b'not executable')
    for timeout in [float('nan'), 0, 181]:
        with pytest.raises(ValueError):
            probe(fake, timeout)
