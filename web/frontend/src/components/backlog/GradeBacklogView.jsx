import React, { useState, useMemo } from 'react';
import { ChevronDown, ChevronUp, CheckCircle2 } from 'lucide-react';

/**
 * DETERMINISTIC MOCK DATA FOR GRADE BACKLOG
 * Represents temporal carry-forward signals across previous sessions.
 * Structured to cleanly map onto Progress Agent, Curriculum Agent, and Activity History signals.
 * NO raw internal agent fields (e.g. mastery_estimate, confidence, trouble_spot_id).
 */
export const DETERMINISTIC_BACKLOG_DATA = {
  '3_mathematics': {
    summary: {
      totalOutstanding: 3,
      oldestSessionsAgo: 3,
    },
    pacing: {
      status: 'Held for reinforcement',
      statusType: 'warning',
      explanation:
        'The class is spending additional time on equivalent fractions before moving to the next curriculum position.',
    },
    unresolvedItems: [
      {
        id: 'spot_3_math_1',
        title: 'Numerator / denominator confusion',
        summary: 'Students continue to mix up numerator and denominator when scaling fractions.',
        flaggedSessionsAgo: 3,
        status: 'Still unresolved',
        observedDetail: 'Observed during group activity and diagnostic questions: 45% of students placed denominator above division bar when writing improper fractions.',
        firstFlaggedSessionAgo: 3,
        sessionsUnresolvedCount: 3,
        mostRecentSession: 'Yesterday\'s Afternoon Session',
        explanation: 'Students struggle distinguishing parts of a whole from total equal divisions when visual representations are omitted.',
      },
      {
        id: 'spot_3_math_2',
        title: 'Comparing unlike fractions',
        summary: 'Students are still relying on visual size rather than common denominators.',
        flaggedSessionsAgo: 2,
        status: 'Still unresolved',
        observedDetail: 'When comparing 1/3 and 2/5, 60% of students relied on drawing size rather than finding common denominator 15.',
        firstFlaggedSessionAgo: 2,
        sessionsUnresolvedCount: 2,
        mostRecentSession: '2 sessions ago',
        explanation: 'Perceptual estimation dominates over algorithmic fraction conversion during multi-choice questions.',
      },
    ],
    deferredActivities: [
      {
        id: 'def_3_math_1',
        title: 'Decimal conversion practice worksheet',
        skippedSessionsAgo: 2,
        reason: 'Teacher skipped this activity to make room for the PM eVIDYA TV government learning session.',
        status: 'Not revisited',
        topic: 'Decimals',
      },
    ],
  },
  '4_mathematics': {
    summary: {
      totalOutstanding: 3,
      oldestSessionsAgo: 4,
    },
    pacing: {
      status: 'Falling behind',
      statusType: 'behind',
      explanation:
        'The class has revisited decimal conversion across three sessions and has not yet demonstrated sufficient progress to advance.',
    },
    unresolvedItems: [
      {
        id: 'spot_4_math_1',
        title: 'Decimal place value misunderstanding',
        summary: 'Students confuse tenths and hundredths when ordering decimals with different digit lengths.',
        flaggedSessionsAgo: 4,
        status: 'Still unresolved',
        observedDetail: 'In Tablet Quiz, 0.4 was consistently judged as smaller than 0.15 due to digit length heuristic.',
        firstFlaggedSessionAgo: 4,
        sessionsUnresolvedCount: 4,
        mostRecentSession: '3 sessions ago',
        explanation: 'Whole number bias causes students to treat digits after decimal as whole numbers.',
      },
    ],
    deferredActivities: [
      {
        id: 'def_4_math_1',
        title: 'Equivalent fraction game cards',
        skippedSessionsAgo: 3,
        reason: 'Skipped during multi-grade tablet resource constraint.',
        status: 'Not revisited',
        topic: 'Fractions',
      },
      {
        id: 'def_4_math_2',
        title: 'Decimal number line printout',
        skippedSessionsAgo: 1,
        reason: 'Skipped to focus on government broadcast session.',
        status: 'Not revisited',
        topic: 'Decimals',
      },
    ],
  },
  '5_mathematics': {
    summary: {
      totalOutstanding: 0,
      oldestSessionsAgo: 0,
    },
    pacing: {
      status: 'On pace',
      statusType: 'on_pace',
      explanation: 'The class is progressing smoothly with the planned curriculum.',
    },
    unresolvedItems: [],
    deferredActivities: [],
  },
  '3_science': {
    summary: {
      totalOutstanding: 1,
      oldestSessionsAgo: 1,
    },
    pacing: {
      status: 'On pace',
      statusType: 'on_pace',
      explanation: 'The class is progressing with the planned science curriculum.',
    },
    unresolvedItems: [
      {
        id: 'spot_3_sci_1',
        title: 'Shadow length vs light source distance',
        summary: 'Students invert relationship between distance of light source and shadow casting size.',
        flaggedSessionsAgo: 1,
        status: 'Still unresolved',
        observedDetail: 'During DIKSHA virtual lab simulation, students incorrectly predicted shadow size when light moved closer.',
        firstFlaggedSessionAgo: 1,
        sessionsUnresolvedCount: 1,
        mostRecentSession: 'Last Friday session',
        explanation: 'Requires hands-on tactile reinforcement with flashlight distance.',
      },
    ],
    deferredActivities: [],
  },
};

const ALL_GRADES = ['1', '2', '3', '4', '5', '6', '7', '8'];
const ALL_SUBJECTS = ['Mathematics', 'Science', 'English', 'Social Studies', 'Environmental Studies'];

export default function GradeBacklogView({ activeSession, sharedState }) {
  const initialGrade = activeSession?.grade_selection?.[0]?.grade || activeSession?.grades?.[0]?.grade || '3';
  const [selectedGrade, setSelectedGrade] = useState(initialGrade);
  const [selectedSubject, setSelectedSubject] = useState('Mathematics');
  const [expandedItemId, setExpandedItemId] = useState(null);

  // Retrieve data deterministically for selected Grade x Subject
  const currentKey = `${selectedGrade}_${selectedSubject.toLowerCase().replace(/\s+/g, '_')}`;
  const effectiveState = sharedState || activeSession?.shared_state;

  // Extract from sharedState if available, fallback to deterministic data
  const backlogData = useMemo(() => {
    const defaultData = DETERMINISTIC_BACKLOG_DATA[currentKey] || DETERMINISTIC_BACKLOG_DATA['default'] || {
      summary: { totalOutstanding: 0, oldestSessionsAgo: 0 },
      pacing: { status: 'On pace', statusType: 'on_pace', explanation: 'The class is progressing with the planned curriculum.' },
      unresolvedItems: [],
      deferredActivities: [],
    };

    if (!effectiveState) return defaultData;

    // Check if shared_state contains trouble spots / pacing for this grade
    const gradeKey = `Grade_${selectedGrade}_${selectedSubject === 'Mathematics' ? 'Math' : selectedSubject}`;
    const gradeProgress = effectiveState?.curriculum_progress?.[gradeKey] || effectiveState?.[gradeKey] || {};
    const troubleSpots = gradeProgress?.trouble_spots || effectiveState?.trouble_spots || [];

    if (troubleSpots.length > 0) {
      const unresolvedItems = troubleSpots.map((ts, idx) => ({
        id: ts.id || `spot_${selectedGrade}_${idx}`,
        title: ts.topic || ts.title || 'Concept reinforcement required',
        summary: ts.description || ts.summary || 'Identified from student performance telemetry.',
        flaggedSessionsAgo: ts.sessions_ago || 1,
        status: 'Still unresolved',
        observedDetail: ts.detail || 'Flagged during active classroom cycle.',
        firstFlaggedSessionAgo: ts.first_flagged || 1,
        sessionsUnresolvedCount: ts.count || 1,
        mostRecentSession: 'Active session cycle',
        explanation: ts.explanation || 'Requires additional practice and scaffolding.',
      }));

      return {
        ...defaultData,
        unresolvedItems,
      };
    }

    return defaultData;
  }, [currentKey, effectiveState, selectedGrade, selectedSubject]);

  // Sort unresolved items oldest first (chronological persistence)
  const sortedUnresolvedItems = useMemo(() => {
    return [...(backlogData.unresolvedItems || [])].sort((a, b) => b.flaggedSessionsAgo - a.flaggedSessionsAgo);
  }, [backlogData.unresolvedItems]);

  // Sort deferred activities oldest skipped first
  const sortedDeferredActivities = useMemo(() => {
    return [...(backlogData.deferredActivities || [])].sort((a, b) => b.skippedSessionsAgo - a.skippedSessionsAgo);
  }, [backlogData.deferredActivities]);

  const totalOutstanding = (sortedUnresolvedItems.length || 0) + (sortedDeferredActivities.length || 0);
  const oldestSessionsAgo = sortedUnresolvedItems.length > 0 ? sortedUnresolvedItems[0].flaggedSessionsAgo : 0;
  const isFullyCaughtUp = totalOutstanding === 0 && backlogData.pacing?.statusType === 'on_pace';

  const toggleExpand = (id) => {
    setExpandedItemId((prev) => (prev === id ? null : id));
  };

  return (
    <div className="space-y-7 transition-all duration-300">
      {/* Page Header */}
      <div className="space-y-1">
        <h1 className="text-2xl font-bold tracking-tight text-[#0A0A0A] dark:text-[#F5F5F5] font-heading">
          Grade Backlog
        </h1>
        <p className="text-xs sm:text-sm text-[#6E6E6E] dark:text-[#A3A3A3]">
          What's still outstanding across your grades.
        </p>
      </div>

      {/* COMPACT GRADE & SUBJECT SELECTORS */}
      <div className="flex flex-wrap items-center gap-4 p-4 rounded-2xl bg-black/[0.02] dark:bg-white/[0.03] border border-black/[0.05] dark:border-white/[0.08]">
        {/* Grade Selector */}
        <div className="flex items-center gap-2">
          <label htmlFor="grade-select" className="text-xs font-semibold uppercase tracking-wider text-[#6E6E6E] dark:text-[#A3A3A3]">
            GRADE
          </label>
          <select
            id="grade-select"
            value={selectedGrade}
            onChange={(e) => setSelectedGrade(e.target.value)}
            className="bg-white/80 dark:bg-white/10 text-xs font-semibold text-[#0A0A0A] dark:text-[#F5F5F5] px-3 py-1.5 rounded-xl border border-black/10 dark:border-white/15 focus:outline-none cursor-pointer"
          >
            {ALL_GRADES.map((g) => (
              <option key={g} value={g} className="bg-white dark:bg-[#1C1E22] text-[#0A0A0A] dark:text-[#F5F5F5]">
                Grade {g}
              </option>
            ))}
          </select>
        </div>

        {/* Subject Selector */}
        <div className="flex items-center gap-2">
          <label htmlFor="subject-select" className="text-xs font-semibold uppercase tracking-wider text-[#6E6E6E] dark:text-[#A3A3A3]">
            SUBJECT
          </label>
          <select
            id="subject-select"
            value={selectedSubject}
            onChange={(e) => setSelectedSubject(e.target.value)}
            className="bg-white/80 dark:bg-white/10 text-xs font-semibold text-[#0A0A0A] dark:text-[#F5F5F5] px-3 py-1.5 rounded-xl border border-black/10 dark:border-white/15 focus:outline-none cursor-pointer"
          >
            {ALL_SUBJECTS.map((sub) => (
              <option key={sub} value={sub} className="bg-white dark:bg-[#1C1E22] text-[#0A0A0A] dark:text-[#F5F5F5]">
                {sub}
              </option>
            ))}
          </select>
        </div>
      </div>

      {/* UNDERSTATED COMPACT SUMMARY BAR */}
      <div className="flex items-center justify-between gap-3 text-xs text-[#6E6E6E] dark:text-[#A3A3A3] px-1">
        <div className="font-semibold text-[#0A0A0A] dark:text-[#F5F5F5]">
          Grade {selectedGrade} · {selectedSubject}
        </div>
        {totalOutstanding > 0 ? (
          <div className="flex items-center gap-2 flex-wrap">
            <span className="px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-amber-500/15 text-amber-700 dark:text-amber-300 border border-amber-500/25">
              {totalOutstanding} {totalOutstanding === 1 ? 'outstanding item' : 'outstanding items'}
            </span>
            {oldestSessionsAgo > 0 && (
              <span className="text-[11px]">
                Oldest: {oldestSessionsAgo} {oldestSessionsAgo === 1 ? 'session' : 'sessions'} ago
              </span>
            )}
          </div>
        ) : (
          <span className="px-2.5 py-0.5 rounded-full text-[11px] font-semibold bg-emerald-500/15 text-emerald-700 dark:text-emerald-300 border border-emerald-500/25">
            All caught up
          </span>
        )}
      </div>

      {/* FULLY CAUGHT UP CELEBRATORY STATE */}
      {isFullyCaughtUp ? (
        <div className="liquid-glass-card rounded-[24px] p-8 text-center space-y-3 border border-emerald-500/20 bg-emerald-500/[0.02] dark:bg-emerald-500/[0.03]">
          <div className="w-10 h-10 rounded-full bg-emerald-500/15 border border-emerald-500/30 text-emerald-600 dark:text-emerald-400 flex items-center justify-center mx-auto">
            <CheckCircle2 className="w-5 h-5" />
          </div>
          <div className="space-y-1">
            <h3 className="text-lg font-bold text-[#0A0A0A] dark:text-[#F5F5F5] font-heading">
              Grade {selectedGrade} · {selectedSubject} — You're all caught up.
            </h3>
            <p className="text-xs text-[#6E6E6E] dark:text-[#A3A3A3] max-w-md mx-auto">
              No unresolved trouble spots, no deferred activities, and pacing is on track.
            </p>
          </div>
        </div>
      ) : (
        <div className="space-y-6">
          {/* SECTION 1 — UNRESOLVED TROUBLE SPOTS */}
          <div className="space-y-3">
            <div>
              <h2 className="text-sm font-bold uppercase tracking-wider text-[#0A0A0A] dark:text-[#F5F5F5]">
                Unresolved
              </h2>
              <p className="text-xs text-[#6E6E6E] dark:text-[#A3A3A3]">
                Recurring issues that haven't been cleared yet.
              </p>
            </div>

            {sortedUnresolvedItems.length === 0 ? (
              <div className="p-4 rounded-2xl bg-white/50 dark:bg-white/[0.03] border border-black/[0.05] dark:border-white/[0.07] text-xs space-y-1">
                <div className="font-semibold text-emerald-600 dark:text-emerald-400 flex items-center gap-1.5">
                  <CheckCircle2 className="w-4 h-4" />
                  <span>No unresolved trouble spots</span>
                </div>
                <p className="text-[#6E6E6E] dark:text-[#A3A3A3]">
                  Nothing currently needs to be carried forward.
                </p>
              </div>
            ) : (
              <div className="liquid-glass-card rounded-[24px] overflow-hidden border border-black/[0.08] dark:border-white/[0.10] divide-y divide-black/[0.05] dark:divide-white/[0.07]">
                {sortedUnresolvedItems.map((item) => {
                  const isExpanded = expandedItemId === item.id;
                  return (
                    <div key={item.id} className="p-4 space-y-2 transition-colors duration-150 hover:bg-black/[0.01] dark:hover:bg-white/[0.02]">
                      <div className="flex items-center justify-between gap-3 text-xs">
                        <span className="text-[11px] font-semibold text-amber-600 dark:text-amber-400 uppercase tracking-wider">
                          Flagged {item.flaggedSessionsAgo} {item.flaggedSessionsAgo === 1 ? 'session' : 'sessions'} ago
                        </span>
                        <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-black/5 dark:bg-white/10 text-[#6E6E6E] dark:text-[#A3A3A3]">
                          {item.status}
                        </span>
                      </div>

                      <div className="flex items-start justify-between gap-3">
                        <div className="space-y-1 min-w-0 flex-1">
                          <h3 className="text-base font-semibold tracking-tight text-[#0A0A0A] dark:text-[#F5F5F5] font-heading">
                            {item.title}
                          </h3>
                          <p className="text-xs text-[#6E6E6E] dark:text-[#A3A3A3] leading-relaxed">
                            {item.summary}
                          </p>
                        </div>

                        <button
                          type="button"
                          onClick={() => toggleExpand(item.id)}
                          className="liquid-glass-btn-secondary px-3 py-1.5 rounded-xl text-xs font-medium shrink-0 flex items-center gap-1 cursor-pointer"
                        >
                          <span>{isExpanded ? 'Collapse' : 'Review'}</span>
                          {isExpanded ? <ChevronUp className="w-3.5 h-3.5" /> : <ChevronDown className="w-3.5 h-3.5" />}
                        </button>
                      </div>

                      {/* EXPANDABLE DETAILS */}
                      {isExpanded && (
                        <div className="pt-3 mt-2 border-t border-black/[0.05] dark:border-white/[0.07] space-y-2.5 text-xs animate-fade-in">
                          <div className="grid grid-cols-1 sm:grid-cols-3 gap-2 p-3 rounded-xl bg-black/[0.025] dark:bg-white/[0.03] border border-black/[0.04] dark:border-white/[0.06]">
                            <div>
                              <span className="text-[#6E6E6E] dark:text-[#A3A3A3]">First Flagged: </span>
                              <span className="font-semibold text-[#0A0A0A] dark:text-[#F5F5F5]">
                                {item.firstFlaggedSessionAgo} sessions ago
                              </span>
                            </div>
                            <div>
                              <span className="text-[#6E6E6E] dark:text-[#A3A3A3]">Unresolved: </span>
                              <span className="font-semibold text-[#0A0A0A] dark:text-[#F5F5F5]">
                                {item.sessionsUnresolvedCount} sessions
                              </span>
                            </div>
                            <div>
                              <span className="text-[#6E6E6E] dark:text-[#A3A3A3]">Most Recent: </span>
                              <span className="font-semibold text-[#0A0A0A] dark:text-[#F5F5F5]">
                                {item.mostRecentSession}
                              </span>
                            </div>
                          </div>

                          <div className="space-y-1">
                            <div className="text-[11px] font-semibold uppercase tracking-wider text-[#6E6E6E] dark:text-[#A3A3A3]">
                              What was observed
                            </div>
                            <p className="text-[#0A0A0A] dark:text-[#F5F5F5] leading-relaxed">
                              {item.observedDetail}
                            </p>
                          </div>

                          <div className="space-y-1">
                            <div className="text-[11px] font-semibold uppercase tracking-wider text-[#6E6E6E] dark:text-[#A3A3A3]">
                              Explanation
                            </div>
                            <p className="text-[#6E6E6E] dark:text-[#A3A3A3] leading-relaxed">
                              {item.explanation}
                            </p>
                          </div>
                        </div>
                      )}
                    </div>
                  );
                })}
              </div>
            )}
          </div>

          {/* SECTION 2 — PACING */}
          <div className="space-y-3">
            <div>
              <h2 className="text-sm font-bold uppercase tracking-wider text-[#0A0A0A] dark:text-[#F5F5F5]">
                Pacing
              </h2>
              <p className="text-xs text-[#6E6E6E] dark:text-[#A3A3A3]">
                Current curriculum position and pace.
              </p>
            </div>

            <div className="liquid-glass-card rounded-[24px] p-5 space-y-2 border border-black/[0.08] dark:border-white/[0.10]">
              <div className="flex items-center justify-between gap-3">
                <span className="text-xs font-semibold text-[#0A0A0A] dark:text-[#F5F5F5]">
                  Grade {selectedGrade} · {selectedSubject}
                </span>

                {backlogData.pacing.statusType === 'on_pace' ? (
                  <span className="px-3 py-1 rounded-full text-xs font-semibold bg-emerald-500/15 border border-emerald-500/30 text-emerald-600 dark:text-emerald-400">
                    On pace
                  </span>
                ) : backlogData.pacing.statusType === 'warning' ? (
                  <span className="px-3 py-1 rounded-full text-xs font-semibold bg-amber-500/15 border border-amber-500/30 text-amber-600 dark:text-amber-400">
                    {backlogData.pacing.status}
                  </span>
                ) : (
                  <span className="px-3 py-1 rounded-full text-xs font-semibold bg-rose-500/15 border border-rose-500/30 text-rose-600 dark:text-rose-400">
                    {backlogData.pacing.status}
                  </span>
                )}
              </div>

              <p className="text-xs text-[#6E6E6E] dark:text-[#A3A3A3] leading-relaxed">
                {backlogData.pacing.explanation}
              </p>
            </div>
          </div>

          {/* SECTION 3 — DEFERRED ACTIVITIES */}
          <div className="space-y-3">
            <div>
              <h2 className="text-sm font-bold uppercase tracking-wider text-[#0A0A0A] dark:text-[#F5F5F5]">
                Deferred activities
              </h2>
              <p className="text-xs text-[#6E6E6E] dark:text-[#A3A3A3]">
                Activities that were skipped and haven't been revisited.
              </p>
            </div>

            {sortedDeferredActivities.length === 0 ? (
              <div className="p-4 rounded-2xl bg-white/50 dark:bg-white/[0.03] border border-black/[0.05] dark:border-white/[0.07] text-xs space-y-1">
                <div className="font-semibold text-emerald-600 dark:text-emerald-400 flex items-center gap-1.5">
                  <CheckCircle2 className="w-4 h-4" />
                  <span>No deferred activities</span>
                </div>
                <p className="text-[#6E6E6E] dark:text-[#A3A3A3]">
                  Everything skipped previously has been revisited.
                </p>
              </div>
            ) : (
              <div className="liquid-glass-card rounded-[24px] overflow-hidden border border-black/[0.08] dark:border-white/[0.10] divide-y divide-black/[0.05] dark:divide-white/[0.07]">
                {sortedDeferredActivities.map((def) => (
                  <div key={def.id} className="p-4 space-y-2 text-xs">
                    <div className="flex items-center justify-between gap-3">
                      <span className="text-[11px] font-semibold text-amber-600 dark:text-amber-400 uppercase tracking-wider">
                        Skipped {def.skippedSessionsAgo} {def.skippedSessionsAgo === 1 ? 'session' : 'sessions'} ago
                      </span>
                      <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-black/5 dark:bg-white/10 text-[#6E6E6E] dark:text-[#A3A3A3]">
                        Status: {def.status}
                      </span>
                    </div>

                    <div className="font-semibold text-[#0A0A0A] dark:text-[#F5F5F5] text-sm">
                      {def.title}
                    </div>

                    <div className="text-[#6E6E6E] dark:text-[#A3A3A3] leading-relaxed">
                      <span className="font-semibold text-[#0A0A0A] dark:text-[#F5F5F5]">Reason: </span>
                      {def.reason}
                    </div>
                  </div>
                ))}
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
