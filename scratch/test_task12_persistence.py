import sys
import os
sys.path.insert(0, os.path.abspath("."))
import asyncio
from api import start_classroom_session, get_classroom_session, end_session_endpoint, SESSIONS

payload = {
    "grade_selection": [
        {"grade": "3", "subject": "Mathematics"},
        {"grade": "5", "subject": "Mathematics"}
    ],
    "duration_minutes": 40,
    "resources": {"tv": True, "tablets": 2, "printer": True, "internet": True}
}

async def run_task12_verification():
    print("=== 1. FIRST SESSION START ===")
    start_res = await start_classroom_session(payload)
    session_id = start_res.get("session_id")
    print(f"Session created: {session_id}, status: {start_res.get('status')}")
    assert session_id is not None
    assert SESSIONS.get(session_id) is not None

    print("\n=== 2. NORMAL GET /api/classroom/{session_id} ===")
    normal_res = await get_classroom_session(session_id)
    print(f"Normal GET session status: {normal_res.get('status')}")
    assert normal_res.get("session_id") == session_id

    print("\n=== 3. BACKEND PROCESS RESTART SIMULATION (Clearing SESSIONS registry) ===")
    SESSIONS.clear()
    assert SESSIONS.get(session_id) is None
    print("In-memory SESSIONS dictionary cleared.")

    print("\n=== 4. RECOVERY GET /api/classroom/{session_id} AFTER RESTART ===")
    recovered_res = await get_classroom_session(session_id)
    print(f"Recovered session ID: {recovered_res.get('session_id')}, status: {recovered_res.get('status')}")
    assert recovered_res.get("session_id") == session_id
    assert recovered_res.get("status") != "completed"
    assert len(recovered_res.get("current_session_grades", [])) == 2

    print("\n=== 5. END SESSION ===")
    end_res = await end_session_endpoint(payload={}, session_id=session_id)
    print(f"End session response status: {end_res.get('status')}")

    print("\n=== 6. GET /api/classroom/{session_id} AFTER END ===")
    after_end_res = await get_classroom_session(session_id)
    print(f"After-end session status: {after_end_res.get('status')}")
    assert after_end_res.get("status") == "completed"

    print("\n[PASSED] TASK 12 BACKEND RECOVERY & PERSISTENCE VERIFICATION SUCCESSFUL")

if __name__ == "__main__":
    asyncio.run(run_task12_verification())
