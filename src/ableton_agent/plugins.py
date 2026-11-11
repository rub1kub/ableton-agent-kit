"""Probe trusted installed VST3s in a child process, independently of Live."""
import hashlib
import json
import math
import subprocess
import sys
import tempfile
from pathlib import Path

from .common import sha256


def fingerprint(path):
    path = Path(path).absolute()
    if path.suffix.lower() != '.vst3' or not path.exists() or path.is_symlink():
        raise ValueError('Expected an existing trusted VST3 file or bundle, not a symlink')
    files = [path] if path.is_file() else sorted(p for p in path.rglob('*') if p.is_file())
    if not files or any(p.is_symlink() for p in path.rglob('*')):
        raise ValueError('Empty or symlinked VST3 bundle')
    digest = hashlib.sha256()
    for p in files:
        name = p.name if path.is_file() else p.relative_to(path).as_posix()
        digest.update(json.dumps([name, sha256(p)], separators=(',', ':')).encode())
    return {'path': str(path), 'sha256': digest.hexdigest(), 'files': len(files)}


def probe(path, timeout=90):
    if not math.isfinite(timeout) or not 1 <= timeout <= 180:
        raise ValueError('Timeout must be between 1 and 180 seconds')
    identity = fingerprint(path)
    with tempfile.TemporaryDirectory(prefix='ableton-plugin-') as tmp:
        report, log = Path(tmp)/'report.json', Path(tmp)/'worker.log'
        with log.open('wb') as stream:
            try:
                result = subprocess.run([sys.executable, '-m', 'ableton_agent.plugins',
                                         identity['path'], str(report)], stdout=stream,
                                        stderr=stream, timeout=timeout, check=False)
            except subprocess.TimeoutExpired as exc:
                raise RuntimeError('VST3 probe timed out; child process was stopped') from exc
        if result.returncode != 0 or not report.exists():
            with log.open('rb') as stream:
                stream.seek(max(0, log.stat().st_size-2000))
                detail = stream.read().decode('utf-8', errors='replace')
            raise RuntimeError(f'VST3 host failed ({result.returncode}): {detail}')
        if report.stat().st_size > 4*1024*1024:
            raise RuntimeError('Unexpectedly large VST3 report')
        data = json.loads(report.read_text(encoding='utf-8'))
    if fingerprint(path) != identity:
        raise RuntimeError('Plugin changed during probe; discard the report')
    return {**identity, **data}


def module_path(path, platform=None):
    path = Path(path)
    if (platform or sys.platform) == 'win32' and path.is_dir():
        modules = list((path/'Contents/x86_64-win').glob('*.vst3'))
        if len(modules) != 1:
            raise ValueError('Expected one Windows x64 VST3 module inside the bundle')
        return modules[0]
    return path


def worker(path, output):
    import numpy as np
    import pedalboard

    module = module_path(path)
    plugin = pedalboard.load_plugin(str(module))
    parameters = []
    for key, p in plugin.parameters.items():
        parameters.append({'key': key, 'name': p.name, 'raw_value': float(p.raw_value),
                           'label': p.label, 'display': str(getattr(plugin, key))})
    rate = 48000
    if plugin.is_instrument:
        audio = plugin([([0x90, 60, 64], 0.05), ([0x80, 60, 0], 0.55)],
                       duration=1.0, sample_rate=rate, num_channels=2)
    else:
        t = np.arange(rate, dtype=np.float32)/rate
        x = (0.01*np.sin(2*np.pi*220*t) + 0.003*np.sin(2*np.pi*1700*t)).astype(np.float32)
        x[rate//2:] = 0
        audio = plugin(np.stack([x, x]), rate)
    report = {'host': 'pedalboard', 'host_version': pedalboard.__version__, 'loaded_module': str(module),
              'name': plugin.name, 'is_instrument': bool(plugin.is_instrument),
              'parameter_count': len(parameters), 'parameters': parameters,
              'smoke': {'sample_rate': rate, 'shape': list(audio.shape),
                        'finite': bool(np.all(np.isfinite(audio))),
                        'peak': float(np.max(np.abs(audio))) if audio.size else None},
              'limitations': ['Separate default plugin instance; not the instance or preset in Live.',
                              'Pedalboard raw_value uses 0..1; do not copy this mapping to Live blindly.',
                              'Units/display are host-inferred and can be inaccurate.',
                              'Synthetic one-second smoke test is not a quality judgment or full tail test.',
                              'No playback, microphone, driver or Live transport used.']}
    Path(output).write_text(json.dumps(report, ensure_ascii=False, allow_nan=False), encoding='utf-8')


if __name__ == '__main__':
    worker(sys.argv[1], sys.argv[2])
