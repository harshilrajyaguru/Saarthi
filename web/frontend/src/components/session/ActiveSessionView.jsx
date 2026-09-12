import React, { useState } from 'react';
import { Sparkles, ChevronDown, ChevronUp, AlertCircle, CheckCircle2, BookOpen, Clock, Loader2, LogOut, Send, MessageSquare } from 'lucide-react';
import { useTranslation } from '../../i18n/i18n';
import { submitClassroomSignal, endClassroomSession } from '../../services/saarthiApi';

export default function ActiveSessionView({ session, onEndSession, onUpdateSession }) {
  const { t } = useTranslation();
  const [isSummaryExpanded, setIsSummaryExpanded] = useState(false);
  const [isConfirmDialogOpen, setIsConfirmDialogOpen] = useState(false);
  const [isEnding, setIsEnding] = useState(false);
  const [endErrorMessage, setEndErrorMessage] = useState(null);

  // Derived grade selection with fallback to current_session_grades
  const effectiveGradeSelection = (session?.grade_selection && session.grade_selection.length > 0)
    ? session.grade_selection
    : (session?.current_session_grades?.map(item => ({
        grade: String(item.grade),
        subject: item.subject
      })) || []);

  // Adaptive Signal Form State
  const gradeSelectionList = effectiveGradeSelection;
  const [signalGrade, setSignalGrade] = useState(gradeSelectionList[0]?.grade || '3');
  const [signalText, setSignalText] = useState('');
  const [isSubmittingSignal, setIsSubmittingSignal] = useState(false);
  const [signalSuccessMsg, setSignalSuccessMsg] = useState(null);
  const [signalErrorMsg, setSignalErrorMsg] = useState(null);

  if (!session) return null;

  const {
    session_id,
    duration_minutes,
    grade_selection = effectiveGradeSelection,
    resources = {},
    cycle_record = {},
    shared_state = {},
    delivered_activities = [],
    current_session_grades = null,
  } = session;

  const nextAction = cycle_record.next_action || {
    priority: 'high',
    grade: '5',
    subject: 'Math',
    action_type: 'normal_progression',
    reason: 'Initial session cycle completed successfully.',
    resolved_conflicts: [],
  };

  const stateUpdates = cycle_record.state_updates || [];

  // Helper to normalize subject
  const normSubj = (s) => {
    if (!s) return 'Math';
    const clean = String(s).trim();
    if (['mathematics', 'maths', 'math'].includes(clean.toLowerCase())) return 'Math';
    return clean.charAt(0).toUpperCase() + clean.slice(1);
  };

  // Derive explicit list of current session grades to render (excluding unrequested historical grades)
  const sessionGradeCards = current_session_grades && current_session_grades.length > 0
    ? current_session_grades.map((item) => {
        const gk = item.grade_key || `Grade_${item.grade}_${normSubj(item.subject)}`;
        const govSess = (grade_selection.find((g) => String(g.grade) === String(item.grade)) || {}).gov_session;
        return {
          ...item,
          gov_session: govSess || item.gov_session || null,
          delivered_activity: item.delivered_activity || delivered_activities.find((a) => {
            const actGk = `Grade_${a.grade}_${normSubj(a.subject)}`;
            return actGk === gk;
          })
        };
      })
    : (grade_selection.length > 0 ? grade_selection.map((g) => {
        const gk = `Grade_${g.grade}_${normSubj(g.subject || 'Math')}`;
        const supMatch = stateUpdates.find((sup) => {
          const supGk = `Grade_${sup.grade}_${normSubj(sup.subject)}`;
          return supGk === gk;
        });
        const delAct = delivered_activities.find((a) => {
          const actGk = `Grade_${a.grade}_${normSubj(a.subject)}`;
          return actGk === gk;
        });
        return {
          grade: String(g.grade),
          subject: normSubj(g.subject || 'Math'),
          grade_key: gk,
          status: supMatch?.status || 'reconciled',
          decided_topic: supMatch?.decided_topic || null,
          recommended_resource: supMatch?.recommended_resource || null,
          activity_status: supMatch?.activity_status || 'passed_safety_gate',
          gov_session: g.gov_session || null,
          delivered_activity: delAct || null
        };
      }) : []);

  const getPriorityStyle = (priority) => {
    switch (priority) {
      case 'critical':
        return 'bg-red-500/15 border-red-500/30 text-red-600 dark:text-red-400';
      case 'high':
        return 'bg-amber-500/15 border-amber-500/30 text-amber-600 dark:text-amber-400';
      case 'medium':
        return 'bg-blue-500/15 border-blue-500/30 text-blue-600 dark:text-blue-400';
      default:
        return 'bg-black/10 dark:bg-white/10 text-[#6E6E6E] dark:text-[#A3A3A3]';
    }
  };

  const handleSendSignal = async (e) => {
    e.preventDefault();
    if (!signalText.trim() || isSubmittingSignal) return;
    setIsSubmittingSignal(true);
    setSignalErrorMsg(null);
    setSignalSuccessMsg(null);

    try {
      const res = await submitClassroomSignal(session_id, {
        grade: signalGrade,
        subject: 'Math',
        signal_type: 'student_progress',
        signal: signalText.trim(),
      });
      setIsSubmittingSignal(false);
      setSignalText('');
      setSignalSuccessMsg(`Saarthi reasoned on new feedback for Grade ${signalGrade} and updated the plan.`);
      if (onUpdateSession) {
        onUpdateSession({
          ...session,
          ...res,
          cycle_record: res.cycle_record || res,
          delivered_activities: res.delivered_activities || session.delivered_activities,
          shared_state: res.shared_state || session.shared_state,
        });
      }
      setTimeout(() => setSignalSuccessMsg(null), 5000);
    } catch (err) {
      console.error('Failed to submit adaptive signal:', err);
      setIsSubmittingSignal(false);
      setSignalErrorMsg(err.message || 'Failed to submit classroom signal.');
    }
  };

  const handleConfirmEndSession = async () => {
    setIsEnding(true);
    setEndErrorMessage(null);
    try {
      if (onEndSession) {
        await onEndSession(session_id);
      } else {
        await endClassroomSession(session_id);
      }
      setIsEnding(false);
      setIsConfirmDialogOpen(false);
    } catch (err) {
      console.error('Failed to end session:', err);
      setIsEnding(false);
      setEndErrorMessage(err.message || t('session.end_error'));
    }
  };

  return (
    <div className="space-y-6 relative">
      {/* 1. COLLAPSED ACTIVE SESSION SUMMARY BAR */}
      <div className="liquid-glass-card rounded-[20px] p-4 transition-all duration-300">
        <div className="flex items-center justify-between gap-4">
          <div className="flex items-center gap-3 flex-wrap">
            {/* Active Status Badge */}
            <div className="inline-flex items-center gap-2 px-3 py-1 rounded-full bg-emerald-500/15 border border-emerald-500/30 text-emerald-600 dark:text-emerald-400 text-xs font-semibold">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
              <span>{t('session.active_banner')}</span>
            </div>

            {/* Concise Summary */}
            <div className="text-xs font-semibold text-[#0A0A0A] dark:text-[#F5F5F5]">
              {grade_selection.map((g) => `Grade ${g.grade} (${g.subject})`).join(' · ')}
            </div>

            <div className="text-xs text-[#6E6E6E] dark:text-[#A3A3A3] flex items-center gap-1">
              <Clock className="w-3.5 h-3.5 inline" />
              <span>{duration_minutes} min</span>
            </div>
          </div>

          {/* Action Buttons: Expand + Subtle Secondary End Session */}
          <div className="flex items-center gap-2 shrink-0">
            <button
              type="button"
              onClick={() => setIsSummaryExpanded((prev) => !prev)}
              className="liquid-glass-btn-secondary px-3 py-1.5 rounded-xl text-xs font-medium inline-flex items-center gap-1 cursor-pointer"
            >
              <span>{isSummaryExpanded ? t('session.collapse') : t('session.expand')}</span>
              {isSummaryExpanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
            </button>

            <button
              type="button"
              onClick={() => setIsConfirmDialogOpen(true)}
              className="liquid-glass-btn-secondary px-3 py-1.5 rounded-xl text-xs font-medium text-red-600 dark:text-red-400 hover:bg-red-500/10 hover:border-red-500/30 transition-all cursor-pointer inline-flex items-center gap-1"
            >
              <LogOut className="w-3.5 h-3.5" />
              <span>{t('session.end_btn')}</span>
            </button>
          </div>
        </div>

        {/* Expanded Summary Details */}
        {isSummaryExpanded && (
          <div className="mt-4 pt-4 border-t border-black/[0.05] dark:border-white/[0.08] text-xs space-y-4 text-[#6E6E6E] dark:text-[#A3A3A3]">
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
              <div>
                <span className="font-semibold text-[#0A0A0A] dark:text-[#F5F5F5]">Session ID: </span>
                <span>{session_id}</span>
              </div>
              <div>
                <span className="font-semibold text-[#0A0A0A] dark:text-[#F5F5F5]">Active Grades: </span>
                <span>{grade_selection.length} grades</span>
              </div>
              <div>
                <span className="font-semibold text-[#0A0A0A] dark:text-[#F5F5F5]">Resources: </span>
                <span>
                  {resources.tablets || 0} tablets · {resources.tv ? 'TV' : 'No TV'} ·{' '}
                  {resources.printer ? 'Printer' : 'No Printer'} ·{' '}
                  {resources.internet ? 'Online' : 'Offline'}
                </span>
              </div>
            </div>

            {/* Actions inside Expanded Summary */}
            <div className="flex items-center justify-end gap-2.5 pt-2">
              <button
                type="button"
                onClick={() => setIsSummaryExpanded(false)}
                className="liquid-glass-btn-secondary px-3.5 py-1.5 rounded-xl text-xs font-medium cursor-pointer"
              >
                {t('session.continue_btn')}
              </button>
              <button
                type="button"
                onClick={() => setIsConfirmDialogOpen(true)}
                className="liquid-glass-btn-secondary px-3.5 py-1.5 rounded-xl text-xs font-medium text-red-600 dark:text-red-400 hover:bg-red-500/10 cursor-pointer"
              >
                {t('session.end_btn')}
              </button>
            </div>
          </div>
        )}
      </div>

      {/* 2. PRIORITIZED NEXT ACTION CARD (FROM ORCHESTRATOR) */}
      <div className="liquid-glass-card rounded-[24px] p-6 space-y-4 border-l-4 border-l-amber-500">
        <div className="flex items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <span className="text-[11px] font-semibold tracking-wider uppercase text-[#6E6E6E] dark:text-[#A3A3A3] flex items-center gap-1.5">
              <Sparkles className="w-3.5 h-3.5 text-amber-500" />
              {t('session.next_action')}
            </span>
          </div>

          <span
            className={`px-3 py-1 rounded-full text-xs font-semibold border uppercase tracking-wider ${getPriorityStyle(
              nextAction.priority
            )}`}
          >
            {nextAction.priority} Priority
          </span>
        </div>

        <div className="space-y-2">
          <h3 className="text-xl font-semibold tracking-tight text-[#0A0A0A] dark:text-[#F5F5F5]">
            Grade {nextAction.grade} {nextAction.subject} — {nextAction.action_type.replace(/_/g, ' ')}
          </h3>
          <p className="text-xs text-[#6E6E6E] dark:text-[#A3A3A3] leading-relaxed">
            {nextAction.reason}
          </p>
        </div>

        {/* Resolved Conflicts Log */}
        {nextAction.resolved_conflicts && nextAction.resolved_conflicts.length > 0 && (
          <div className="p-3 rounded-xl bg-black/[0.03] dark:bg-white/[0.03] text-xs space-y-1">
            <div className="font-semibold text-[#0A0A0A] dark:text-[#F5F5F5]">Cross-Grade Conflicts Resolved:</div>
            {nextAction.resolved_conflicts.map((conf, i) => (
              <div key={i} className="text-[#6E6E6E] dark:text-[#A3A3A3] flex items-center gap-1.5">
                <CheckCircle2 className="w-3.5 h-3.5 text-emerald-500 shrink-0" />
                <span>{conf}</span>
              </div>
            ))}
          </div>
        )}
      </div>

      {/* 3. PER-GRADE ACTION & ACTIVITY CARDS */}
      <div className="space-y-4">
        <h3 className="text-base font-semibold text-[#0A0A0A] dark:text-[#F5F5F5]">
          Active Grade Plans & Delivered Activities
        </h3>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {sessionGradeCards.map((sup, idx) => {
            const delAct = sup.delivered_activity;
            const govSess = sup.gov_session;

            const specEvals = cycle_record?.specialist_evaluations || {};
            const gk = sup.grade_key || `Grade_${sup.grade}_${normSubj(sup.subject)}`;
            let specEval = specEvals[gk];
            if (!specEval) {
              const matchedKey = Object.keys(specEvals).find((k) => {
                const ev = specEvals[k];
                return String(ev?.grade) === String(sup.grade) || k.includes(`_${sup.grade}_`) || k.includes(`Grade_${sup.grade}`);
              });
              specEval = matchedKey ? specEvals[matchedKey] : null;
            }

            const pDiag = specEval?.progress_diag;
            const cDec = specEval?.curriculum_dec;
            const rRec = specEval?.resource_rec;
            const aDes = specEval?.activity_design;
            const sVerd = specEval?.safety_verdict;
            const gradesState = shared_state?.grades || {};
            const gData = gradesState[gk] || gradesState[String(sup.grade)] || gradesState[`Grade_${sup.grade}_Math`] || {};
            const rosterSize = gData?.roster_size ?? '—';
            const hist = gData?.history || [];
            const lastSess = hist.length > 0 ? hist[hist.length - 1] : null;
            const avgCorrPct = lastSess?.avg_correctness != null ? Math.round(lastSess.avg_correctness * 100) : '—';
            const below60Count = lastSess?.below_60_count ?? '—';

            const aggErrs = {};
            hist.forEach((s) => {
              if (s.error_tags && typeof s.error_tags === 'object') {
                Object.entries(s.error_tags).forEach(([k, v]) => {
                  aggErrs[k] = (aggErrs[k] || 0) + (typeof v === 'number' ? v : 1);
                });
              }
            });
            const topErrEntries = Object.entries(aggErrs).sort((a, b) => b[1] - a[1]).slice(0, 3);
            const tabletsAvail = gData?.resources?.tablets ?? '—';
            const tabletsInsuff = typeof tabletsAvail === 'number' && typeof rosterSize === 'number' && tabletsAvail < rosterSize;

            return (
              <div
                key={idx}
                className={`liquid-glass-card rounded-[20px] p-5 space-y-3.5 flex flex-col justify-between ${
                  govSess ? 'border-emerald-500/30 bg-emerald-500/[0.02] dark:bg-emerald-500/[0.03]' : ''
                }`}
              >
                <div className="space-y-2">
                  <div className="flex items-center justify-between gap-2">
                    <span className="text-sm font-semibold text-[#0A0A0A] dark:text-[#F5F5F5]">
                      Grade {sup.grade} · {sup.subject}
                    </span>
                    {govSess ? (
                      <span className="px-2.5 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-500/20 text-emerald-700 dark:text-emerald-300 uppercase">
                        Gov Session
                      </span>
                    ) : (
                      <span className="px-2.5 py-0.5 rounded-full text-[10px] font-semibold bg-black/5 dark:bg-white/10 text-[#6E6E6E] dark:text-[#A3A3A3] uppercase">
                        {sup.status}
                      </span>
                    )}
                  </div>

                  <div className="space-y-1.5 text-xs">
                    {/* 👥 Roster row */}
                    <div className="flex items-center justify-between text-[#6E6E6E] dark:text-[#A3A3A3]">
                      <span>👥 Roster:</span>
                      <span className="font-semibold text-[#0A0A0A] dark:text-[#F5F5F5]">
                        {rosterSize !== '—' ? `${rosterSize} students` : '—'}
                      </span>
                    </div>

                    {/* 📊 Last session row */}
                    <div className="flex items-center justify-between text-[#6E6E6E] dark:text-[#A3A3A3]">
                      <span>📊 Last session:</span>
                      <span className="font-semibold text-[#0A0A0A] dark:text-[#F5F5F5]">
                        {avgCorrPct !== '—' ? `avg ${avgCorrPct}%, ${below60Count}/${rosterSize} below 60%` : '—'}
                      </span>
                    </div>

                    {/* ⚠️ Top error tags row */}
                    <div className="flex items-start justify-between text-[#6E6E6E] dark:text-[#A3A3A3] gap-2">
                      <span className="shrink-0">⚠️ Top error tags:</span>
                      <span className="font-semibold text-[#0A0A0A] dark:text-[#F5F5F5] text-right truncate max-w-[200px]" title={topErrEntries.map(([spot, cnt]) => `${spot}: ${cnt}`).join(', ')}>
                        {topErrEntries.length > 0 ? topErrEntries.map(([spot, cnt]) => `${spot}: ${cnt}`).join(', ') : '—'}
                      </span>
                    </div>

                    {/* 📦 Resources row */}
                    <div className="flex items-center justify-between text-[#6E6E6E] dark:text-[#A3A3A3]">
                      <span>📦 Resources:</span>
                      <div className="flex items-center gap-1.5 flex-wrap justify-end">
                        <span className="font-semibold text-[#0A0A0A] dark:text-[#F5F5F5]">
                          {tabletsAvail !== '—' ? `${tabletsAvail} tablets vs ${rosterSize}` : '—'}
                        </span>
                        {tabletsInsuff && (
                          <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-red-500/20 text-red-600 dark:text-red-400 border border-red-500/30">
                            ⚠️ Insufficient tablets
                          </span>
                        )}
                      </div>
                    </div>

                    <div className="flex items-center justify-between">
                      <span className="text-[#6E6E6E] dark:text-[#A3A3A3]">
                        {govSess ? 'Government Session:' : 'Decided Topic:'}
                      </span>
                      <span className="font-semibold text-[#0A0A0A] dark:text-[#F5F5F5] truncate max-w-[200px]" title={govSess ? govSess.title : sup.decided_topic}>
                        {govSess ? govSess.title : (sup.decided_topic || 'Standard Progression')}
                      </span>
                    </div>

                    <div className="flex items-center justify-between">
                      <span className="text-[#6E6E6E] dark:text-[#A3A3A3]">Required Resource:</span>
                      <span className="font-semibold text-[#0A0A0A] dark:text-[#F5F5F5]">
                        {govSess ? govSess.requiredResource : (sup.recommended_resource || 'Printable Worksheet')}
                      </span>
                    </div>

                    <div className="flex items-center justify-between">
                      <span className="text-[#6E6E6E] dark:text-[#A3A3A3]">Safety Gate Verdict:</span>
                      <span className="font-semibold text-emerald-600 dark:text-emerald-400">
                        {sup.activity_status || 'passed_safety_gate'}
                      </span>
                    </div>
                  </div>
                </div>

                {/* Delivered Activity Content */}
                {delAct && (
                  <div className="pt-3 border-t border-black/[0.05] dark:border-white/[0.08] text-xs space-y-1.5">
                    <div className="font-semibold text-[#0A0A0A] dark:text-[#F5F5F5] flex items-center gap-1.5">
                      <BookOpen className="w-3.5 h-3.5" />
                      <span>{govSess ? 'Government Content:' : 'Activity:'} {delAct.topic}</span>
                    </div>
                    <div className="p-2.5 rounded-xl bg-white/40 dark:bg-white/5 text-[#6E6E6E] dark:text-[#A3A3A3] leading-relaxed">
                      {delAct.content?.instructions || `Interactive practice for ${delAct.topic}`}
                    </div>
                  </div>
                )}

                {/* Agent Reasoning Trail Collapsible Section */}
                <details className="group mt-3 pt-3 border-t border-black/[0.05] dark:border-white/[0.08] text-xs transition-all duration-200">
                  <summary className="font-semibold text-[#0A0A0A] dark:text-[#F5F5F5] cursor-pointer hover:text-amber-500 transition-colors flex items-center justify-between select-none py-1">
                    <span className="flex items-center gap-1.5">
                      <Sparkles className="w-3.5 h-3.5 text-amber-500" />
                      <span>Agent Reasoning Trail</span>
                    </span>
                    <ChevronDown className="w-3.5 h-3.5 text-[#6E6E6E] dark:text-[#A3A3A3] group-open:rotate-180 transition-transform" />
                  </summary>

                  <div className="mt-2.5 space-y-2.5 pl-1">
                    {/* 1. Progress Agent */}
                    <div className="p-2.5 rounded-xl bg-black/[0.02] dark:bg-white/[0.03] border border-black/[0.04] dark:border-white/[0.06] space-y-1">
                      <div className="flex items-center justify-between gap-2">
                        <span className="font-semibold text-[11px] text-cyan-600 dark:text-cyan-400">
                          Progress Agent
                        </span>
                        <div className="flex items-center gap-1.5 flex-wrap text-[10px]">
                          <span className="px-1.5 py-0.5 rounded bg-blue-500/10 text-blue-600 dark:text-blue-400 font-medium">
                            Mastery: {pDiag?.mastery_estimate ?? 'developing'}
                          </span>
                          <span className="px-1.5 py-0.5 rounded bg-purple-500/10 text-purple-600 dark:text-purple-400 font-medium">
                            Trend: {pDiag?.trend ?? 'insufficient_data'}
                          </span>
                          <span className="px-1.5 py-0.5 rounded bg-gray-500/10 text-gray-600 dark:text-gray-400 font-medium">
                            Conf: {pDiag?.confidence ?? 'medium'}
                          </span>
                        </div>
                      </div>
                      <p className="text-[11px] text-[#6E6E6E] dark:text-[#A3A3A3] leading-relaxed">
                        {pDiag?.explanation ?? 'No diagnosis detail provided.'}
                      </p>
                    </div>

                    {/* 2. Curriculum Agent */}
                    <div className="p-2.5 rounded-xl bg-black/[0.02] dark:bg-white/[0.03] border border-black/[0.04] dark:border-white/[0.06] space-y-1">
                      <div className="flex items-center justify-between gap-2">
                        <span className="font-semibold text-[11px] text-amber-600 dark:text-amber-400">
                          Curriculum Agent
                        </span>
                        <div className="flex items-center gap-1.5 text-[10px]">
                          <span className="px-1.5 py-0.5 rounded bg-amber-500/10 text-amber-600 dark:text-amber-400 font-medium">
                            Pacing: {cDec?.pacing_decision ?? 'hold'}
                          </span>
                          <span className="px-1.5 py-0.5 rounded bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 font-medium truncate max-w-[120px]">
                            {cDec?.decided_topic ?? sup.decided_topic ?? 'Standard Topic'}
                          </span>
                        </div>
                      </div>
                      <p className="text-[11px] text-[#6E6E6E] dark:text-[#A3A3A3] leading-relaxed">
                        {cDec?.reasoning ?? cDec?.explanation ?? 'No curriculum reasoning provided.'}
                      </p>
                    </div>

                    {/* 3. Resource Agent */}
                    <div className="p-2.5 rounded-xl bg-black/[0.02] dark:bg-white/[0.03] border border-black/[0.04] dark:border-white/[0.06] space-y-1">
                      <div className="flex items-center justify-between gap-2">
                        <span className="font-semibold text-[11px] text-indigo-600 dark:text-indigo-400">
                          Resource Agent
                        </span>
                        <span className="px-1.5 py-0.5 rounded bg-indigo-500/10 text-indigo-600 dark:text-indigo-400 font-medium text-[10px]">
                          {rRec?.recommended_resource ?? sup.recommended_resource ?? 'Printable Worksheet'}
                        </span>
                      </div>
                      <p className="text-[11px] text-[#6E6E6E] dark:text-[#A3A3A3] leading-relaxed">
                        {rRec?.rationale ?? rRec?.reasoning ?? rRec?.explanation ?? 'No resource rationale provided.'}
                      </p>
                    </div>

                    {/* 4. Activity Agent */}
                    <div className="p-2.5 rounded-xl bg-black/[0.02] dark:bg-white/[0.03] border border-black/[0.04] dark:border-white/[0.06] space-y-1">
                      <div className="flex items-center justify-between gap-2">
                        <span className="font-semibold text-[11px] text-emerald-600 dark:text-emerald-400">
                          Activity Agent
                        </span>
                        <div className="flex items-center gap-1.5 text-[10px]">
                          <span className="px-1.5 py-0.5 rounded bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 font-medium">
                            {aDes?.activity_type ?? 'printable_worksheet'}
                          </span>
                          <span className="px-1.5 py-0.5 rounded bg-gray-500/10 text-gray-600 dark:text-gray-400 font-medium">
                            {aDes?.estimated_time_minutes ? `${aDes.estimated_time_minutes} min` : '10 min'}
                          </span>
                        </div>
                      </div>
                      <p className="text-[11px] text-[#6E6E6E] dark:text-[#A3A3A3] leading-relaxed">
                        {aDes?.design_rationale ?? aDes?.explanation ?? aDes?.content?.instructions ?? 'Interactive practice activity.'}
                      </p>
                    </div>

                    {/* 5. Safety Gate */}
                    <div className="p-2.5 rounded-xl bg-black/[0.02] dark:bg-white/[0.03] border border-black/[0.04] dark:border-white/[0.06] space-y-1">
                      <div className="flex items-center justify-between gap-2">
                        <span className="font-semibold text-[11px] text-rose-600 dark:text-rose-400">
                          Safety Gate
                        </span>
                        {isPassed ? (
                          <span className="px-2 py-0.5 rounded bg-emerald-500/15 text-emerald-600 dark:text-emerald-400 font-semibold text-[10px]">
                            APPROVED
                          </span>
                        ) : (
                          <span className="px-2 py-0.5 rounded bg-red-500/15 text-red-600 dark:text-red-400 font-semibold text-[10px]">
                            REJECTED ({sVerd?.action ?? 'Failed'})
                          </span>
                        )}
                      </div>
                      <p className="text-[11px] text-[#6E6E6E] dark:text-[#A3A3A3] leading-relaxed">
                        {sVerd?.explanation ?? 'Passed all safety and pedagogical quality checks.'}
                      </p>
                    </div>
                  </div>
                </details>
              </div>
            );
          })}
        </div>
      </div>

      {/* 4. ADAPTIVE CLASSROOM FEEDBACK / SIGNAL INPUT */}
      <div className="liquid-glass-card rounded-[24px] p-6 space-y-4">
        <div className="flex items-center gap-2">
          <MessageSquare className="w-4 h-4 text-emerald-500" />
          <h3 className="text-base font-semibold text-[#0A0A0A] dark:text-[#F5F5F5]">
            Send Live Classroom Signal to Saarthi
          </h3>
        </div>
        <p className="text-xs text-[#6E6E6E] dark:text-[#A3A3A3]">
          Provide live feedback (e.g. student struggling, quick completion, concept confusion). Saarthi multi-agent system will re-evaluate progress and adjust next cycle.
        </p>

        {signalSuccessMsg && (
          <div className="p-3 rounded-xl bg-emerald-500/10 border border-emerald-500/20 text-emerald-600 dark:text-emerald-400 text-xs flex items-center gap-2">
            <CheckCircle2 className="w-4 h-4 shrink-0" />
            <span>{signalSuccessMsg}</span>
          </div>
        )}

        {signalErrorMsg && (
          <div className="p-3 rounded-xl bg-red-500/10 border border-red-500/20 text-red-600 dark:text-red-400 text-xs flex items-center gap-2">
            <AlertCircle className="w-4 h-4 shrink-0" />
            <span>{signalErrorMsg}</span>
          </div>
        )}

        <form onSubmit={handleSendSignal} className="space-y-3">
          <div className="flex flex-col sm:flex-row gap-3">
            <div className="sm:w-48 shrink-0">
              <label className="block text-xs font-semibold text-[#6E6E6E] dark:text-[#A3A3A3] mb-1">
                Target Grade
              </label>
              <select
                value={signalGrade}
                onChange={(e) => setSignalGrade(e.target.value)}
                className="w-full px-3 py-2 rounded-xl text-xs bg-white/50 dark:bg-black/40 border border-black/10 dark:border-white/10 text-[#0A0A0A] dark:text-[#F5F5F5] focus:outline-none focus:ring-2 focus:ring-amber-500/50"
              >
                {gradeSelectionList.map((g) => (
                  <option key={g.grade} value={g.grade} className="bg-white dark:bg-neutral-900 text-black dark:text-white">
                    Grade {g.grade} ({g.subject})
                  </option>
                ))}
              </select>
            </div>

            <div className="flex-1">
              <label className="block text-xs font-semibold text-[#6E6E6E] dark:text-[#A3A3A3] mb-1">
                Classroom Observation / Signal
              </label>
              <input
                type="text"
                value={signalText}
                onChange={(e) => setSignalText(e.target.value)}
                placeholder="e.g. Grade 3 completed practice quickly, ready for word problems."
                className="w-full px-3 py-2 rounded-xl text-xs bg-white/50 dark:bg-black/40 border border-black/10 dark:border-white/10 text-[#0A0A0A] dark:text-[#F5F5F5] focus:outline-none focus:ring-2 focus:ring-amber-500/50"
              />
            </div>
          </div>

          <div className="flex justify-end">
            <button
              type="submit"
              disabled={isSubmittingSignal || !signalText.trim()}
              className="liquid-glass-btn-primary px-4 py-2 rounded-xl text-xs font-semibold inline-flex items-center gap-1.5 cursor-pointer disabled:opacity-50"
            >
              {isSubmittingSignal ? (
                <>
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                  <span>Reasoning...</span>
                </>
              ) : (
                <>
                  <Send className="w-3.5 h-3.5" />
                  <span>Send Adaptive Signal</span>
                </>
              )}
            </button>
          </div>
        </form>
      </div>

      {/* END SESSION CONFIRMATION DIALOG / MODAL */}
      {isConfirmDialogOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
          <div
            className="fixed inset-0 bg-black/40 dark:bg-black/65 backdrop-blur-sm transition-opacity"
            onClick={!isEnding ? () => setIsConfirmDialogOpen(false) : undefined}
          />

          <div className="relative w-full max-w-md liquid-glass-card rounded-[24px] p-6 z-10 shadow-2xl space-y-5">
            <div className="space-y-2">
              <h3 className="text-lg font-semibold text-[#0A0A0A] dark:text-[#F5F5F5]">
                {t('session.end_confirm_title')}
              </h3>
              <p className="text-xs text-[#6E6E6E] dark:text-[#A3A3A3] leading-relaxed">
                {t('session.end_confirm_desc')}
              </p>
            </div>

            {endErrorMessage && (
              <div className="p-3 rounded-xl bg-red-500/10 border border-red-500/20 text-red-600 dark:text-red-400 text-xs flex items-center gap-2">
                <AlertCircle className="w-4 h-4 shrink-0" />
                <span>{endErrorMessage}</span>
              </div>
            )}

            <div className="flex items-center justify-end gap-3 pt-2">
              {/* Keep Session — Primary/Safe Action */}
              <button
                type="button"
                disabled={isEnding}
                onClick={() => setIsConfirmDialogOpen(false)}
                className="liquid-glass-btn-primary px-5 py-2.5 rounded-xl text-xs font-semibold cursor-pointer disabled:opacity-50"
              >
                {t('session.keep_btn')}
              </button>

              {/* End Session — Destructive Action */}
              <button
                type="button"
                disabled={isEnding}
                onClick={handleConfirmEndSession}
                className="liquid-glass-btn-secondary px-5 py-2.5 rounded-xl text-xs font-semibold text-red-600 dark:text-red-400 hover:bg-red-500/10 cursor-pointer disabled:opacity-50 inline-flex items-center gap-2"
              >
                {isEnding ? (
                  <>
                    <Loader2 className="w-3.5 h-3.5 animate-spin" />
                    <span>Ending...</span>
                  </>
                ) : (
                  <span>{t('session.end_btn')}</span>
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
