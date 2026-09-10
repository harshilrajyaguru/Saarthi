"""
test_local_resource_3.py
------------------------
Retest script for Resource Agent evaluating 3 specific real-life reasoning scenarios:
  - Scenario 1: Offline Classroom (Grades 3, 5, 7, 35m, Internet unavailable)
  - Scenario 2: Contention (Grades 3, 4, 5, 6, 40m, 1 TV, 2 tablets)
  - Scenario 3: Setup Time (Grades 5 & 7, 10m session vs 8m TV / 6m printer setup)
"""

import sys
import json
import time
from pathlib import Path

# Ensure stdout uses UTF-8 to prevent Windows cp1252 encoding crashes
if sys.stdout.encoding and sys.stdout.encoding.lower() != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass

# Ensure project root is in sys.path
PROJECT_ROOT = Path(__file__).resolve().parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from agents.local_ollama import recommend_resources_local


def safe_recommend(*args, **kwargs):
    for attempt in range(3):
        try:
            return recommend_resources_local(*args, **kwargs)
        except Exception as e:
            if attempt == 2:
                raise
            time.sleep(2)


def run_3_scenarios():
    outputs = {}

    # =========================================================================
    # SCENARIO 1 — OFFLINE
    # =========================================================================
    print("=" * 80)
    print("SCENARIO 1 — OFFLINE CLASSROOM")
    print("=" * 80)

    sess_1 = {
        "available_time": "35m",
        "internet_available": False,
        "power_stable": True,
        "tv_available": True,
        "tv_count": 1,
        "tablets_available": True,
        "tablet_count": 3,
        "printer_available": True,
        "printer_has_paper": True,
        "whiteboard_available": True,
        "textbooks_available": True,
        "concurrent_demand": {
            "Grade_3_Math": "video-based resource requiring internet",
            "Grade_5_Math": "tablet-based resource",
            "Grade_7_Math": "printable resource"
        },
        "recent_usage_history": {
            "Grade_5_Math": "used tablets in previous session",
            "Grade_7_Math": "used worksheets in previous 2 sessions"
        }
    }

    res_1 = safe_recommend("3", "Math", "Addition", sess_1)
    outputs[1] = res_1
    print("FULL RESOURCE AGENT OUTPUT (SCENARIO 1):")
    print(json.dumps(res_1, indent=2))
    print("\n")

    # =========================================================================
    # SCENARIO 2 — CONTENTION
    # =========================================================================
    print("=" * 80)
    print("SCENARIO 2 — CONTENTION")
    print("=" * 80)

    sess_2 = {
        "available_time": "40m",
        "internet_available": True,
        "power_stable": True,
        "tv_available": True,
        "tv_count": 1,
        "tablets_available": True,
        "tablet_count": 2,
        "printer_available": True,
        "printer_has_paper": True,
        "whiteboard_available": True,
        "textbooks_available": True,
        "concurrent_demand": {
            "Grade_3_Math": "requests TV",
            "Grade_4_Math": "requests TV",
            "Grade_5_Math": "requests tablet",
            "Grade_6_Math": "requests tablet"
        }
    }

    res_2 = safe_recommend("3", "Math", "Fractions", sess_2)
    outputs[2] = res_2
    print("FULL RESOURCE AGENT OUTPUT (SCENARIO 2):")
    print(json.dumps(res_2, indent=2))
    print("\n")

    # =========================================================================
    # SCENARIO 3 — SETUP TIME
    # =========================================================================
    print("=" * 80)
    print("SCENARIO 3 — SETUP TIME (10 MINUTE SESSION)")
    print("=" * 80)

    sess_3 = {
        "available_time": "10m",
        "internet_available": True,
        "power_stable": True,
        "tv_available": True,
        "tv_setup_minutes": 8,
        "printer_available": True,
        "printer_has_paper": True,
        "printer_setup_minutes": 6,
        "tablets_available": True,
        "tablet_count": 2,
        "tablet_setup_minutes": 0,
        "whiteboard_available": True,
        "whiteboard_setup_minutes": 0,
        "textbooks_available": True,
        "concurrent_demand": {
            "Grade_5_Math": "wants TV or printable resource",
            "Grade_7_Math": "wants tablet"
        }
    }

    res_3 = safe_recommend("5", "Math", "Decimals", sess_3)
    outputs[3] = res_3
    print("FULL RESOURCE AGENT OUTPUT (SCENARIO 3):")
    print(json.dumps(res_3, indent=2))
    print("\n")

    return outputs


if __name__ == "__main__":
    run_3_scenarios()
