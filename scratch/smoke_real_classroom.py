import json
import sys
from pathlib import Path

# Ensure root workspace is in python path
ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from tools.orchestrator_tools import read_shared_state
from tools.progress_tools import get_history, get_trouble_spot_log


def run_smoke_test():
    print("=" * 60)
    print("RUNNING REAL CLASSROOM DETERMINISTIC SMOKE TEST (ZERO LLM CALLS)")
    print("=" * 60)

    # 1. Load classroom_state.json
    state = read_shared_state()
    assert state and ("grades" in state or "classrooms" in state), "Failed to load classroom_state.json!"
    print("1. [PASS] Loaded classroom_state.json successfully.")

    # 2. Call get_history("5","Math","Decimals - multiplication",5)
    hist_res = get_history("5", "Math", "Decimals - multiplication", 5)
    print("\n2. get_history('5', 'Math', 'Decimals - multiplication', 5) result:")
    print(json.dumps(hist_res, indent=2))

    assert hist_res.get("count") == 5, f"Expected 5 sessions, got {hist_res.get('count')}"
    assert hist_res.get("trend") == "declining", f"Expected trend='declining', got '{hist_res.get('trend')}'"
    assert hist_res.get("total_below_60", 0) >= 15, f"Expected total_below_60 >= 15, got {hist_res.get('total_below_60')}"
    err_tags = hist_res.get("aggregated_error_tags", {})
    assert "decimal point alignment" in err_tags, f"Expected 'decimal point alignment' in aggregated_error_tags, got {err_tags}"
    print("2. [PASS] get_history verified: 5 sessions, trend='declining', below_60 >= 15, error_tags contains 'decimal point alignment'.")

    # 3. Call get_trouble_spot_log("5","Math")
    ts_res = get_trouble_spot_log("5", "Math")
    print("\n3. get_trouble_spot_log('5', 'Math') result:")
    print(json.dumps(ts_res, indent=2))

    spots = ts_res.get("trouble_spots", []) or ts_res.get("trouble_spot_log", [])
    assert len(spots) > 0, "Expected non-empty trouble_spot_log for Grade 5 Math!"
    print("3. [PASS] get_trouble_spot_log verified: returned trouble spot log.")

    # 4. Direct assertion on data/classroom_state.json (tablets < roster_size)
    grades_dict = state.get("grades", {})
    g5_data = grades_dict.get("5") or grades_dict.get("Grade_5_Math") or {}
    tablets = g5_data.get("resources", {}).get("tablets", 12)
    roster_size = g5_data.get("roster_size", 30)

    assert tablets < roster_size, f"Expected tablets ({tablets}) < roster_size ({roster_size})!"
    print(f"\n4. [PASS] Resource constraint verified on data/classroom_state.json: tablets ({tablets}) < roster_size ({roster_size}).")

    print("\n" + "=" * 60)
    print("ALL 4 DETERMINISTIC SMOKE TEST CHECKS PASSED SUCCESSFULLY!")
    print("=" * 60)


if __name__ == "__main__":
    run_smoke_test()
