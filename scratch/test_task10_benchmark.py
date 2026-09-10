import sys
import os
sys.path.insert(0, os.path.abspath("."))
import time
import json
import asyncio
from api import start_classroom_session

payload = {
    "grade_selection": [
        {"grade": "3", "subject": "Mathematics"},
        {"grade": "5", "subject": "Mathematics"},
        {"grade": "6", "subject": "Mathematics"}
    ],
    "duration_minutes": 40,
    "resources": {
        "tv": True,
        "tablets": 2,
        "printer": True,
        "internet": False
    },
    "connectivity": "offline"
}

async def run_benchmark():
    print("--- SESSION 1 (Cold Start) ---")
    start_time = time.perf_counter()
    res1 = await start_classroom_session(payload)
    end_time = time.perf_counter()
    latency1 = end_time - start_time
    print(f"Session 1 Latency: {latency1:.4f} seconds ({latency1 * 1000:.2f} ms)")

    print("\n--- SESSION 2 (Warm Process) ---")
    start_time = time.perf_counter()
    res2 = await start_classroom_session(payload)
    end_time = time.perf_counter()
    latency2 = end_time - start_time
    print(f"Session 2 Latency: {latency2:.4f} seconds ({latency2 * 1000:.2f} ms)")

if __name__ == "__main__":
    asyncio.run(run_benchmark())
