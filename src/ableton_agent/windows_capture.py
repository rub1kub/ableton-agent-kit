"""Windows process-tree loopback. No endpoint/driver/monitor settings are changed.

Requires Windows build 20348+ and comtypes. 44.1 kHz, PCM16 stereo is a
measurement capture, not a replacement for a native full-resolution export.
"""
import sys
if sys.platform != "win32":
    raise ImportError("Process loopback capture is Windows-only")

import ctypes as c
from ctypes import wintypes as W
import threading
import time

import comtypes
from comtypes import GUID, IUnknown, COMMETHOD, COMObject
import numpy as np

H, U, P, L = c.c_long, c.c_uint32, c.c_void_p, c.c_int64
IID_AUDIO = GUID("{1CB9AD4C-DBFA-4c32-B178-C2F568A703B2}")
IID_CAPTURE = GUID("{C8ADBD64-E71E-48a0-A4DE-185C395CD317}")
SAMPLE_RATE = 44100


def method(ptr, index, *params):
    table = c.cast(ptr, c.POINTER(c.POINTER(P))).contents
    return c.WINFUNCTYPE(H, P, *params)(table[index])


def invoke(ptr, index, types=(), *args):
    hr = method(ptr, index, *types)(ptr, *args)
    if hr < 0:
        raise OSError("WASAPI HRESULT 0x%08x at method %d" % (hr & 0xffffffff, index))
    return hr


class Completed(IUnknown):
    _iid_ = GUID("{41D949AB-9862-444A-80F6-C261334DA5EB}")
    _methods_ = [COMMETHOD([], c.HRESULT, "ActivateCompleted", (["in"], P, "operation"))]


class Agile(IUnknown):
    _iid_ = GUID("{94ea2b94-e9cc-49e0-c0ff-ee64ca8f5b90}")
    _methods_ = []


class Activation(COMObject):
    _com_interfaces_ = [Completed, Agile]

    def __init__(self):
        super().__init__()
        self.ready, self.ptr, self.error = threading.Event(), P(), None

    def ActivateCompleted(self, operation):
        try:
            result = H()
            invoke(operation, 3, (c.POINTER(H), c.POINTER(P)), c.byref(result), c.byref(self.ptr))
            if result.value < 0:
                raise OSError("Audio activation HRESULT 0x%08x" % (result.value & 0xffffffff))
        except Exception as exc:
            self.error = exc
        finally:
            self.ready.set()
        return 0


class Blob(c.Structure):
    _fields_ = [("size", U), ("data", P)]


class Variant(c.Structure):
    _fields_ = [("vt", W.WORD), ("r1", W.WORD), ("r2", W.WORD), ("r3", W.WORD), ("blob", Blob)]


class WaveFormat(c.Structure):
    _pack_ = 1
    _fields_ = [("tag", W.WORD), ("channels", W.WORD), ("rate", U), ("avg", U),
                ("align", W.WORD), ("bits", W.WORD), ("extra", W.WORD)]


class ProcessCapture:
    def __init__(self, pid):
        if sys.getwindowsversion().build < 20348 or int(pid) <= 0:
            raise ValueError("Need Windows build 20348+ and a positive target PID")
        self.audio, self.capture_client, self.event, self.operation = P(), P(), None, P()
        self.started, self.closed, self.discontinuities = False, False, 0
        self._com_initialized = False
        # comtypes initializes the importing thread. Each capture may run in another thread.
        try:
            comtypes.CoInitializeEx(comtypes.COINIT_MULTITHREADED)
            self._com_initialized = True
        except OSError as exc:
            # comtypes may already have initialized this thread as STA. The callback
            # declares IAgileObject, so keep the caller's apartment without changing it.
            if getattr(exc, "winerror", None) != -2147417850:  # RPC_E_CHANGED_MODE
                raise
        try:
            params = (U * 3)(1, int(pid), 0)  # process loopback, include target and children
            var = Variant(65, 0, 0, 0, Blob(c.sizeof(params), c.cast(params, P)))
            self.handler = Activation()
            callback = self.handler.QueryInterface(Completed)
            api = c.WinDLL("Mmdevapi.dll").ActivateAudioInterfaceAsync
            api.argtypes = (W.LPCWSTR, c.POINTER(GUID), c.POINTER(Variant), P, c.POINTER(P))
            api.restype = H
            hr = api("VAD\\Process_Loopback", c.byref(IID_AUDIO), c.byref(var), c.cast(callback, P), c.byref(self.operation))
            if hr < 0:
                raise OSError("Activation call HRESULT 0x%08x" % (hr & 0xffffffff))
            if not self.handler.ready.wait(8):
                raise TimeoutError("WASAPI activation timed out")
            if self.handler.error:
                raise self.handler.error
            self.audio = self.handler.ptr
            kernel = c.WinDLL("kernel32", use_last_error=True)
            create = kernel.CreateEventW
            create.argtypes, create.restype = (P, W.BOOL, W.BOOL, W.LPCWSTR), P
            self.event = create(None, False, False, None)
            if not self.event:
                raise c.WinError(c.get_last_error())
            fmt = WaveFormat(1, 2, SAMPLE_RATE, SAMPLE_RATE * 4, 4, 16, 0)
            invoke(self.audio, 3, (U, U, L, L, c.POINTER(WaveFormat), P),
                   0, 0x80060000, 0, 0, c.byref(fmt), None)
            invoke(self.audio, 13, (P,), self.event)
            invoke(self.audio, 14, (c.POINTER(GUID), c.POINTER(P)), c.byref(IID_CAPTURE), c.byref(self.capture_client))
            invoke(self.audio, 10)
            self.started = True
        except Exception:
            self.close()
            raise

    def drain(self):
        blocks, size = [], U()
        while True:
            invoke(self.capture_client, 5, (c.POINTER(U),), c.byref(size))
            if not size.value:
                break
            pointer, frames, flags = P(), U(), U()
            invoke(self.capture_client, 3, (c.POINTER(P), c.POINTER(U), c.POINTER(U), P, P),
                   c.byref(pointer), c.byref(frames), c.byref(flags), None, None)
            try:
                if flags.value & 1:
                    self.discontinuities += 1
                blocks.append(bytes(frames.value * 4) if flags.value & 2 else c.string_at(pointer, frames.value * 4))
            finally:
                invoke(self.capture_client, 4, (U,), frames.value)
        return blocks

    def record(self, seconds, progress=None):
        seconds = float(seconds)
        if not math_isfinite_positive(seconds) or seconds > 600:
            raise ValueError("Capture length must be 0..600 seconds")
        self.drain()
        self.discontinuities = 0
        blocks, started, next_update = [], time.monotonic(), 0
        while time.monotonic() - started < seconds:
            blocks.extend(self.drain())
            elapsed = time.monotonic() - started
            if progress and elapsed >= next_update:
                progress(elapsed)
                next_update = elapsed + 5
            time.sleep(0.01)
        blocks.extend(self.drain())
        data = np.frombuffer(b"".join(blocks), "<i2").reshape(-1, 2).astype(np.float64) / 32768
        return data, {"wall_duration_s": time.monotonic() - started, "audio_duration_s": len(data) / SAMPLE_RATE,
                      "packet_discontinuities": self.discontinuities, "sample_rate": SAMPLE_RATE,
                      "source": "process tree loopback", "transport_controlled": False,
                      "physical_listening_performed": False}

    def close(self):
        if self.closed:
            return
        self.closed = True
        try:
            if self.started:
                invoke(self.audio, 11)
        finally:
            for pointer in (self.capture_client, self.audio, self.operation):
                if pointer:
                    method(pointer, 2)(pointer)
            if self.event:
                close = c.WinDLL("kernel32").CloseHandle
                close.argtypes = [P]
                close(self.event)
            if self._com_initialized:
                comtypes.CoUninitialize()
                self._com_initialized = False

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()


def math_isfinite_positive(n):
    import math
    return math.isfinite(n) and n > 0
