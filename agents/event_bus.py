import threading, time, uuid

_LOCK = threading.Lock()
_STREAMS = {}

def emit(session_id, agent, event, grade=None, message="", payload=None):
    ev = {"id": uuid.uuid4().hex, "ts": time.time(), "agent": agent,
          "event": event, "grade": grade, "message": message, "payload": payload}
    with _LOCK:
        _STREAMS.setdefault(session_id, []).append(ev)
    return ev

def get_events(session_id):
    with _LOCK:
        return list(_STREAMS.get(session_id, []))
