import React, { useState, useEffect } from 'react';
import AppShell from './components/layout/AppShell';
import StartSessionCard from './components/session/StartSessionCard';
import StartSessionModal from './components/session/StartSessionModal';
import QuickStatusCard from './components/session/QuickStatusCard';
import QuickStatusModal from './components/session/QuickStatusModal';
import TodayAtAGlanceCard from './components/dashboard/TodayAtAGlanceCard';
import ActiveSessionView from './components/session/ActiveSessionView';
import AgentsWorkingScreen from './components/session/AgentsWorkingScreen';
import ActivityView from './components/activity/ActivityView';
import GovernmentSessionView, { OFFICIAL_GOVERNMENT_CATALOG } from './components/government/GovernmentSessionView';
import GradeBacklogView from './components/backlog/GradeBacklogView';
import AttendanceView from './components/attendance/AttendanceView';
import SettingsView from './components/settings/SettingsView';
import HelpSupportView from './components/help/HelpSupportView';
import { useTranslation } from './i18n/i18n';
import { CheckCircle2 } from 'lucide-react';
import { getClassroomSession, endClassroomSession, getSessionState, normalizeCycle } from './services/saarthiApi';

export default function App() {
  const { t } = useTranslation();
  const [activeTab, setActiveTab] = useState('dashboard');
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [isQuickStatusOpen, setIsQuickStatusOpen] = useState(false);
  const [pendingSessionPayload, setPendingSessionPayload] = useState(null);
  const [activeSession, setActiveSession] = useState(null);
  const [toastMessage, setToastMessage] = useState(null);
  const [isAttendanceSaved, setIsAttendanceSaved] = useState(false);

  // Government Sessions Frontend Selections State
  const [includedGovSessions, setIncludedGovSessions] = useState({});

  const [isRestoringSession, setIsRestoringSession] = useState(() => {
    return !!localStorage.getItem('saarthi_session_id');
  });

  // Restore active session from localStorage on startup/reload
  useEffect(() => {
    const restoreActiveSession = async () => {
      const storedSessionId = localStorage.getItem('saarthi_session_id');
      if (!storedSessionId) {
        setIsRestoringSession(false);
        return;
      }

      try {
        const data = await getClassroomSession(storedSessionId);
        if (data && (data.session_id || data.sessionId) && data.status !== 'completed') {
          setActiveSession(normalizeCycle(data));
        } else {
          localStorage.removeItem('saarthi_session_id');
          setActiveSession(null);
        }
      } catch (err) {
        console.warn('Could not restore session from localStorage:', err);
        localStorage.removeItem('saarthi_session_id');
        setActiveSession(null);
      } finally {
        setIsRestoringSession(false);
      }
    };

    restoreActiveSession();
  }, []);

  // Requirement 5: 5-second polling fallback to GET /api/session-state while a session is active
  useEffect(() => {
    if (!activeSession || (!activeSession.session_id && !activeSession.sessionId)) return;

    const interval = setInterval(async () => {
      try {
        const stateData = await getSessionState();
        if (stateData && (stateData.shared_state || stateData.active_session || stateData.cycle_record)) {
          const normalized = normalizeCycle(stateData);
          if (normalized && (normalized.session_id || normalized.sessionId)) {
            setActiveSession((prev) => ({
              ...prev,
              ...normalized,
              // Retain active grades/selection if backend polling shared_state lacks explicit grade_selection array
              grade_selection: (normalized.grade_selection && normalized.grade_selection.length > 0)
                ? normalized.grade_selection
                : (prev?.grade_selection || []),
            }));
          }
        }
      } catch (err) {
        console.warn('5s session state polling fallback error:', err);
      }
    }, 5000);

    return () => clearInterval(interval);
  }, [activeSession?.session_id, activeSession?.sessionId]);

  // Dynamic Teacher Profile Info
  const teacherName = 'Sarah Jenkins';
  const teacherFirstName = teacherName.split(' ')[0] || 'Sarah';

  const showToast = (message) => {
    setToastMessage(message);
    setTimeout(() => {
      setToastMessage(null);
    }, 4500);
  };

  const handleUpdateGovInclusion = (sessionId, selectedGrades) => {
    setIncludedGovSessions((prev) => ({
      ...prev,
      [sessionId]: selectedGrades,
    }));
  };

  // Called when StartSessionModal submits valid form data
  const handleStartSessionSubmit = (sessionPayload) => {
    setIsModalOpen(false);
    setPendingSessionPayload(sessionPayload);
    setActiveTab('dashboard');
  };

  // Called when AgentsWorkingScreen finishes real backend session creation
  const handleTransitionComplete = (createdSessionData) => {
    const normalized = normalizeCycle(createdSessionData);
    if (normalized && (normalized.session_id || normalized.sessionId)) {
      const sessId = normalized.session_id || normalized.sessionId;
      localStorage.setItem('saarthi_session_id', sessId);
      setActiveSession(normalized);
    } else {
      const fallbackId = `sess_${Math.random().toString(36).substring(2, 10)}`;
      localStorage.setItem('saarthi_session_id', fallbackId);
      setActiveSession({
        session_id: fallbackId,
        sessionId: fallbackId,
        status: 'active',
        started_at: Date.now(),
        duration_minutes: createdSessionData?.duration_minutes || 45,
        grade_selection: createdSessionData?.grade_selection || [],
        resources: createdSessionData?.resources || {},
        cycle_record: createdSessionData?.cycle_record || {},
        delivered_activities: createdSessionData?.delivered_activities || [],
      });
    }
    setPendingSessionPayload(null);
  };

  const handleEndSessionSubmit = async (sessionId) => {
    localStorage.removeItem('saarthi_session_id');
    if (sessionId && typeof sessionId === 'string') {
      try {
        await endClassroomSession(sessionId);
      } catch (err) {
        console.warn('Backend end session failed or already ended:', err);
      }
    }
    setActiveSession(null);
    showToast(t('session.ended_toast_desc'));
  };

  return (
    <AppShell activeTab={activeTab} onTabChange={setActiveTab}>
      <div className="max-w-5xl space-y-6 relative">
        {/* TOAST NOTIFICATION */}
        {toastMessage && (
          <div className="fixed bottom-6 right-6 z-50 liquid-glass-card rounded-2xl px-4 py-3 shadow-xl border border-emerald-500/30 flex items-center gap-3 animate-fade-in">
            <CheckCircle2 className="w-5 h-5 text-emerald-500 shrink-0" />
            <div>
              <div className="text-xs font-semibold text-[#0A0A0A] dark:text-[#F5F5F5]">
                {t('session.ended_toast')}
              </div>
              <div className="text-[11px] text-[#6E6E6E] dark:text-[#A3A3A3]">
                {toastMessage}
              </div>
            </div>
          </div>
        )}

        {/* TAB VIEW ROUTING */}
        {isRestoringSession ? (
          <div className="flex items-center justify-center py-20">
            <div className="liquid-glass-card rounded-2xl p-6 text-center space-y-3 border border-black/10 dark:border-white/10">
              <div className="w-6 h-6 rounded-full border-2 border-orange-500 border-t-transparent animate-spin mx-auto" />
              <div className="text-xs font-medium text-[#6E6E6E] dark:text-[#A3A3A3]">
                Restoring active classroom session...
              </div>
            </div>
          </div>
        ) : activeTab === 'activity' ? (
          <ActivityView
            activeSession={activeSession}
            onStartSession={() => {
              setActiveTab('dashboard');
              setIsModalOpen(true);
            }}
          />
        ) : activeTab === 'government_session' ? (
          <GovernmentSessionView
            includedSessions={includedGovSessions}
            onUpdateInclusion={handleUpdateGovInclusion}
            isSessionActive={!!activeSession}
          />
        ) : activeTab === 'grade_backlog' ? (
          <GradeBacklogView activeSession={activeSession} sharedState={activeSession?.shared_state} />
        ) : activeTab === 'attendance' ? (
          <AttendanceView activeSession={activeSession} sharedState={activeSession?.shared_state} onSaveAttendance={() => setIsAttendanceSaved(true)} />
        ) : activeTab === 'settings' ? (
          <SettingsView />
        ) : activeTab === 'help' ? (
          <HelpSupportView onNavigate={setActiveTab} />
        ) : pendingSessionPayload ? (
          <AgentsWorkingScreen
            sessionPayload={pendingSessionPayload}
            onComplete={handleTransitionComplete}
          />
        ) : activeSession ? (
          <div className="space-y-6">
            <QuickStatusCard
              activeSession={activeSession}
              onOpenStatusModal={() => setIsQuickStatusOpen(true)}
            />
            <ActiveSessionView
              session={activeSession}
              onEndSession={handleEndSessionSubmit}
              onUpdateSession={(updatedSession) => setActiveSession(updatedSession)}
            />
          </div>
        ) : (
          <div className="space-y-6">
            {/* COMPACT DASHBOARD WELCOME SECTION */}
            <div className="space-y-1">
              <h2 className="text-xl sm:text-2xl font-bold tracking-tight text-[#0A0A0A] dark:text-[#F5F5F5] font-heading">
                Hello, {teacherFirstName} 👋
              </h2>
              <p className="text-xs sm:text-sm text-[#6E6E6E] dark:text-[#A3A3A3]">
                Your intelligent classroom copilot for planning, coordinating, and adapting learning across every grade.
              </p>
            </div>

            {/* FIRST CONTENT CARD ON DASHBOARD */}
            <StartSessionCard onOpenModal={() => setIsModalOpen(true)} />

            {/* SECONDARY CARD ON DASHBOARD WHEN NO ACTIVE SESSION */}
            <TodayAtAGlanceCard
              includedGovSessions={includedGovSessions}
              plannedGradesCount={activeSession?.grade_selection?.length || 0}
              isAttendanceSaved={isAttendanceSaved}
              onNavigateToAttendance={() => setActiveTab('attendance')}
            />
          </div>
        )}

        {/* MODAL SHEET FOR START SESSION */}
        <StartSessionModal
          isOpen={isModalOpen}
          onClose={() => setIsModalOpen(false)}
          onStartSession={handleStartSessionSubmit}
          includedGovSessions={includedGovSessions}
          onNavigateToGovSessions={() => {
            setIsModalOpen(false);
            setActiveTab('government_session');
          }}
        />

        {/* MODAL OVERLAY FOR QUICK CLASSROOM STATUS */}
        <QuickStatusModal
          isOpen={isQuickStatusOpen}
          onClose={() => setIsQuickStatusOpen(false)}
          activeSession={activeSession}
        />
      </div>
    </AppShell>
  );
}


