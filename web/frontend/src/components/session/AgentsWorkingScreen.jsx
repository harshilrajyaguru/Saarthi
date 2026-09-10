import React, { useState, useEffect } from 'react';
import { Check, AlertCircle, RefreshCw } from 'lucide-react';
import { useTranslation } from '../../i18n/i18n';
import { startClassroomSession } from '../../services/saarthiApi';

export default function AgentsWorkingScreen({ sessionPayload, onComplete, onCancel }) {
  const { t } = useTranslation();

  // Selected grades from teacher input payload
  const gradeSelection = sessionPayload?.grade_selection || [
    { grade: '3', subject: 'Mathematics' },
    { grade: '4', subject: 'Mathematics' },
    { grade: '5', subject: 'Mathematics' },
  ];

  // 4 Sequential Agent Steps
  const STATUS_STEPS = [
    {
      id: 'progress',
      messageKey: 'session.status_step_1',
      defaultMessage: 'Reviewing where each grade left off...',
      agentKey: 'session.agent_step_1',
      defaultAgent: 'Progress',
    },
    {
      id: 'resources',
      messageKey: 'session.status_step_2',
      defaultMessage: "Checking what's available today...",
      agentKey: 'session.agent_step_2',
      defaultAgent: 'Resources',
    },
    {
      id: 'curriculum_activity',
      messageKey: 'session.status_step_3',
      defaultMessage: "Planning today's activities...",
      agentKey: 'session.agent_step_3',
      defaultAgent: 'Curriculum · Activity',
    },
    {
      id: 'safety',
      messageKey: 'session.status_step_4',
      defaultMessage: "Double-checking everything's ready for students...",
      agentKey: 'session.agent_step_4',
      defaultAgent: 'Safety',
    },
  ];

  const [currentStepIndex, setCurrentStepIndex] = useState(0);
  const [isReadyState, setIsReadyState] = useState(false);
  const [apiResult, setApiResult] = useState(null);
  const [apiError, setApiError] = useState(null);
  const [isApiLoading, setIsApiLoading] = useState(true);

  // Trigger real backend API call
  const triggerApiCall = async () => {
    setIsApiLoading(true);
    setApiError(null);
    try {
      const result = await startClassroomSession(sessionPayload);
      setApiResult(result);
      setIsApiLoading(false);
    } catch (err) {
      console.error('Failed to start session via backend:', err);
      setApiError(err.message || 'Agent orchestration failed. Please verify backend service.');
      setIsApiLoading(false);
    }
  };

  useEffect(() => {
    triggerApiCall();
  }, []);

  // Sequential progression timer
  useEffect(() => {
    let timer;
    let completionTimer;

    if (!apiError) {
      if (currentStepIndex < STATUS_STEPS.length) {
        timer = setTimeout(() => {
          setCurrentStepIndex((prev) => prev + 1);
        }, 900);
      } else if (currentStepIndex >= STATUS_STEPS.length && !isApiLoading && apiResult && !isReadyState) {
        setIsReadyState(true);
      }
    }

    if (isReadyState && apiResult) {
      completionTimer = setTimeout(() => {
        if (onComplete) {
          // Pass real backend response enriched with initial payload
          onComplete({
            ...apiResult,
            duration_minutes: sessionPayload.duration_minutes || apiResult.duration_minutes || 40,
            grade_selection: sessionPayload.grade_selection || [],
            resources: sessionPayload.resources || {},
            included_gov_sessions: sessionPayload.included_gov_sessions || {},
            started_at: Date.now(),
          });
        }
      }, 1200);
    }

    return () => {
      if (timer) clearTimeout(timer);
      if (completionTimer) clearTimeout(completionTimer);
    };
  }, [currentStepIndex, isReadyState, isApiLoading, apiResult, apiError, onComplete, sessionPayload]);

  // Compute grade status ('ready', 'working', 'pending') for each grade dynamically
  const getGradeStatus = (index) => {
    if (isReadyState || currentStepIndex >= STATUS_STEPS.length) return 'ready';
    const totalGrades = gradeSelection.length;
    const workingGradeIndex = Math.min(
      totalGrades - 1,
      Math.floor((currentStepIndex * totalGrades) / STATUS_STEPS.length)
    );
    if (index < workingGradeIndex) return 'ready';
    if (index === workingGradeIndex) return 'working';
    return 'pending';
  };

  return (
    <div className="w-full max-w-4xl mx-auto space-y-8 py-4 sm:py-8 px-2 sm:px-4">
      {apiError ? (
        <div className="liquid-glass-card rounded-[24px] p-8 sm:p-12 text-center space-y-5 max-w-xl mx-auto border border-red-500/30 bg-red-500/[0.03]">
          <div className="w-14 h-14 rounded-full bg-red-500/10 border border-red-500/30 flex items-center justify-center mx-auto text-red-600 dark:text-red-400 shadow-md">
            <AlertCircle className="w-7 h-7" />
          </div>
          <div className="space-y-2">
            <h2 className="text-xl font-bold tracking-tight text-[#0A0A0A] dark:text-[#F5F5F5] font-heading">
              Classroom Preparation Failed
            </h2>
            <p className="text-xs sm:text-sm text-red-600 dark:text-red-400 font-medium leading-relaxed">
              {apiError}
            </p>
          </div>
          <div className="pt-2 flex items-center justify-center gap-3">
            {onCancel && (
              <button
                type="button"
                onClick={onCancel}
                className="liquid-glass-btn-secondary px-5 py-2.5 rounded-xl text-xs font-semibold cursor-pointer"
              >
                Back to Setup
              </button>
            )}
            <button
              type="button"
              onClick={triggerApiCall}
              className="liquid-glass-btn-primary px-5 py-2.5 rounded-xl text-xs font-semibold inline-flex items-center gap-2 cursor-pointer"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              <span>Retry Session Setup</span>
            </button>
          </div>
        </div>
      ) : isReadyState ? (
        <div className="flex flex-col items-center justify-center py-16 px-4 text-center space-y-6 animate-fade-in-up">
          {/* Subtle Liquid Glass Checkmark Disc */}
          <div className="w-16 h-16 rounded-full bg-emerald-500/10 dark:bg-emerald-500/20 border border-emerald-500/30 flex items-center justify-center shadow-lg text-emerald-600 dark:text-emerald-400">
            <Check className="w-8 h-8 stroke-[2.5]" />
          </div>

          <div className="space-y-2">
            <h2 className="text-3xl font-bold tracking-tight text-[#0A0A0A] dark:text-[#F5F5F5] font-heading">
              {t('session.ready_heading', 'Ready')}
            </h2>
            <p className="text-sm text-[#6E6E6E] dark:text-[#A3A3A3]">
              {t('session.ready_subtitle', 'Your classroom is prepared.')}
            </p>
          </div>
        </div>
      ) : (
        /* AGENTS WORKING ORCHESTRATION VIEW */
        <div className="space-y-8 animate-fade-in-up">
          {/* Header */}
          <div className="space-y-1.5 border-b border-black/[0.06] dark:border-white/[0.08] pb-6">
            <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-[#0A0A0A] dark:text-[#F5F5F5] font-heading">
              {t('session.working_heading', "Preparing today's classroom")}
            </h1>
            <p className="text-sm text-[#6E6E6E] dark:text-[#A3A3A3]">
              {t('session.working_subtitle', 'Saarthi is coordinating the first plan for each grade.')}
            </p>
          </div>

          {/* Grid Layout: Left Column (Status Sequence) | Right Column (Liquid Glass Multi-Grade Panel) */}
          <div className="grid grid-cols-1 md:grid-cols-12 gap-8 items-start">
            {/* Sequential Agent Status Column */}
            <div className="md:col-span-7 space-y-4">
              {STATUS_STEPS.map((step, index) => {
                const isCompleted = index < currentStepIndex;
                const isActive = index === currentStepIndex;

                return (
                  <div
                    key={step.id}
                    className={`flex items-start gap-4 p-4 rounded-2xl transition-all duration-300 border ${
                      isActive
                        ? 'liquid-glass-card border-black/15 dark:border-white/20 bg-white/70 dark:bg-white/[0.08] shadow-md'
                        : isCompleted
                        ? 'border-transparent bg-black/[0.02] dark:bg-white/[0.02] opacity-90'
                        : 'border-transparent opacity-40'
                    }`}
                  >
                    {/* Status Indicator Disc */}
                    <div className="mt-0.5 shrink-0">
                      {isCompleted ? (
                        <div className="w-5 h-5 rounded-full bg-[#0A0A0A] dark:bg-white text-white dark:text-[#0A0A0A] flex items-center justify-center text-[10px] font-bold shadow-xs">
                          ✓
                        </div>
                      ) : isActive ? (
                        <div className="w-5 h-5 rounded-full border border-black/30 dark:border-white/40 flex items-center justify-center">
                          <span className="w-2.5 h-2.5 rounded-full bg-[#0A0A0A] dark:bg-white animate-subtle-pulse" />
                        </div>
                      ) : (
                        <div className="w-5 h-5 rounded-full border border-black/20 dark:border-white/20 flex items-center justify-center">
                          <span className="w-1.5 h-1.5 rounded-full bg-black/20 dark:bg-white/20" />
                        </div>
                      )}
                    </div>

                    {/* Message & Agent Label */}
                    <div className="space-y-1 min-w-0 flex-1">
                      <div className="flex items-center justify-between gap-2">
                        <span
                          className={`text-sm leading-snug ${
                            isActive
                              ? 'font-semibold text-[#0A0A0A] dark:text-[#F5F5F5]'
                              : isCompleted
                              ? 'font-medium text-[#0A0A0A] dark:text-[#F5F5F5]'
                              : 'text-[#6E6E6E] dark:text-[#A3A3A3]'
                          }`}
                        >
                          {t(step.messageKey, step.defaultMessage)}
                        </span>
                        {isCompleted && (
                          <span className="text-[11px] font-semibold text-emerald-600 dark:text-emerald-400 shrink-0 flex items-center gap-1">
                            ✓ {t('session.status_completed', 'Completed')}
                          </span>
                        )}
                      </div>

                      <div className="text-[11px] text-[#6E6E6E] dark:text-[#A3A3A3] font-normal">
                        {t(step.agentKey, step.defaultAgent)}
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>

            {/* Multi-Grade Liquid Glass Panel Column */}
            <div className="md:col-span-5">
              <div className="liquid-glass-card rounded-[24px] p-6 space-y-5 border border-black/[0.08] dark:border-white/[0.12] shadow-lg">
                {/* Panel Header */}
                <div className="border-b border-black/[0.06] dark:border-white/[0.08] pb-3">
                  <h3 className="text-xs font-semibold uppercase tracking-wider text-[#6E6E6E] dark:text-[#A3A3A3]">
                    {t('session.panel_title', 'Classroom preparation')}
                  </h3>
                </div>

                {/* Selected Grades Rows */}
                <div className="space-y-2.5">
                  {gradeSelection.map((item, idx) => {
                    const status = getGradeStatus(idx);
                    return (
                      <div
                        key={item.grade}
                        className="flex items-center justify-between p-3.5 rounded-xl bg-white/40 dark:bg-white/[0.04] border border-black/[0.04] dark:border-white/[0.06] text-xs transition-all duration-300"
                      >
                        <div className="flex items-center gap-3">
                          <span className="font-semibold text-[#0A0A0A] dark:text-[#F5F5F5]">
                            Grade {item.grade}
                          </span>
                          <span className="text-[#6E6E6E] dark:text-[#A3A3A3]">
                            {item.subject}
                          </span>
                        </div>

                        {/* Status Icon */}
                        <div className="w-5 h-5 flex items-center justify-center shrink-0">
                          {status === 'ready' ? (
                            <span className="text-emerald-600 dark:text-emerald-400 font-bold text-sm">
                              ✓
                            </span>
                          ) : status === 'working' ? (
                            <span className="w-2.5 h-2.5 rounded-full bg-[#0A0A0A] dark:bg-white animate-subtle-pulse" />
                          ) : (
                            <span className="text-[#6E6E6E] dark:text-[#A3A3A3] text-sm">
                              ○
                            </span>
                          )}
                        </div>
                      </div>
                    );
                  })}
                </div>

                {/* Panel Footer */}
                <div className="pt-3 border-t border-black/[0.06] dark:border-white/[0.08] text-[11px] text-[#6E6E6E] dark:text-[#A3A3A3]">
                  {gradeSelection.length === 1
                    ? t('session.panel_coordinating_single', 'Coordinating 1 grade')
                    : t('session.panel_coordinating', `Coordinating ${gradeSelection.length} grades`).replace(
                        '{count}',
                        gradeSelection.length
                      )}
                </div>
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
