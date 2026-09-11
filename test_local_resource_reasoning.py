"""
test_local_resource_reasoning.py
--------------------------------
Real-life resource reasoning test for Saarthi Resource Agent (GPT-OSS-120B via Groq API).

Tests 8 real-life classroom resource constraint scenarios:
  1. Single Scarce Resource (1 TV contested between Grade 3 & 4)
  2. Offline Classroom (Internet unavailable)
  3. Printer Without Paper + Short Session (15m, printer paperless)
  4. Contention With Unequal Demand (TV requested by G3, G5, G8)
  5. Staleness Vs Availability (G4 used tablets 3 consecutive sessions)
  6. No Good Resource Exists (All hardware unavailable -> needs_generation = true)
  7. Multi-Grade Resource Collision (4 grades competing for TV and tablets)
  8. Setup Too Expensive (10m session vs 8m TV setup time)
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

from agents.local_ollama import recommend_resources_local


def safe_recommend(*args, **kwargs):
    for attempt in range(3):
        try:
            return recommend_resources_local(*args, **kwargs)
        except Exception as e:
            if attempt == 2:
                raise
            time.sleep(2)


def run_resource_reasoning_tests():
    results = {}

    # =========================================================================
    # SCENARIO 1 — SINGLE SCARCE RESOURCE
    # =========================================================================
    print("=" * 80)
    print("SCENARIO 1 — SINGLE SCARCE RESOURCE")
    print("=" * 80)

    sess_1 = {
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
            "Grade_3_Math": "needs visual display (TV)",
            "Grade_4_Math": "needs visual display (TV)",
            "Grade_5_Math": "needs tablets (2 tablets)"
        },
        "recent_usage_history": {
            "Grade_3_Math": "used TV yesterday",
            "Grade_4_Math": "has not used TV recently",
            "Grade_5_Math": "used tablets 2 sessions ago"
        }
    }

    res_1_g3 = safe_recommend("3", "Math", "Fractions", sess_1)
    res_1_g4 = safe_recommend("4", "Math", "Equivalent Fractions", sess_1)
    results[1] = {"Grade 3": res_1_g3, "Grade 4": res_1_g4}

    print("GRADE 3 RECOMMENDATION:")
    print(json.dumps(res_1_g3, indent=2))
    print("\nGRADE 4 RECOMMENDATION:")
    print(json.dumps(res_1_g4, indent=2))
    print("\n")

    # =========================================================================
    # SCENARIO 2 — OFFLINE CLASSROOM
    # =========================================================================
    print("=" * 80)
    print("SCENARIO 2 — OFFLINE CLASSROOM")
    print("=" * 80)

    sess_2 = {
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
            "Grade_3_Math": "wants video-based online streaming resource",
            "Grade_5_Math": "wants offline tablet activity",
            "Grade_7_Math": "wants printable worksheet resource"
        },
        "recent_usage_history": {
            "Grade_5_Math": "used tablets in previous session",
            "Grade_7_Math": "used worksheets in previous 2 sessions"
        }
    }

    res_2_g3 = safe_recommend("3", "Math", "Addition", sess_2)
    results[2] = res_2_g3
    print("GRADE 3 RECOMMENDATION (OFFLINE CLASSROOM):")
    print(json.dumps(res_2_g3, indent=2))
    print("\n")

    # =========================================================================
    # SCENARIO 3 — PRINTER WITHOUT PAPER + SHORT SESSION
    # =========================================================================
    print("=" * 80)
    print("SCENARIO 3 — PRINTER WITHOUT PAPER + SHORT SESSION (15 MINUTES)")
    print("=" * 80)

    sess_3 = {
        "available_time": "15m",
        "internet_available": True,
        "power_stable": True,
        "printer_available": True,
        "printer_has_paper": False,
        "paper_available": False,
        "tv_available": True,
        "tv_count": 1,
        "tablets_available": True,
        "tablet_count": 1,
        "whiteboard_available": True,
        "textbooks_available": True,
        "concurrent_demand": {
            "Grade_4_Math": "requests printable material",
            "Grade_6_Math": "requests tablet activity"
        },
        "recent_usage_history": {
            "Grade_4_Math": "used textbook activity last session",
            "Grade_6_Math": "used tablet last session"
        }
    }

    res_3_g4 = safe_recommend("4", "Math", "Equivalent Fractions", sess_3)
    results[3] = res_3_g4
    print("GRADE 4 RECOMMENDATION (PAPERLESS PRINTER):")
    print(json.dumps(res_3_g4, indent=2))
    print("\n")

    # =========================================================================
    # SCENARIO 4 — CONTENTION WITH UNEQUAL DEMAND
    # =========================================================================
    print("=" * 80)
    print("SCENARIO 4 — CONTENTION WITH UNEQUAL DEMAND")
    print("=" * 80)

    sess_4 = {
        "available_time": "45m",
        "internet_available": True,
        "power_stable": True,
        "tv_available": True,
        "tv_count": 1,
        "tablets_available": True,
        "tablet_count": 2,
        "printer_available": True,
        "printer_has_paper": True,
        "whiteboard_available": True,
        "concurrent_demand": {
            "Grade_3_Math": "requests TV",
            "Grade_5_Math": "requests TV",
            "Grade_8_Math": "requests TV + tablet"
        },
        "recent_usage_history": {
            "Grade_3_Math": "has not used TV recently",
            "Grade_5_Math": "used TV in previous session",
            "Grade_8_Math": "used TV 3 sessions ago"
        }
    }

    res_4_g3 = safe_recommend("3", "Math", "Multiplication", sess_4)
    results[4] = res_4_g3
    print("GRADE 3 RECOMMENDATION (3-WAY TV CONTENTION):")
    print(json.dumps(res_4_g3, indent=2))
    print("\n")

    # =========================================================================
    # SCENARIO 5 — STALENESS VS AVAILABILITY
    # =========================================================================
    print("=" * 80)
    print("SCENARIO 5 — STALENESS VS AVAILABILITY")
    print("=" * 80)

    sess_5 = {
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
            "Grade_4_Math": "needs digital practice (tablets)",
            "Grade_6_Math": "needs digital practice (tablets)"
        },
        "recent_usage_history": {
            "Grade_4_Math": "used tablets for last 3 consecutive sessions (STALE!)",
            "Grade_6_Math": "has not used tablets recently",
            "Grade_4_printed": "has not used printed material recently",
            "Grade_6_printed": "used printed material last session"
        }
    }

    res_5_g4 = safe_recommend("4", "Math", "Fractions", sess_5)
    results[5] = res_5_g4
    print("GRADE 4 RECOMMENDATION (HIGH STALENESS):")
    print(json.dumps(res_5_g4, indent=2))
    print("\n")

    # =========================================================================
    # SCENARIO 6 — NO GOOD RESOURCE EXISTS
    # =========================================================================
    print("=" * 80)
    print("SCENARIO 6 — NO GOOD RESOURCE EXISTS (HARDWARE ALL UNAVAILABLE)")
    print("=" * 80)

    sess_6 = {
        "available_time": "20m",
        "internet_available": False,
        "power_stable": False,
        "tv_available": False,
        "tablets_available": False,
        "printer_available": False,
        "whiteboard_available": True,
        "textbooks_available": True,
        "concurrent_demand": {},
        "resource_needs": "Requires specialized interactive practice which is unavailable offline/in textbooks"
    }

    res_6 = safe_recommend("5", "Math", "Decimals", sess_6)
    results[6] = res_6
    print("GRADE 5 RECOMMENDATION (NO DEPLOYABLE HARDWARE):")
    print(json.dumps(res_6, indent=2))
    print("\n")

    # =========================================================================
    # SCENARIO 7 — MULTI-GRADE RESOURCE COLLISION
    # =========================================================================
    print("=" * 80)
    print("SCENARIO 7 — MULTI-GRADE RESOURCE COLLISION")
    print("=" * 80)

    sess_7 = {
        "available_time": "40m",
        "internet_available": True,
        "tv_available": True,
        "tv_count": 1,
        "tablets_available": True,
        "tablet_count": 2,
        "printer_available": True,
        "printer_has_paper": True,
        "whiteboard_available": True,
        "textbooks_available": True,
        "concurrent_demand": {
            "Grade_3_Math": "requires TV",
            "Grade_4_Math": "requires TV",
            "Grade_5_Math": "requires tablet",
            "Grade_6_Math": "requires tablet"
        }
    }

    res_7_g3 = safe_recommend("3", "Math", "Addition", sess_7)
    results[7] = res_7_g3
    print("GRADE 3 RECOMMENDATION (MULTI-GRADE COLLISION):")
    print(json.dumps(res_7_g3, indent=2))
    print("\n")

    # =========================================================================
    # SCENARIO 8 — SETUP TOO EXPENSIVE
    # =========================================================================
    print("=" * 80)
    print("SCENARIO 8 — SETUP TOO EXPENSIVE (10 MINUTE SESSION)")
    print("=" * 80)

    sess_8 = {
        "available_time": "10m",
        "internet_available": True,
        "power_stable": True,
        "tv_available": True,
        "tv_setup_minutes": 8,
        "printer_available": True,
        "printer_setup_minutes": 6,
        "tablets_available": True,
        "tablet_count": 2,
        "tablet_setup_minutes": 0,
        "whiteboard_available": True,
        "whiteboard_setup_minutes": 0,
        "concurrent_demand": {
            "Grade_5_Math": "wants TV or printable resource",
            "Grade_7_Math": "wants tablet"
        }
    }

    res_8_g5 = safe_recommend("5", "Math", "Fractions", sess_8)
    results[8] = res_8_g5
    print("GRADE 5 RECOMMENDATION (10m SESSION vs 8m SETUP):")
    print(json.dumps(res_8_g5, indent=2))
    print("\n")

    return results


if __name__ == "__main__":
    run_resource_reasoning_tests()
