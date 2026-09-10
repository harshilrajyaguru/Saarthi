import sys
import os
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from api import app, SESSIONS, parse_teacher_input
from tools.orchestrator_tools import read_shared_state

class TestSaarthiAPI(unittest.TestCase):

    def setUp(self):
        self.client = TestClient(app)

    def test_health_check(self):
        """Verify health check endpoint returns status ok."""
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "ok")
        self.assertEqual(data["service"], "Saarthi API")

    def test_invalid_teacher_inputs(self):
        """Verify that invalid inputs return HTTP 400 with meaningful error messages."""
        # Missing grades
        res1 = self.client.post("/api/classroom/start", json={"duration_minutes": 40})
        self.assertEqual(res1.status_code, 400)
        self.assertIn("At least one grade must be provided", res1.json()["detail"])

        # Invalid session duration
        res2 = self.client.post("/api/classroom/start", json={"grades": ["3"], "session_minutes": 0})
        self.assertEqual(res2.status_code, 400)
        self.assertIn("session_minutes must be greater than 0", res2.json()["detail"])

    def test_parse_teacher_input_flexible_formats(self):
        """Verify parse_teacher_input helper correctly normalizes arbitrary teacher input."""
        # Dict format
        active_grades, subjs, dur, res, con = parse_teacher_input({
            "grades": [{"grade": "5", "subject": "Science"}, {"grade": "6", "subject": "Math"}],
            "session_minutes": 50,
            "resources": {"tablets": 4, "tv": True},
            "connectivity": "online"
        })
        self.assertEqual(active_grades, ["Grade_5_Science", "Grade_6_Math"])
        self.assertEqual(subjs, ["Science", "Math"])
        self.assertEqual(dur, 50)
        self.assertEqual(res["tablets"], 4)

        # String format
        active_grades_2, subjs_2, dur_2, _, _ = parse_teacher_input({
            "grades": ["3", "4"],
            "subjects": ["Math", "Math"],
            "duration_minutes": 30
        })
        self.assertEqual(active_grades_2, ["Grade_3_Math", "Grade_4_Math"])
        self.assertEqual(dur_2, 30)

    def test_unknown_session_not_found(self):
        """Verify that requesting or posting to non-existent session IDs returns HTTP 404."""
        res = self.client.get("/api/classroom/sess_nonexistent")
        self.assertEqual(res.status_code, 404)

        res_sig = self.client.post(
            "/api/classroom/sess_nonexistent/signals",
            json={"grade": "3", "signal": "Struggling with fractions"}
        )
        self.assertEqual(res_sig.status_code, 404)

    def test_invalid_signal_payload(self):
        """Verify submitting signal with missing required fields returns HTTP 400."""
        # Create a session first
        start_res = self.client.post("/api/classroom/start", json={
            "grades": [{"grade": "3", "subject": "Math"}],
            "session_minutes": 40
        })
        self.assertEqual(start_res.status_code, 200)
        session_id = start_res.json()["session_id"]

        # Submit signal missing text/signal
        sig_res = self.client.post(f"/api/classroom/{session_id}/signals", json={"grade": "3"})
        self.assertEqual(sig_res.status_code, 400)
        self.assertIn("must include 'grade' and 'signal'", sig_res.json()["detail"])

    def test_full_classroom_session_and_adaptive_signal_flow(self):
        """
        End-to-end sanity test for session lifecycle:
        1. Start classroom session with complex arbitrary teacher input
        2. Verify specialist agent outputs (Progress, Curriculum, Resource, Activity, Safety)
        3. Retrieve session state
        4. Submit mid-session student signal to trigger adaptive reasoning cycle
        5. Trigger manual run cycle
        6. End session via single-writer Orchestrator routing
        """
        teacher_input = {
            "grades": ["3", "5"],
            "subjects": ["Math"],
            "session_minutes": 80,
            "resources": {
                "tablets": 2,
                "tv": 1,
                "printer": True
            },
            "connectivity": "offline",
            "teacher_constraints": [
                "Grade 5 has an exam tomorrow"
            ],
            "notes": "Grade 3 is struggling with fractions"
        }

        # 1. Start Session
        start_response = self.client.post("/api/classroom/start", json=teacher_input)
        self.assertEqual(start_response.status_code, 200)
        start_data = start_response.json()

        session_id = start_data["session_id"]
        self.assertTrue(session_id.startswith("sess_"))
        self.assertIn(start_data["status"], ["active", "adapting", "escalated"])
        self.assertIn("cycle_record", start_data)
        self.assertIn("next_action", start_data["cycle_record"])
        self.assertEqual(len(start_data["active_grades"]), 2)

        # 2. Verify Specialist Agent Outputs Contract
        spec_evals = start_data["cycle_record"].get("specialist_evaluations", {})
        self.assertIsNotNone(spec_evals)
        self.assertIn("Grade_3_Math", spec_evals)
        g3_eval = spec_evals["Grade_3_Math"]
        self.assertIn("progress_diag", g3_eval)
        self.assertIn("curriculum_dec", g3_eval)
        self.assertIn("resource_rec", g3_eval)
        self.assertIn("activity_design", g3_eval)
        self.assertIn("safety_verdict", g3_eval)

        # 3. Get Session State
        get_response = self.client.get(f"/api/classroom/{session_id}")
        self.assertEqual(get_response.status_code, 200)
        get_data = get_response.json()
        self.assertEqual(get_data["session_id"], session_id)
        self.assertGreaterEqual(get_data["current_cycle"], 1)

        # 4. Submit Student Signal for Grade 5
        signal_payload = {
            "grade": "5",
            "subject": "Math",
            "signal_type": "student_progress",
            "signal": "Students are struggling with equivalent fractions numerator scaling",
            "score": 0.3
        }
        sig_response = self.client.post(f"/api/classroom/{session_id}/signals", json=signal_payload)
        self.assertEqual(sig_response.status_code, 200)
        sig_data = sig_response.json()
        self.assertEqual(sig_data["current_cycle"], 2)
        self.assertIn("cycle_record", sig_data)

        # 5. Trigger Manual Run
        run_response = self.client.post(f"/api/classroom/{session_id}/run", json={"trigger_type": "manual"})
        self.assertEqual(run_response.status_code, 200)
        run_data = run_response.json()
        self.assertEqual(run_data["current_cycle"], 3)

        # 6. End Session via Single-Writer Orchestrator Routing
        end_response = self.client.post(f"/api/classroom/{session_id}/end")
        self.assertEqual(end_response.status_code, 200)
        end_data = end_response.json()
        self.assertEqual(end_data["status"], "success")

        # 7. Shared State check
        shared_state = read_shared_state()
        self.assertTrue("grades" in shared_state or "classrooms" in shared_state or "active_session" in shared_state)
        if "active_session" in shared_state:
            self.assertEqual(shared_state["active_session"]["session_id"], session_id)
            self.assertEqual(shared_state["active_session"]["status"], "completed")

if __name__ == "__main__":
    unittest.main()
