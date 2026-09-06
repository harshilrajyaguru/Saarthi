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
        return parts[1], "_".join(parts[2:])
    elif len(parts) == 2 and parts[0] == "Grade":
        return parts[1], "Math"
    clean = grade_key.replace("Grade", "").strip()
    return clean if clean else "3", "Math"


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
        print("\n" + "=" * 70)
        print(text)
        print("=" * 70)

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
            print("\n[Session End] Available session duration expired. No new cycles started.")
            rec = CycleRecord(
                cycle_number=self.session.current_cycle,
                trigger_type=trigger_type,
                active_evaluations=[],
                decision="END"
            )
            return rec

        self.session.current_cycle += 1
        cycle_num = self.session.current_cycle

        print(f"\n--- CLASSROOM LOOP CYCLE {cycle_num} (Trigger: {trigger_type.upper()}) ---")

        signals = override_signals if override_signals is not None else self.session.latest_signals

        session_config = {
            "session_id": self.session.session_id,
            "active_grades": self.session.active_grades,
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

        print(f"[Candidate Filter] Candidate Grades Requiring Evaluation ({len(active_evals)}): {active_evals}")
        print(f"[Candidate Filter] Skipped Grades ({len(skipped_evals)}): {skipped_evals}")

        # STEP 2: Execute Orchestration Cycle (Specialist Agents run ONCE per candidate grade)
        print("\n[Executing Specialist Pipeline & Orchestration Reconciliation]")
        orch_result: OrchestrationResult = run_orchestration_cycle(session_config)

        # Build Cycle Record
        cycle_record = CycleRecord(
            cycle_number=cycle_num,
            trigger_type=trigger_type,
            active_evaluations=active_evals,
            orchestration_result=orch_result.model_dump()
        )

        print("\n[PASSED] Orchestrator Prioritized Next Action:")
        print(json.dumps(orch_result.next_action.model_dump(), indent=2))

        if orch_result.next_action.resolved_conflicts:
            print("\n[PASSED] Cross-Grade Conflicts Resolved:")
            for c_msg in orch_result.next_action.resolved_conflicts:
                print(f"  - {c_msg}")

        print("\n[PASSED] State Updates Committed to Shared Store (Single Writer):")
        for sup in orch_result.state_updates:
            print(f"  - Grade {sup.grade} {sup.subject}: status='{sup.status}', topic='{sup.decided_topic}', resource='{sup.recommended_resource}', activity_status='{sup.activity_status}'")

        # STEP 3: Auto-Deliver generated activities for active grades
        for sup in orch_result.state_updates:
            if sup.status == "reconciled" and sup.decided_topic and sup.recommended_resource:
                act_id = f"act_{uuid.uuid4().hex[:6]}"
                del_act = DeliveredActivity(
                    activity_id=act_id,
                    grade=sup.grade,
                    subject=sup.subject,
                    topic=sup.decided_topic,
                    activity_type=sup.recommended_resource,
                    content={"instructions": f"Practice for {sup.decided_topic}", "items": [f"Exercise for {sup.decided_topic}"]},
                    estimated_time_minutes=min(12, self.session.remaining_time_minutes),
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
