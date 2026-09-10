import unittest
import json
import uuid
from datetime import datetime, timezone

from tools.orchestrator_tools import read_shared_state, write_shared_state
from api import app
from fastapi.testclient import TestClient

client = TestClient(app)


class TestEndSession(unittest.TestCase):
    """
    Test suite for Saarthi End Session functionality.
    Verifies state mutations route through Single-Writer tools,
    preserve historical grade data, update session status to 'completed',
    and properly return error responses when session_id is missing.
    """

    def setUp(self):
        # Backup original shared state
        self.original_state = read_shared_state()

    def tearDown(self):
        # Restore original shared state
        write_shared_state(self.original_state)

    def test_end_session_missing_session_id_fails(self):
        """1. Asserts calling end-session without session_id returns HTTP 400."""
        response = client.post("/api/end-session", json={})
        self.assertEqual(response.status_code, 400)
        self.assertIn("session_id is required", response.json()["detail"])

    def test_end_session_updates_state_via_single_writer(self):
        """2. Asserts ending session updates active_session.status to completed via Orchestrator write_shared_state."""
        session_id = f"sess_test_{uuid.uuid4().hex[:6]}"

        response = client.post("/api/end-session", json={"session_id": session_id})
        self.assertEqual(response.status_code, 200)

        res_data = response.json()
        self.assertEqual(res_data["status"], "success")
        self.assertEqual(res_data["session_id"], session_id)
        self.assertIn("Session ended successfully", res_data["message"])

        # Read state back to verify single-writer state mutation
        state = read_shared_state()
        self.assertIn("active_session", state)
        self.assertEqual(state["active_session"]["session_id"], session_id)
        self.assertEqual(state["active_session"]["status"], "completed")
        self.assertIsNotNone(state["active_session"].get("ended_at"))

    def test_end_session_preserves_historical_classroom_data(self):
        """3. Asserts ending session preserves existing classroom history and grade evaluations."""
        session_id = f"sess_test_{uuid.uuid4().hex[:6]}"
        initial_state = read_shared_state()

        # Execute end session
        response = client.post("/api/end-session", json={"session_id": session_id})
        self.assertEqual(response.status_code, 200)

        updated_state = read_shared_state()

        # Verify historical data structures remain intact
        if "classrooms" in initial_state:
            self.assertEqual(len(updated_state.get("classrooms", [])), len(initial_state["classrooms"]))
        if "grades" in initial_state:
            self.assertEqual(len(updated_state.get("grades", {})), len(initial_state["grades"]))


if __name__ == "__main__":
    unittest.main()
