/**
 * saarthiApi.js
 * API Client service for connecting the Saarthi frontend to the FastAPI backend engine.
 */

const API_BASE_URL = import.meta.env.VITE_API_URL || '';

async function handleResponse(response) {
  if (!response.ok) {
    let errorDetail = 'API request failed';
    try {
      const errText = await response.text();
      try {
        const errJson = JSON.parse(errText);
        errorDetail = errJson.detail || errJson.message || errText;
      } catch (e) {
        if (errText) errorDetail = errText;
      }
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
export async function startSession(payload) {
  const res = await fetch(`${API_BASE_URL}/api/classroom/start`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
  if (!res.ok) {
    let errorDetail = `HTTP ${res.status}`;
    try {
      const errText = await res.text();
      try {
        const errJson = JSON.parse(errText);
        errorDetail = errJson.detail || errJson.message || errText;
      } catch (e) {
        if (errText) errorDetail = errText;
      }
    } catch (e) {}
    throw new Error(errorDetail);
  }
  return res.json();
}

export const startClassroomSession = startSession;

/**
 * Fetches current session state fallback from /api/session-state
 * GET /api/session-state
 */
export async function getSessionState() {
  const res = await fetch(`${API_BASE_URL}/api/session-state`);
  if (!res.ok) {
    throw new Error(`HTTP ${res.status}: ${res.statusText}`);
  }
  return res.json();
}

/**
 * Normalizes BOTH flat (data.cycle_record) and nested (data.shared_state.active_session.cycle_record)
 * backend shapes so field drift never causes blank UI screens.
 */
export function normalizeCycle(data) {
  if (!data) return null;

  const sharedState = data?.shared_state ?? {};
  const active = sharedState?.active_session ?? data?.active_session ?? {};
  const cycle = data?.cycle_record ?? active?.cycle_record ?? {};
  const orchestration = cycle?.orchestration_result ?? cycle;

  const sessionId = data?.session_id ?? active?.session_id ?? data?.sessionId;
  const status = data?.status ?? active?.status ?? 'active';
  const durationMinutes = data?.duration_minutes ?? active?.duration_minutes ?? 40;
  const gradeSelection = data?.grade_selection ?? active?.grade_selection ?? [];
  const resources = data?.resources ?? active?.resources ?? {};
  const currentSessionGrades = data?.current_session_grades ?? active?.current_session_grades ?? [];
  const deliveredActivities = data?.delivered_activities ?? active?.delivered_activities ?? cycle?.delivered_activities ?? [];

  return {
    sessionId,
    session_id: sessionId,
    status,
    duration_minutes: durationMinutes,
    durationMinutes,
    grade_selection: gradeSelection,
    resources,
    current_session_grades: currentSessionGrades,
    grades: currentSessionGrades,
    delivered_activities: deliveredActivities,
    activities: deliveredActivities,
    cycle_record: cycle,
    shared_state: sharedState,
    orchestration,
    next_action: cycle?.next_action ?? orchestration?.next_action,
    state_updates: cycle?.state_updates ?? orchestration?.state_updates ?? [],
    raw: data,
  };
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
 * POST /api/classroom/{session_id}/end
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
