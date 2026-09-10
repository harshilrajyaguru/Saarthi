/**
 * saarthiApi.js
 * API Client service for connecting the Saarthi frontend to the FastAPI backend engine.
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || '';

async function handleResponse(response) {
  if (!response.ok) {
    let errorDetail = 'API request failed';
    try {
      const errJson = await response.json();
      errorDetail = errJson.detail || errJson.message || JSON.stringify(errJson);
    } catch (e) {
      errorDetail = `HTTP ${response.status}: ${response.statusText}`;
    }
    throw new Error(errorDetail);
  }
  return await response.json();
}

/**
 * Starts a real classroom session and runs cold-start agent cycle.
 * POST /api/classroom/start
 */
export async function startClassroomSession(payload) {
  const res = await fetch(`${API_BASE_URL}/api/classroom/start`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  return handleResponse(res);
}

/**
 * Fetches current real session state by session ID.
 * GET /api/classroom/{session_id}
 */
export async function getClassroomSession(sessionId) {
  const res = await fetch(`${API_BASE_URL}/api/classroom/${sessionId}`);
  return handleResponse(res);
}

/**
 * Submits a mid-session classroom or student signal to trigger adaptive cycle.
 * POST /api/classroom/{session_id}/signals
 */
export async function submitClassroomSignal(sessionId, signalData) {
  const res = await fetch(`${API_BASE_URL}/api/classroom/${sessionId}/signals`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(signalData),
  });
  return handleResponse(res);
}

/**
 * Manually triggers an orchestration cycle for an active session.
 * POST /api/classroom/{session_id}/run
 */
export async function runClassroomCycle(sessionId, options = {}) {
  const res = await fetch(`${API_BASE_URL}/api/classroom/${sessionId}/run`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(options),
  });
  return handleResponse(res);
}

/**
 * Ends active classroom session via Orchestrator state transition.
 * POST /api/classroom/{session_id}/end or POST /api/end-session
 */
export async function endClassroomSession(sessionId) {
  const res = await fetch(`${API_BASE_URL}/api/classroom/${sessionId}/end`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ session_id: sessionId }),
  });
  return handleResponse(res);
}

/**
 * Reads ground-truth shared classroom state.
 * GET /api/classroom/state
 */
export async function getClassroomState() {
  const res = await fetch(`${API_BASE_URL}/api/classroom/state`);
  return handleResponse(res);
}
