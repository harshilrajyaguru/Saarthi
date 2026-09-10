import sys
import os
sys.path.insert(0, os.path.abspath("."))
import time
import json
import asyncio

from agents.progress_agent import analyze_progress
from agents.curriculum_agent import reconcile_curriculum
from agents.resource_agent import recommend_resources
from agents.activity_agent import design_activity
from agents.safety_gate import evaluate_safety_gate

def profile_single_grade(g_str="3", subj_str="Math", topic="Equivalent fractions"):
    print(f"\n--- Profiling Grade {g_str} {subj_str} ---")
    
    t0 = time.perf_counter()
    p_diag = analyze_progress(g_str, subj_str, topic, {})
    t1 = time.perf_counter()
    print(f"1. Progress Agent:    {(t1 - t0)*1000:.2f} ms")

    c_dec = reconcile_curriculum(g_str, subj_str, topic, p_diag, {"available_time": "40m"})
    t2 = time.perf_counter()
    print(f"2. Curriculum Agent:  {(t2 - t1)*1000:.2f} ms")

    r_rec = recommend_resources(g_str, subj_str, topic, {"duration_minutes": 40})
    t3 = time.perf_counter()
    print(f"3. Resource Agent:    {(t3 - t2)*1000:.2f} ms")

    act = design_activity(g_str, subj_str, topic, "hold", ["confusing numerator"], "developing", "reinforce", "printable_worksheet", False, 40)
    t4 = time.perf_counter()
    print(f"4. Activity Agent:    {(t4 - t3)*1000:.2f} ms")

    sg = evaluate_safety_gate(act, topic, "confusing numerator", 40)
    t5 = time.perf_counter()
    print(f"5. Safety Gate:       {(t5 - t4)*1000:.2f} ms")
    print(f"TOTAL SINGLE GRADE:   {(t5 - t0)*1000:.2f} ms")

if __name__ == "__main__":
    profile_single_grade("3")
    profile_single_grade("5")
    profile_single_grade("6")
