import json
import socket
import threading

import pytest

from ableton_agent.live import LiveClient, LiveError, transport_check


def server(response):
    listener = socket.socket()
    listener.bind(("127.0.0.1", 0))
    listener.listen(1)
    port = listener.getsockname()[1]
    def worker():
        try:
            conn, _ = listener.accept()
            with conn, conn.makefile("rb") as f:
                request = json.loads(f.readline())
                wire = response(request)
                conn.sendall(wire[:5])
                conn.sendall(wire[5:])
        finally:
            listener.close()
    thread = threading.Thread(target=worker, daemon=True)
    thread.start()
    return port, thread


def test_framing():
    port, thread = server(lambda r: json.dumps({"id": r["id"], "status": "success", "result": {"tempo": 112}}).encode() + b"\n")
    assert LiveClient(port=port).call("get_session_info")["tempo"] == 112
    thread.join(2)


def test_write_gates(tmp_path):
    with pytest.raises(PermissionError):
        LiveClient().call("start_playback")
    with pytest.raises(ValueError, match="journal"):
        LiveClient().call("start_playback", allow_write=True)
    with pytest.raises(ValueError, match="allowlist"):
        LiveClient(journal_dir=tmp_path).call("eval_python", allow_write=True)


@pytest.mark.parametrize("wire", [b'{"status":"success","result":1}', b"x" * 120 + b"\n",
                                  b'{"id":"wrong","status":"success","result":1}\n'])
def test_bad_responses(wire):
    port, thread = server(lambda _: wire)
    with pytest.raises(LiveError):
        LiveClient(port=port, max_response=100).call("get_song_time")
    thread.join(2)


def test_write_journal(tmp_path):
    port, thread = server(lambda r: b'{"status":"success","result":{"playing":false}}\n')
    LiveClient(port=port, journal_dir=tmp_path).call("stop_playback", allow_write=True)
    assert len(list(tmp_path.glob("*.request.json"))) == 1
    assert len(list(tmp_path.glob("*.result.json"))) == 1
    thread.join(2)


def test_failure_does_not_retry(tmp_path):
    port, thread = server(lambda r: b'{"status":"error","error":"stale"}\n')
    with pytest.raises(LiveError, match="unconfirmed"):
        LiveClient(port=port, journal_dir=tmp_path).call("stop_playback", allow_write=True)
    assert len(list(tmp_path.glob("*.error.json"))) == 1
    thread.join(2)


def test_transport_jumps():
    good = [{"wall_s": 0, "beat": 10}, {"wall_s": 1, "beat": 12}, {"wall_s": 2, "beat": 14}]
    assert transport_check(good, 120)["valid"]
    good[2]["beat"] = 4
    assert not transport_check(good, 120)["valid"]
