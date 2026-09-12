import React, { useState, useEffect, useRef } from 'react';
import { AlertCircle, RefreshCw, Sparkles, Terminal } from 'lucide-react';
import { useTranslation } from '../../i18n/i18n';
import { startSession, normalizeCycle, streamSessionEvents } from '../../services/saarthiApi';

export default function AgentsWorkingScreen({ sessionPayload, onComplete, onReady, onCancel }) {
  const { t } = useTranslation();
  const [events, setEvents] = useState([]);
  const [elapsedSeconds, setElapsedSeconds] = useState(0);
  const [errorTraceback, setErrorTraceback] = useState(null);
  const feedEndRef = useRef(null);

  const handleReadyCallback = onReady || onComplete;

  const startSessionFlow = async () => {
    setEvents([]);
    setErrorTraceback(null);
    setElapsedSeconds(0);

    try {
      // 1. POST start session (returns instantly with { session_id, status: "running" })
      const res = await startSession(sessionPayload);
      const sid = res.session_id;
      if (!sid) {
        throw new Error('Backend failed to return a session_id');
      }

      // 2. Open SSE stream
      const es = streamSessionEvents(sid, (data) => {
        if (data.event === 'done') {
          es.close();
          if (data.status === 'ready' && data.result) {
            const normalized = normalizeCycle(data.result);
            const enriched = {
              ...normalized,
              duration_minutes: sessionPayload?.duration_minutes || normalized?.duration_minutes || 40,
              grade_selection: sessionPayload?.grade_selection || normalized?.grade_selection || [],
              resources: sessionPayload?.resources || normalized?.resources || {},
              started_at: Date.now(),
            };
            if (handleReadyCallback) {
              handleReadyCallback(enriched);
            }
          } else {
            setErrorTraceback(data.error || 'Agent orchestration encountered an unhandled error.');
          }
        } else {
          setEvents((prev) => [...prev, data]);
        }
      });

      return es;
    } catch (err) {
      console.error('Failed to start session:', err);
      setErrorTraceback(err.message || 'Failed to connect to Saarthi backend.');
      return null;
    }
  };

  useEffect(() => {
    let esInstance = null;
    let timer = setInterval(() => {
      setElapsedSeconds((prev) => prev + 1);
    }, 1000);

    startSessionFlow().then((es) => {
      esInstance = es;
    });

    return () => {
      clearInterval(timer);
      if (esInstance) esInstance.close();
    };
  }, []);

  // Auto-scroll feed to bottom when new events arrive
  useEffect(() => {
    feedEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [events]);

  const getAgentBadgeColor = (agent) => {
    switch (agent) {
      case 'ProgressAgent':
        return 'bg-sky-500/10 text-sky-700 dark:text-sky-300 border-sky-500/20';
      case 'CurriculumAgent':
        return 'bg-emerald-500/10 text-emerald-700 dark:text-emerald-300 border-emerald-500/20';
      case 'ResourceAgent':
        return 'bg-purple-500/10 text-purple-700 dark:text-purple-300 border-purple-500/20';
      case 'ActivityAgent':
        return 'bg-indigo-500/10 text-indigo-700 dark:text-indigo-300 border-indigo-500/20';
      case 'SafetyGate':
        return 'bg-rose-500/10 text-rose-700 dark:text-rose-300 border-rose-500/20';
      case 'OrchestratorAgent':
      case 'Orchestrator':
        return 'bg-amber-500/10 text-amber-800 dark:text-amber-200 border-amber-500/30 font-bold';
      default:
        return 'bg-slate-500/10 text-slate-700 dark:text-slate-300 border-slate-500/20';
    }
  };

  return (
    <div className="w-full max-w-4xl mx-auto space-y-6 py-4 sm:py-6 px-2 sm:px-4 animate-fade-in-up">
      {errorTraceback ? (
        <div className="liquid-glass-card rounded-[24px] p-6 sm:p-8 space-y-4 max-w-3xl mx-auto border border-red-500/30 bg-red-500/[0.03]">
          <div className="flex items-center gap-3 text-red-600 dark:text-red-400">
            <AlertCircle className="w-6 h-6 shrink-0" />
            <h2 className="text-lg font-bold font-heading text-[#0A0A0A] dark:text-[#F5F5F5]">
              Classroom Preparation Failed
            </h2>
          </div>
          <div className="bg-black/90 text-red-300 font-mono text-xs p-4 rounded-xl max-h-72 overflow-y-auto whitespace-pre-wrap select-text border border-red-900/50">
            {errorTraceback}
          </div>
          <div className="flex items-center justify-end gap-3 pt-2">
            {onCancel && (
              <button
                type="button"
                onClick={onCancel}
                className="liquid-glass-btn-secondary px-4 py-2 rounded-xl text-xs font-semibold cursor-pointer"
              >
                Back to Setup
              </button>
            )}
            <button
              type="button"
              onClick={startSessionFlow}
              className="liquid-glass-btn-primary px-4 py-2 rounded-xl text-xs font-semibold inline-flex items-center gap-2 cursor-pointer"
            >
              <RefreshCw className="w-3.5 h-3.5" />
              <span>Retry Session Setup</span>
            </button>
          </div>
        </div>
      ) : (
        <div className="space-y-6">
          {/* Header Bar */}
          <div className="flex flex-wrap items-center justify-between gap-4 border-b border-black/[0.06] dark:border-white/[0.08] pb-4">
            <div className="space-y-1">
              <h1 className="text-2xl sm:text-3xl font-bold tracking-tight text-[#0A0A0A] dark:text-[#F5F5F5] font-heading flex items-center gap-2.5">
                <span>{t('session.working_heading', "Preparing today's classroom")}</span>
                <Sparkles className="w-5 h-5 text-amber-500 animate-subtle-pulse" />
              </h1>
              <p className="text-xs sm:text-sm text-[#6E6E6E] dark:text-[#A3A3A3]">
                {t('session.working_subtitle', 'Saarthi multi-agent orchestration engine is reasoning live.')}
              </p>
            </div>

            {/* Live Counter Badge */}
            <div className="flex items-center gap-2.5 px-4 py-2 rounded-full bg-amber-500/10 dark:bg-amber-500/20 border border-amber-500/30 text-amber-800 dark:text-amber-300 text-xs font-semibold shadow-xs">
              <span className="w-2 h-2 rounded-full bg-amber-500 animate-ping" />
              <span>Agents reasoning… {elapsedSeconds}s</span>
            </div>
          </div>

          {/* Live Agent Event Stream Container */}
          <div className="liquid-glass-card rounded-[24px] p-4 sm:p-6 space-y-3 border border-black/[0.08] dark:border-white/[0.12] shadow-lg">
            {/* Terminal Header */}
            <div className="flex items-center justify-between border-b border-black/[0.06] dark:border-white/[0.08] pb-3 text-xs font-semibold text-[#6E6E6E] dark:text-[#A3A3A3]">
              <div className="flex items-center gap-2">
                <Terminal className="w-4 h-4 text-sky-500" />
                <span>LIVE AGENT REASONING FEED</span>
              </div>
              <span className="text-[11px] font-normal font-mono text-[#6E6E6E] dark:text-[#A3A3A3]">
                {events.length} events logged
              </span>
            </div>

            {/* Event List Feed */}
            <div className="h-[420px] overflow-y-auto space-y-1.5 pr-2 custom-scrollbar">
              {events.length === 0 ? (
                <div className="h-full flex items-center justify-center text-xs text-[#6E6E6E] dark:text-[#A3A3A3] italic gap-2">
                  <span className="w-2 h-2 rounded-full bg-sky-500 animate-ping" />
                  <span>Connecting to live agent trace stream...</span>
                </div>
              ) : (
                events.map((ev, index) => {
                  const isOrchestratorDecision = ev.event === 'orchestrator_decision';
                  const timeStr = ev.ts ? new Date(ev.ts * 1000).toLocaleTimeString() : '';

                  if (isOrchestratorDecision) {
                    return (
                      <div
                        key={ev.id || index}
                        className="my-2 p-3 rounded-xl bg-amber-500/10 dark:bg-amber-500/20 border border-amber-500/30 text-amber-900 dark:text-amber-100 text-xs shadow-xs space-y-1"
                      >
                        <div className="flex items-center justify-between font-bold text-[11px] uppercase tracking-wider text-amber-800 dark:text-amber-300">
                          <span className="flex items-center gap-1.5">
                            ⚡ Orchestrator Priority Action
                          </span>
                          <span className="font-mono text-[10px] opacity-75">{timeStr}</span>
                        </div>
                        <p className="font-medium leading-relaxed">{ev.message}</p>
                      </div>
                    );
                  }

                  return (
                    <div
                      key={ev.id || index}
                      className="flex items-start gap-2 text-xs py-1.5 px-2.5 rounded-lg border-b border-black/[0.03] dark:border-white/[0.04] hover:bg-black/[0.02] dark:hover:bg-white/[0.02] transition-colors"
                    >
                      {/* Timestamp */}
                      <span className="text-[10px] font-mono text-[#6E6E6E] dark:text-[#A3A3A3] shrink-0 pt-0.5">
                        {timeStr}
                      </span>

                      {/* Agent Badge */}
                      <span
                        className={`text-[10px] font-semibold px-2 py-0.5 rounded-md border shrink-0 ${getAgentBadgeColor(
                          ev.agent
                        )}`}
                      >
                        {ev.agent}
                      </span>

                      {/* Grade Badge */}
                      {ev.grade && (
                        <span className="text-[10px] font-bold text-amber-600 dark:text-amber-400 bg-amber-500/10 px-1.5 py-0.5 rounded shrink-0">
                          G{ev.grade}
                        </span>
                      )}

                      {/* Event Content & Icon */}
                      <span
                        className={`flex-1 min-w-0 leading-relaxed ${
                          ev.event === 'reasoning'
                            ? 'italic text-[#6E6E6E] dark:text-[#A3A3A3]'
                            : ev.event === 'tool_call'
                            ? 'font-mono text-sky-600 dark:text-sky-400'
                            : ev.event === 'tool_result'
                            ? 'font-mono text-slate-500 dark:text-slate-400 text-[11px]'
                            : ev.event === 'completed'
                            ? 'font-medium text-emerald-700 dark:text-emerald-300'
                            : ev.event === 'started'
                            ? 'font-medium text-indigo-600 dark:text-indigo-400'
                            : 'text-[#0A0A0A] dark:text-[#F5F5F5]'
                        }`}
                      >
                        {ev.event === 'tool_call'
                          ? '🔧 '
                          : ev.event === 'completed'
                          ? '✅ '
                          : ev.event === 'started'
                          ? '▶ '
                          : ev.event === 'reasoning'
                          ? '💭 '
                          : '💬 '}
                        {ev.message}
                      </span>
                    </div>
                  );
                })
              )}
              <div ref={feedEndRef} />
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
