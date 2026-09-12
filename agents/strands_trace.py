from agents.event_bus import emit

def make_trace_handler(session_id, agent_name, grade=None):
    def handler(**kwargs):
        try:
            r = kwargs.get("reasoning")
            if r:
                txt = r.get("text") if isinstance(r, dict) else str(r)
                if txt: emit(session_id, agent_name, "reasoning", grade, message=str(txt)[:400])
            ts = kwargs.get("tool_start")
            if ts:
                emit(session_id, agent_name, "tool_call", grade,
                     message=f"🔧 calling {ts.get('name') if isinstance(ts, dict) else ts}")
            te = kwargs.get("tool_end")
            if te:
                emit(session_id, agent_name, "tool_result", grade,
                     message=str(te)[:300])
        except Exception:
            pass
    return handler
