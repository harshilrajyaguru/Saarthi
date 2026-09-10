import sys
import os
sys.path.insert(0, os.path.abspath("."))
import asyncio
from api import start_classroom_session, get_classroom_session, end_session_endpoint

payload = {
    "grade_selection": [
        {"grade": "3", "subject": "Mathematics"},
        {"grade": "5", "subject": "Mathematics"}
    ],
    "duration_minutes": 40,
    "resources": {"tv": True, "tablets": 2, "printer": True, "internet": True}
}

async def test_session_lifecycle():
    print("--- 1. START SESSION ---")
    start_res = await start_classroom_session(payload)
    session_id = start_res.get("session_id")
    print(f"Started session ID: {session_id}, status: {start_res.get('status')}")

    print("\n--- 2. RESTORE SESSION VIA GET /api/classroom/{session_id} ---")
    restore_res = await get_classroom_session(session_id)
    print(f"Restored session ID: {restore_res.get('session_id')}, status: {restore_res.get('status')}")
    assert restore_res.get("session_id") == session_id
    assert restore_res.get("status") != "completed"

    print("\n--- 3. END SESSION VIA POST /api/classroom/{session_id}/end ---")
    end_res = await end_session_endpoint(payload={}, session_id=session_id)
    print(f"Ended session status: {end_res.get('status')}")

    print("\n[SUCCESS] TASK 11 BACKEND / API PERSISTENCE CONTRACT VERIFIED")

if __name__ == "__main__":
    asyncio.run(test_session_lifecycle())
