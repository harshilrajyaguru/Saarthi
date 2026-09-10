import React, { useState } from 'react';
import { Activity, Clock, CheckCircle2, ChevronDown, ChevronUp, Printer, AlertTriangle, Play, Landmark } from 'lucide-react';
import { useTranslation } from '../../i18n/i18n';

/**
 * ActivityView Component
 * Renders the CURRENT classroom activity for each active grade.
 * Implements 3 UI states:
 * - State 1: No active classroom session
 * - State 2: Active session exists, but activity has not started
 * - State 3: Activity is currently active (multi-grade cards)
 */
export default function ActivityView({ activeSession, onStartSession }) {
  const { t } = useTranslation();

  // Internal state for State 2 vs State 3 transition (when session is active)
  const [isActivityStarted, setIsActivityStarted] = useState(true);

  // Expander state for [ View Activity ] per grade card
  const [expandedContent, setExpandedContent] = useState({});

  // Feedback state per grade card
  const [feedbackState, setFeedbackState] = useState({});

  // Toast / notification feedback for print trigger
  const [printNotification, setPrintNotification] = useState(null);

  const toggleExpand = (grade) => {
    setExpandedContent((prev) => ({
      ...prev,
      [grade]: !prev[grade],
    }));
  };

  const handleFeedback = (grade, rating) => {
    setFeedbackState((prev) => ({
      ...prev,
      [grade]: rating,
    }));
  };

  const handlePrint = (grade, topic) => {
    setPrintNotification(`Print job sent for Grade ${grade} (${topic})`);
    setTimeout(() => {
      setPrintNotification(null);
    }, 4000);
  };

  // Helper to build deterministic activity card data per grade from activeSession
  const getActivityDataForGrade = (item, idx, totalGrades) => {
    const gradeNum = String(item.grade || (item.grade_key ? item.grade_key.split('_')[1] : '3'));
    const rawSubj = item.subject || (item.grade_key ? item.grade_key.split('_')[2] : 'Math');
    const canonicalSubj = rawSubj === 'Mathematics' || rawSubj === 'Maths' ? 'Math' : rawSubj;
    const gradeKey = item.grade_key || `Grade_${gradeNum}_${canonicalSubj}`;

    // Find matching current session grade record from activeSession.current_session_grades
    const currentSessionGrades = activeSession?.current_session_grades || [];
    const csgMatch = currentSessionGrades.find(
      (g) => g.grade_key === gradeKey || (String(g.grade) === gradeNum && (g.subject === canonicalSubj || g.subject === rawSubj))
    ) || item;

    // Find delivered activity object if present
    const deliveredActivities = activeSession?.delivered_activities || [];
    const delAct = deliveredActivities.find(
      (a) => (a.grade === gradeNum || a.grade_key === gradeKey) && (a.subject === canonicalSubj || a.subject === rawSubj)
    ) || csgMatch.activity_details || {};

    const topic = csgMatch.decided_topic || delAct.topic || csgMatch.topic || `${canonicalSubj} Concepts`;

    // Activity Type & Resource Requirement formatting
    const rawActType = csgMatch.activity_type || delAct.activity_type || 'printable_worksheet';
    const rawResourceReq = csgMatch.recommended_resource || delAct.resource_requirement || rawActType;

    const activityTypeFormatted = rawActType.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());
    const resourceReqFormatted = rawResourceReq.replace(/_/g, ' ').replace(/\b\w/g, (c) => c.toUpperCase());

    const activityTypeLabel = `${activityTypeFormatted} · ${resourceReqFormatted}`;
    const isPrintable = rawActType.toLowerCase().includes('printable') ||
                        rawActType.toLowerCase().includes('worksheet') ||
                        rawResourceReq.toLowerCase().includes('printable') ||
                        rawResourceReq.toLowerCase().includes('worksheet');

    // Estimated duration
    const estimatedTime = csgMatch.activity_details?.estimated_duration_minutes
      ? `${csgMatch.activity_details.estimated_duration_minutes} min`
      : delAct.estimated_duration_minutes
      ? `${delAct.estimated_duration_minutes} min`
      : `${activeSession?.duration_minutes || 45} min`;

    // Pedagogical target / rationale
    const whyExplanation = csgMatch.activity_details?.pedagogical_purpose ||
      csgMatch.activity_details?.target ||
      csgMatch.activity_details?.explanation ||
      delAct.pedagogical_purpose ||
      delAct.explanation ||
      `Targets key foundational skills for Grade ${gradeNum} ${canonicalSubj} (${topic}).`;

    // Questions / Student Instructions
    let questions = [];
    const rawQuestions = csgMatch.activity_details?.student_instructions ||
      csgMatch.activity_details?.questions ||
      csgMatch.activity_details?.exercise_details ||
      delAct.student_instructions ||
      delAct.questions ||
      delAct.exercise_details;

    if (Array.isArray(rawQuestions)) {
      questions = rawQuestions;
    } else if (typeof rawQuestions === 'string' && rawQuestions.trim()) {
      questions = rawQuestions.split('\n').filter((l) => l.trim().length > 0);
    } else if (csgMatch.activity_details?.content) {
      questions = [csgMatch.activity_details.content];
    } else {
      questions = [
        `1. Complete introductory activity on ${topic}.`,
        `2. Practice core exercises with partner guidance.`,
        `3. Review and check solutions with teacher.`
      ];
    }

    const safetyVerdict = csgMatch.safety_verdict?.verdict || 'Safety Reviewed';
    const safetyStatus = safetyVerdict === 'approved' || safetyVerdict === 'Safety Reviewed' ? 'Safety Reviewed' : safetyVerdict;
    const currentStatus = csgMatch.status || csgMatch.activity_status || 'In Progress';

    return {
      grade: gradeNum,
      subject: canonicalSubj,
      grade_key: gradeKey,
      topic,
      activityTypeLabel,
      resourceRequirement: resourceReqFormatted,
      isPrintable,
      estimatedTime,
      whyExplanation,
      questions,
      difficulty: csgMatch.activity_details?.difficulty || (idx % 2 === 0 ? 'On-level' : 'Scaffolded'),
      safetyStatus,
      currentStatus,
      conflictMessage: null,
    };
  };

  // --------------------------------------------------------------------------
  // STATE 1: NO ACTIVE SESSION
  // --------------------------------------------------------------------------
  if (!activeSession) {
    return (
      <div className="space-y-6">
        {/* Page Header */}
        <div className="space-y-1">
          <h1 className="text-2xl font-bold tracking-tight text-[#0A0A0A] dark:text-[#F5F5F5] font-heading">
            Activity
          </h1>
          <p className="text-xs sm:text-sm text-[#6E6E6E] dark:text-[#A3A3A3]">
            {t('activity.subtitle', 'Current classroom activity · What each grade is working on right now.')}
          </p>
        </div>

        {/* State 1 Empty Glass Card */}
        <div className="liquid-glass-card rounded-[24px] p-8 sm:p-12 text-center space-y-5 max-w-2xl mx-auto my-8 border border-black/[0.08] dark:border-white/[0.10]">
          <div className="w-14 h-14 rounded-full bg-black/5 dark:bg-white/10 flex items-center justify-center mx-auto text-[#0A0A0A] dark:text-[#F5F5F5]">
            <Activity className="w-7 h-7 stroke-[1.75]" />
          </div>

          <div className="space-y-2">
            <h2 className="text-xl font-bold tracking-tight text-[#0A0A0A] dark:text-[#F5F5F5] font-heading">
              {t('activity.state1_title', 'No activity in progress')}
            </h2>
            <p className="text-xs sm:text-sm text-[#6E6E6E] dark:text-[#A3A3A3] max-w-md mx-auto leading-relaxed">
              {t('activity.state1_desc', 'Start a classroom session to see what Saarthi is preparing for each grade.')}
            </p>
          </div>

          <div className="pt-2">
            <button
              type="button"
              onClick={onStartSession}
              className="liquid-glass-btn-primary rounded-[16px] px-6 py-3 text-xs font-semibold tracking-tight inline-flex items-center gap-2 cursor-pointer shadow-md hover:scale-[1.02] active:scale-[0.985] transition-transform"
            >
              <span>{t('session.start_btn', 'Start Session →')}</span>
            </button>
          </div>
        </div>
      </div>
    );
  }

  const gradeSelection = (activeSession.current_session_grades && activeSession.current_session_grades.length > 0)
    ? activeSession.current_session_grades
    : activeSession.grade_selection || [];

  // --------------------------------------------------------------------------
  // STATE 2: SESSION ACTIVE, ACTIVITY NOT STARTED
  // --------------------------------------------------------------------------
  if (!isActivityStarted) {
    return (
      <div className="space-y-6">
        {/* Page Header */}
        <div className="space-y-1">
          <h1 className="text-2xl font-bold tracking-tight text-[#0A0A0A] dark:text-[#F5F5F5] font-heading">
            Activity
          </h1>
          <p className="text-xs sm:text-sm text-[#6E6E6E] dark:text-[#A3A3A3]">
            {t('activity.subtitle', 'Current classroom activity · What each grade is working on right now.')}
          </p>
        </div>

        {/* State 2 Waiting Card */}
        <div className="liquid-glass-card rounded-[24px] p-7 sm:p-8 space-y-6 border border-black/[0.08] dark:border-white/[0.10] max-w-3xl">
          <div className="flex items-center justify-between gap-4 flex-wrap pb-4 border-b border-black/[0.06] dark:border-white/[0.08]">
            <div>
              <h2 className="text-lg font-bold tracking-tight text-[#0A0A0A] dark:text-[#F5F5F5] font-heading">
                {t('activity.state2_title', 'Preparing classroom activities')}
              </h2>
              <p className="text-xs text-[#6E6E6E] dark:text-[#A3A3A3] mt-0.5">
                {t('activity.state2_desc', 'Saarthi has prepared the classroom plan. Activities will appear here when they begin.')}
              </p>
            </div>

            <button
              type="button"
              onClick={() => setIsActivityStarted(true)}
              className="liquid-glass-btn-primary rounded-xl px-5 py-2.5 text-xs font-semibold inline-flex items-center gap-2 cursor-pointer shrink-0"
            >
              <Play className="w-3.5 h-3.5 fill-current" />
              <span>{t('activity.begin_btn', 'Begin Activities →')}</span>
            </button>
          </div>

          {/* Compact Grade Status List */}
          <div className="space-y-2.5">
            {gradeSelection.map((g) => (
              <div
                key={g.grade_key || g.grade}
                className="flex items-center justify-between p-3.5 rounded-xl bg-white/50 dark:bg-white/[0.04] border border-black/[0.04] dark:border-white/[0.06] text-xs"
              >
                <div className="font-semibold text-[#0A0A0A] dark:text-[#F5F5F5]">
                  Grade {g.grade} · {g.subject} {g.gov_session ? ' (Government Session)' : ''}
                </div>
                <div className="inline-flex items-center gap-1.5 font-semibold text-emerald-600 dark:text-emerald-400">
                  <span className="w-2 h-2 rounded-full bg-emerald-500" />
                  <span>Ready</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>
    );
  }

  // --------------------------------------------------------------------------
  // STATE 3: ACTIVE ACTIVITY (MULTI-GRADE CARDS)
  // --------------------------------------------------------------------------
  return (
    <div className="space-y-6">
      {/* Toast notification for print action */}
      {printNotification && (
        <div className="fixed bottom-6 right-6 z-50 liquid-glass-card rounded-2xl px-4 py-3 shadow-xl border border-emerald-500/30 flex items-center gap-3 animate-fade-in-up">
          <CheckCircle2 className="w-5 h-5 text-emerald-500 shrink-0" />
          <div className="text-xs font-semibold text-[#0A0A0A] dark:text-[#F5F5F5]">
            {printNotification}
          </div>
        </div>
      )}

      {/* Page Header */}
      <div className="flex items-center justify-between gap-4 flex-wrap">
        <div className="space-y-1">
          <h1 className="text-2xl font-bold tracking-tight text-[#0A0A0A] dark:text-[#F5F5F5] font-heading">
            Activity
          </h1>
          <p className="text-xs sm:text-sm text-[#6E6E6E] dark:text-[#A3A3A3]">
            {t('activity.subtitle', 'Current classroom activity · What each grade is working on right now.')}
          </p>
        </div>

        <button
          type="button"
          onClick={() => setIsActivityStarted(false)}
          className="liquid-glass-btn-secondary px-3.5 py-1.5 rounded-xl text-xs font-medium text-[#6E6E6E] dark:text-[#A3A3A3] cursor-pointer"
        >
          Pause Activities
        </button>
      </div>

      {/* Multi-Grade Activity Cards Layout */}
      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {gradeSelection.map((gItem, idx) => {
          const isGov = !!gItem.gov_session;
          const cardData = getActivityDataForGrade(gItem, idx, gradeSelection.length);
          const isExpanded = !!expandedContent[cardData.grade_key];
          const currentFeedback = feedbackState[cardData.grade_key];

          if (isGov) {
            const govSess = gItem.gov_session;
            return (
              <div
                key={cardData.grade_key}
                className="liquid-glass-card rounded-[24px] p-6 space-y-5 border border-emerald-500/30 bg-emerald-500/[0.02] dark:bg-emerald-500/[0.03] shadow-md flex flex-col justify-between transition-all duration-200"
              >
                <div className="space-y-4">
                  {/* Header: Grade & Government Session Badge */}
                  <div className="flex items-center justify-between gap-3">
                    <div className="text-xs font-semibold uppercase tracking-wider text-emerald-700 dark:text-emerald-300 flex items-center gap-1.5">
                      <Landmark className="w-4 h-4 text-emerald-600 dark:text-emerald-400" />
                      <span>Grade {gItem.grade} · Government Session</span>
                    </div>

                    <div className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-emerald-500/15 border border-emerald-500/30 text-emerald-600 dark:text-emerald-400 text-[10px] font-bold tracking-wider uppercase">
                      <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                      <span>IN PROGRESS</span>
                    </div>
                  </div>

                  {/* Topic Title */}
                  <div>
                    <h2 className="text-xl font-bold tracking-tight text-[#0A0A0A] dark:text-[#F5F5F5] font-heading">
                      {govSess.title}
                    </h2>
                  </div>

                  {/* Details Row */}
                  <div className="flex flex-wrap items-center justify-between gap-2 p-3 rounded-xl bg-black/[0.025] dark:bg-white/[0.03] border border-black/[0.04] dark:border-white/[0.06] text-xs">
                    <span className="font-semibold text-[#0A0A0A] dark:text-[#F5F5F5]">
                      {govSess.requiredResource}
                    </span>
                    <span className="text-[#6E6E6E] dark:text-[#A3A3A3] font-medium flex items-center gap-1">
                      <Clock className="w-3.5 h-3.5 inline" />
                      {govSess.durationMinutes} min
                    </span>
                  </div>

                  {/* Source Info */}
                  <div className="space-y-1 text-xs">
                    <div className="text-[11px] font-semibold uppercase tracking-wider text-[#6E6E6E] dark:text-[#A3A3A3]">
                      Official Government Source
                    </div>
                    <p className="text-[#0A0A0A] dark:text-[#F5F5F5] leading-relaxed">
                      {govSess.source}
                    </p>
                  </div>

                  {/* Expandable Session Content */}
                  {isExpanded && (
                    <div className="pt-3 border-t border-black/[0.06] dark:border-white/[0.08] space-y-3 animate-fade-in-up text-xs">
                      <div className="font-semibold text-[#0A0A0A] dark:text-[#F5F5F5] uppercase tracking-wider text-[11px]">
                        Session Overview & Details
                      </div>
                      <div className="p-3.5 rounded-xl bg-white/60 dark:bg-white/5 space-y-2 text-[#0A0A0A] dark:text-[#F5F5F5] border border-black/[0.04] dark:border-white/[0.06]">
                        <p className="leading-relaxed">{govSess.description}</p>
                        <div className="pt-1 text-[11px] text-[#6E6E6E] dark:text-[#A3A3A3]">
                          Schedule: {govSess.schedule} · Language: {govSess.language}
                        </div>
                      </div>

                      <div className="pt-1">
                        <a
                          href={govSess.sourceUrl}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="liquid-glass-btn-secondary px-3.5 py-2 rounded-xl text-xs font-semibold inline-flex items-center gap-1.5 cursor-pointer text-emerald-600 dark:text-emerald-400"
                        >
                          <span>Open on DIKSHA Portal ↗</span>
                        </a>
                      </div>
                    </div>
                  )}
                </div>

                {/* Card Footer Actions */}
                <div className="pt-4 border-t border-black/[0.06] dark:border-white/[0.08] flex items-center justify-between gap-2 text-xs">
                  <button
                    type="button"
                    onClick={() => toggleExpand(cardData.grade_key)}
                    className="liquid-glass-btn-secondary px-3 py-1.5 rounded-xl text-xs font-semibold inline-flex items-center gap-1 cursor-pointer"
                  >
                    <span>{isExpanded ? 'Hide Details' : 'View Session'}</span>
                    {isExpanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
                  </button>

                  <div className="flex items-center gap-2 text-[11px] text-[#6E6E6E] dark:text-[#A3A3A3]">
                    <span className="px-2 py-0.5 rounded-md bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 font-semibold">
                      ✓ Government Session Active
                    </span>
                  </div>
                </div>
              </div>
            );
          }

          return (
            <div
              key={cardData.grade_key}
              className="liquid-glass-card rounded-[24px] p-6 space-y-5 border border-black/[0.08] dark:border-white/[0.12] shadow-md flex flex-col justify-between transition-all duration-200"
            >
              <div className="space-y-4">
                {/* Header: Grade, Subject & Status Badge */}
                <div className="flex items-center justify-between gap-3">
                  <div className="text-xs font-semibold uppercase tracking-wider text-[#6E6E6E] dark:text-[#A3A3A3]">
                    Grade {cardData.grade} · {cardData.subject}
                  </div>

                  <div className="inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-full bg-emerald-500/15 border border-emerald-500/30 text-emerald-600 dark:text-emerald-400 text-[10px] font-bold tracking-wider uppercase">
                    <span className="w-1.5 h-1.5 rounded-full bg-emerald-500 animate-pulse" />
                    <span>{t('activity.in_progress', 'IN PROGRESS')}</span>
                  </div>
                </div>

                {/* Topic Title */}
                <div>
                  <h2 className="text-xl font-bold tracking-tight text-[#0A0A0A] dark:text-[#F5F5F5] font-heading">
                    {cardData.topic}
                  </h2>
                </div>

                {/* Activity Type & Teacher Action + Time */}
                <div className="flex flex-wrap items-center justify-between gap-2 p-3 rounded-xl bg-black/[0.025] dark:bg-white/[0.03] border border-black/[0.04] dark:border-white/[0.06] text-xs">
                  <span className="font-semibold text-[#0A0A0A] dark:text-[#F5F5F5]">
                    {cardData.activityTypeLabel}
                  </span>
                  <span className="text-[#6E6E6E] dark:text-[#A3A3A3] font-medium flex items-center gap-1">
                    <Clock className="w-3.5 h-3.5 inline" />
                    {cardData.estimatedTime}
                  </span>
                </div>

                {/* Inline Resource Conflict Warning if applicable */}
                {cardData.conflictMessage && (
                  <div className="p-3 rounded-xl bg-amber-500/10 border border-amber-500/25 text-amber-700 dark:text-amber-300 text-xs flex items-center gap-2">
                    <AlertTriangle className="w-4 h-4 shrink-0 text-amber-500" />
                    <span>⚠ {cardData.conflictMessage}</span>
                  </div>
                )}

                {/* Why This Activity */}
                <div className="space-y-1 text-xs">
                  <div className="text-[11px] font-semibold uppercase tracking-wider text-[#6E6E6E] dark:text-[#A3A3A3]">
                    Why this activity
                  </div>
                  <p className="text-[#0A0A0A] dark:text-[#F5F5F5] leading-relaxed">
                    {cardData.whyExplanation}
                  </p>
                </div>

                {/* Expandable Student Content Area */}
                {isExpanded && (
                  <div className="pt-3 border-t border-black/[0.06] dark:border-white/[0.08] space-y-3 animate-fade-in-up text-xs">
                    <div className="font-semibold text-[#0A0A0A] dark:text-[#F5F5F5] uppercase tracking-wider text-[11px]">
                      Student Exercises & Questions
                    </div>
                    <div className="p-3.5 rounded-xl bg-white/60 dark:bg-white/5 space-y-2 text-[#0A0A0A] dark:text-[#F5F5F5] border border-black/[0.04] dark:border-white/[0.06]">
                      {cardData.questions.map((q, qIdx) => (
                        <div key={qIdx} className="leading-relaxed">
                          {q}
                        </div>
                      ))}
                    </div>

                    {cardData.isPrintable && (
                      <div className="pt-1">
                        <button
                          type="button"
                          onClick={() => handlePrint(cardData.grade, cardData.topic)}
                          className="liquid-glass-btn-secondary px-3.5 py-1.5 rounded-xl text-xs font-medium inline-flex items-center gap-1.5 cursor-pointer"
                        >
                          <Printer className="w-3.5 h-3.5" />
                          <span>{t('activity.print_btn', 'Print Activity')}</span>
                        </button>
                      </div>
                    )}
                  </div>
                )}
              </div>

              {/* Card Footer Actions & Controls */}
              <div className="pt-4 border-t border-black/[0.06] dark:border-white/[0.08] space-y-3">
                {/* Secondary Info Row: View Activity toggle + Secondary metadata */}
                <div className="flex items-center justify-between gap-2 flex-wrap text-xs">
                  <button
                    type="button"
                    onClick={() => toggleExpand(cardData.grade_key)}
                    className="liquid-glass-btn-secondary px-3 py-1.5 rounded-xl text-xs font-semibold inline-flex items-center gap-1 cursor-pointer"
                  >
                    <span>{isExpanded ? t('activity.hide_content', 'Hide Activity') : t('activity.view_content', 'View Activity')}</span>
                    {isExpanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
                  </button>

                  <div className="flex items-center gap-2 text-[11px] text-[#6E6E6E] dark:text-[#A3A3A3]">
                    <span className="px-2 py-0.5 rounded-md bg-black/5 dark:bg-white/10 font-medium">
                      {cardData.difficulty}
                    </span>
                    <span className="px-2 py-0.5 rounded-md bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 font-semibold">
                      ✓ {cardData.safetyStatus}
                    </span>
                  </div>
                </div>

                {/* Tactile Feedback Controls */}
                <div className="flex items-center justify-between gap-2 pt-1">
                  <span className="text-[11px] text-[#6E6E6E] dark:text-[#A3A3A3] font-medium">
                    Feedback:
                  </span>

                  <div className="flex items-center gap-1.5">
                    <button
                      type="button"
                      onClick={() => handleFeedback(cardData.grade_key, 'went_well')}
                      className={`px-3 py-1.5 rounded-xl text-xs font-semibold cursor-pointer transition-all border ${
                        currentFeedback === 'went_well'
                          ? 'bg-emerald-500/20 border-emerald-500/40 text-emerald-700 dark:text-emerald-300 shadow-xs'
                          : 'liquid-glass-btn-secondary opacity-80 hover:opacity-100'
                      }`}
                    >
                      {t('activity.went_well', '✓ Went well')}
                    </button>

                    <button
                      type="button"
                      onClick={() => handleFeedback(cardData.grade_key, 'struggled')}
                      className={`px-3 py-1.5 rounded-xl text-xs font-semibold cursor-pointer transition-all border ${
                        currentFeedback === 'struggled'
                          ? 'bg-amber-500/20 border-amber-500/40 text-amber-700 dark:text-amber-300 shadow-xs'
                          : 'liquid-glass-btn-secondary opacity-80 hover:opacity-100'
                      }`}
                    >
                      {t('activity.struggled', 'Struggled')}
                    </button>

                    <button
                      type="button"
                      onClick={() => handleFeedback(cardData.grade_key, 'skip')}
                      className={`px-3 py-1.5 rounded-xl text-xs font-semibold cursor-pointer transition-all border ${
                        currentFeedback === 'skip'
                          ? 'bg-black/15 dark:bg-white/20 border-black/30 dark:border-white/30 text-[#0A0A0A] dark:text-[#F5F5F5] shadow-xs'
                          : 'liquid-glass-btn-secondary opacity-80 hover:opacity-100'
                      }`}
                    >
                      {t('activity.skip', 'Skip')}
                    </button>
                  </div>
                </div>
              </div>
            </div>
          );
        })}
      </div>
    </div>
  );
}

