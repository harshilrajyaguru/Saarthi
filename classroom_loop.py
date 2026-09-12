import os
import time
import traceback
from concurrent.futures import ThreadPoolExecutor
from dotenv import load_dotenv
load_dotenv()

import json
import uuid
from dataclasses import dataclass, field, asdict
from typing import Any, Optional

# Import exact existing frozen agent functions & state tools
from agents.progress_agent import analyze_progress
from agents.curriculum_agent import reconcile_curriculum
from agents.resource_agent import recommend_resources
from agents.activity_agent import design_activity
from agents.safety_gate import evaluate_safety_gate, SafetyGateResult
from agents.orchestrator_agent import run_orchestration_cycle, OrchestrationResult, NextAction
from tools.orchestrator_tools import read_shared_state, write_shared_state, get_active_grades


@dataclass
class DeliveredActivity:
    activity_id: str
    grade: str
    subject: str
    topic: str
    activity_type: str
    content: dict
    estimated_time_minutes: int
    delivery_status: str = "delivered"
    delivered_at_cycle: int = 1


@dataclass
class CycleRecord:
    cycle_number: int
    trigger_type: str  # "initial", "feedback", "resource_change", "adaptation"
    active_evaluations: list[str]
    progress_diagnoses: dict[str, Any] = field(default_factory=dict)
    curriculum_decisions: dict[str, Any] = field(default_factory=dict)
    resource_recommendations: dict[str, Any] = field(default_factory=dict)
    activity_designs: dict[str, Any] = field(default_factory=dict)
    safety_verdicts: dict[str, Any] = field(default_factory=dict)
    orchestration_result: Optional[dict] = field(default=None)
    decision: str = "CONTINUE"  # "CONTINUE", "ADAPT", "ESCALATE", "END"


@dataclass
class ClassroomSession:
    session_id: str
    active_grades: list[str]
    subjects: list[str]
    session_duration_minutes: int = 40
    remaining_time_minutes: int = 40
    session_constraints: dict[str, Any] = field(default_factory=dict)
    classroom_resources: dict[str, Any] = field(default_factory=dict)
    status: str = "active"  # "active", "adapting", "escalated", "ended"
    current_cycle: int = 0
    latest_signals: dict[str, Any] = field(default_factory=dict)
    delivered_activities: list[DeliveredActivity] = field(default_factory=list)
    cycle_history: list[CycleRecord] = field(default_factory=list)


def parse_grade_subject(grade_key: str) -> tuple[str, str]:
    """
    Generic grade/subject parser supporting any Grade 1-8 key format.
    Format example: 'Grade_2_Math' -> ('2', 'Math')
    Format example: 'Grade_8_Science' -> ('8', 'Science')
    """
    parts = grade_key.split("_")
    if len(parts) >= 3 and parts[0] == "Grade":
        s = "_".join(parts[2:])
        s_norm = "Math" if s.lower() in ["mathematics", "maths", "math"] else s.capitalize()
        return parts[1], s_norm
    elif len(parts) == 2 and parts[0] == "Grade":
        return parts[1], "Math"
    clean = grade_key.replace("Grade", "").strip()
    return clean if clean else "3", "Math"


# ANSI Color Codes for Rich Terminal Logging
ANSI_CYAN = "\033[96m"
ANSI_GREEN = "\033[92m"
ANSI_YELLOW = "\033[93m"
ANSI_RED = "\033[91m"
ANSI_MAGENTA = "\033[95m"
ANSI_BLUE = "\033[94m"
ANSI_BOLD = "\033[1m"
ANSI_RESET = "\033[0m"


from agents.event_bus import emit


class ClassroomLoopRunner:
    """
    Workflow runner for the Saarthi Continuous Classroom Loop.
    OBSERVE -> REASON -> DECIDE -> ACT -> MONITOR -> LEARN -> ADAPT

    CRITICAL BOUNDARIES:
    - Does NOT act as an intelligent agent.
    - Coordinates existing specialist agents and Orchestrator.
    - Orchestrator remains the SINGLE WRITER of shared classroom state (write_shared_state).
    - Generic across Grades 1-8 without hardcoded grade conditionals.
    """

    def __init__(self, session: ClassroomSession):
        self.session = session

    def print_banner(self, text: str):
        print("\n" + f"{ANSI_BOLD}{ANSI_CYAN}" + "=" * 70 + f"{ANSI_RESET}")
        print(f"{ANSI_BOLD}{ANSI_GREEN}{text}{ANSI_RESET}")
        print(f"{ANSI_BOLD}{ANSI_CYAN}" + "=" * 70 + f"{ANSI_RESET}")

    def start_session(self) -> CycleRecord:
        """
        Executes Cycle 1: Initial classroom session cycle.
        Runs Orchestrator candidate filtering, specialist pipeline, safety gate,
        conflict resolution, single state commit, and surfaces ONE next_action.
        """
        self.print_banner(f"SAARTHI CLASSROOM SESSION START — Session ID: {self.session.session_id}")
        self.session.status = "active"
        return self.run_cycle(trigger_type="initial")

    def run_cycle(
        self,
        trigger_type: str = "initial",
        override_signals: Optional[dict] = None
    ) -> CycleRecord:
        """
        Runs one iteration of the classroom loop.
        """
        if self.session.remaining_time_minutes <= 0:
            self.session.status = "ended"
            print(f"\n{ANSI_BOLD}{ANSI_RED}[Session End] Available session duration expired. No new cycles started.{ANSI_RESET}")
            rec = CycleRecord(
                cycle_number=self.session.current_cycle,
                trigger_type=trigger_type,
                active_evaluations=[],
                decision="END"
            )
            return rec

        self.session.current_cycle += 1
        cycle_num = self.session.current_cycle
        session_id = self.session.session_id

        emit(session_id, "ClassroomLoop", "cycle_start", payload={"cycle_number": cycle_num, "trigger_type": trigger_type, "active_grades": self.session.active_grades})

        print(f"\n{ANSI_BOLD}{ANSI_MAGENTA}--- SAARTHI CLASSROOM LOOP CYCLE {cycle_num} (Trigger: {trigger_type.upper()}) ---{ANSI_RESET}")

        signals = override_signals if override_signals is not None else self.session.latest_signals

        session_config = {
            "session_id": session_id,
            "active_grades": self.session.active_grades,
            "trigger_type": trigger_type,
            "is_initial_session": (trigger_type == "initial" or cycle_num == 1),
            "new_signals": signals,
            "session_info": {
                "duration_minutes": self.session.remaining_time_minutes,
                **self.session.classroom_resources
            },
            "session_constraints": self.session.session_constraints,
            "waiting_days": self.session.session_constraints.get("waiting_days", {}),
            **self.session.session_constraints
        }

        if isinstance(signals, dict):
            for k, v in signals.items():
                if k not in session_config:
                    session_config[k] = v

        # STEP 1: Candidate Filtering via get_active_grades (Cheap deterministic filter)
        active_filter = get_active_grades(session_config)
        active_evals = [item["grade_key"] for item in active_filter.get("active_evaluations", [])]
        skipped_evals = [item["grade_key"] for item in active_filter.get("skipped_grades", [])]

        emit(session_id, "ClassroomLoop", "candidate_filter", payload={"active_evaluations": active_evals, "skipped_grades": skipped_evals})

        print(f"\n{ANSI_BOLD}{ANSI_CYAN}[Candidate Filter]{ANSI_RESET} Active Candidate Grades ({len(active_evals)}): {ANSI_GREEN}{active_evals}{ANSI_RESET}")
        if skipped_evals:
            print(f"{ANSI_BOLD}{ANSI_CYAN}[Candidate Filter]{ANSI_RESET} Skipped Grades ({len(skipped_evals)}): {ANSI_YELLOW}{skipped_evals}{ANSI_RESET}")

        # STEP 2: Execute Orchestration Cycle (Specialist Agents run ONCE per candidate grade)
        print(f"\n{ANSI_BOLD}{ANSI_BLUE}[Executing Specialist Pipeline & Multi-Agent Orchestration]{ANSI_RESET}")
        orch_result: OrchestrationResult = run_orchestration_cycle(session_config)

        # Build Cycle Record
        cycle_record = CycleRecord(
            cycle_number=cycle_num,
            trigger_type=trigger_type,
            active_evaluations=active_evals,
            orchestration_result=orch_result.model_dump()
        )

        # STEP 3: Auto-Deliver generated activities for active grades
        evals = orch_result.specialist_evaluations or {}
        for sup in orch_result.state_updates:
            if sup.status == "reconciled" and sup.decided_topic and sup.recommended_resource:
                if sup.activity_status != "passed_safety_gate":
                    print(f"{ANSI_BOLD}{ANSI_RED}[Safety Gate Rejection] Activity for Grade {sup.grade} {sup.subject} (status='{sup.activity_status}') did not pass safety gate. Delivery skipped.{ANSI_RESET}")
                    continue

                act_design = None
                for ev_key, ev_val in evals.items():
                    if isinstance(ev_val, dict) and str(ev_val.get("grade")).strip() == str(sup.grade).strip():
                        act_design = ev_val.get("activity_design")
                        break

                if act_design and isinstance(act_design, dict) and act_design.get("content"):
                    delivered_content = act_design["content"]
                    est_time = act_design.get("estimated_time_minutes", min(12, self.session.remaining_time_minutes))
                else:
                    delivered_content = {
                        "instructions": f"Practice for {sup.decided_topic}",
                        "items": [f"Exercise for {sup.decided_topic}"]
                    }
                    est_time = min(12, self.session.remaining_time_minutes)

                act_id = f"act_{uuid.uuid4().hex[:6]}"
                del_act = DeliveredActivity(
                    activity_id=act_id,
                    grade=sup.grade,
                    subject=sup.subject,
                    topic=sup.decided_topic,
                    activity_type=sup.recommended_resource,
                    content=delivered_content,
                    estimated_time_minutes=est_time,
                    delivery_status="delivered",
                    delivered_at_cycle=cycle_num
                )
                self.session.delivered_activities.append(del_act)
                # Deduct time from session
                self.session.remaining_time_minutes = max(0, self.session.remaining_time_minutes - del_act.estimated_time_minutes)

        # Determine Cycle Decision
        if orch_result.next_action.priority == "critical":
            cycle_record.decision = "ESCALATE"
            self.session.status = "escalated"
        elif orch_result.next_action.priority in ["high", "medium"]:
            cycle_record.decision = "ADAPT"
            self.session.status = "adapting"
        else:
            cycle_record.decision = "CONTINUE"
            self.session.status = "active"

        self.session.cycle_history.append(cycle_record)
        next_action_payload = orch_result.next_action.model_dump() if hasattr(orch_result.next_action, "model_dump") else (orch_result.next_action.dict() if hasattr(orch_result.next_action, "dict") else orch_result.next_action)
        emit(session_id, "ClassroomLoop", "cycle_complete", payload={"cycle_number": cycle_num, "decision": cycle_record.decision, "next_action": next_action_payload})
        return cycle_record

    def process_new_signals(self, new_signals: dict) -> CycleRecord:
        """
        FEEDBACK LOOP: Receives new classroom evidence after activity delivery.
        Passes evidence to Progress Agent -> Orchestrator -> decides whether ADAPTATION is needed.
        """
        print("\n" + "=" * 50)
        print("NEW CLASSROOM SIGNALS RECEIVED AFTER ACTIVITY DELIVERY")
        print("=" * 50)
        print(json.dumps(new_signals, indent=2))

        self.session.latest_signals = new_signals

        # Orchestrator decides whether adaptation cycle is necessary based on signals
        return self.run_cycle(trigger_type="feedback", override_signals=new_signals)

    def update_classroom_resources(self, resource_updates: dict):
        """
        Updates physical/digital resource availability mid-session.
        Example: Internet drops, printer runs out of paper, tablets freed.
        """
        print(f"\n[Environment Update] Classroom Resource Conditions Changed: {resource_updates}")
        self.session.classroom_resources.update(resource_updates)

    def end_session(self) -> CycleRecord:
        """
        Ends the classroom session through the Orchestrator engine.
        Ensures state mutations route strictly via Orchestrator single-writer state tools.
        """
        print(f"\n[Session Termination] Ending session {self.session.session_id} via Orchestrator.")
        self.session.status = "ended"
        orch_result = run_orchestration_cycle({
            "session_id": self.session.session_id,
            "end_session": True,
            "active_grades": self.session.active_grades
        })
        cycle_rec = CycleRecord(
            cycle_number=self.session.current_cycle,
            trigger_type="end_session",
            active_evaluations=[],
            orchestration_result=orch_result.model_dump(),
            decision="END"
        )
        self.session.cycle_history.append(cycle_rec)
        return cycle_rec
