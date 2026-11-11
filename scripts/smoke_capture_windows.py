"""Optional native capture check; --play-test-tone plays a quiet 0.3 s synthetic tone."""
import argparse
import ctypes as c
import json
import os


def run():
    import numpy as np
    from ableton_agent.windows_capture import ProcessCapture, WaveFormat, SAMPLE_RATE
    class Header(c.Structure):
        _fields_ = [("data", c.c_void_p), ("length", c.c_uint32), ("recorded", c.c_uint32),
                    ("user", c.c_size_t), ("flags", c.c_uint32), ("loops", c.c_uint32),
                    ("next", c.c_void_p), ("reserved", c.c_size_t)]
    audio = np.sin(2 * np.pi * 1000 * np.arange(round(SAMPLE_RATE * 0.3)) / SAMPLE_RATE) * 0.005
    pcm = np.column_stack((audio, audio))
    buffer = c.create_string_buffer((pcm * 32767).astype("<i2").tobytes())
    header = Header(c.cast(buffer, c.c_void_p), len(buffer) - 1, 0, 0, 0, 0, None, 0)
    fmt = WaveFormat(1, 2, SAMPLE_RATE, SAMPLE_RATE * 4, 4, 16, 0)
    winmm = c.WinDLL("winmm")
    handle = c.c_void_p()
    winmm.waveOutOpen.argtypes = [c.POINTER(c.c_void_p), c.c_uint32, c.POINTER(WaveFormat), c.c_size_t, c.c_size_t, c.c_uint32]
    for name in ("waveOutPrepareHeader", "waveOutWrite", "waveOutUnprepareHeader"):
        getattr(winmm, name).argtypes = [c.c_void_p, c.POINTER(Header), c.c_uint32]
    winmm.waveOutReset.argtypes = [c.c_void_p]
    winmm.waveOutClose.argtypes = [c.c_void_p]
    def check(result):
        if result:
            raise OSError("WinMM result %d" % result)
    with ProcessCapture(os.getpid()) as capture:
        check(winmm.waveOutOpen(c.byref(handle), 0xffffffff, c.byref(fmt), 0, 0, 0))
        prepared = False
        try:
            check(winmm.waveOutPrepareHeader(handle, c.byref(header), c.sizeof(header)))
            prepared = True
            check(winmm.waveOutWrite(handle, c.byref(header), c.sizeof(header)))
            y, report = capture.record(0.65)
        finally:
            winmm.waveOutReset(handle)
            if prepared:
                winmm.waveOutUnprepareHeader(handle, c.byref(header), c.sizeof(header))
            winmm.waveOutClose(handle)
    peak = float(np.max(np.abs(y))) if len(y) else 0
    return {**report, "test": "quiet synthetic process tone", "peak": peak,
            "signal_detected": peak > 0.0001,
            "limitation": "Validates this process/backend, not Ableton's audio driver path or transport alignment"}


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--play-test-tone", action="store_true", required=True)
    parser.parse_args()
    print(json.dumps(run(), indent=2))
