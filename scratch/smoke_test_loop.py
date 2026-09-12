import sys
import os

sys.path.insert(0, os.path.abspath("."))

from classroom_loop import ClassroomSession, ClassroomLoopRunner

def main():
    print("=== Testing Classroom Loop Runner Smoke Test ===")
    session = ClassroomSession(
        session_id="smoke_test_123",
        active_grades=["3", "4", "5"],
        subjects=["Math"]
    )
    runner = ClassroomLoopRunner(session)
    print("Starting cycle execution...")
    record = runner.run_cycle(trigger_type="initial")
    print(f"Cycle execution finished! Decision: {record.decision}")

if __name__ == "__main__":
    main()
