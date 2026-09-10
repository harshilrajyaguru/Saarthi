import React, { useState, useEffect } from 'react';
import { X, ChevronLeft, ChevronRight, Landmark, Clock, CheckCircle2 } from 'lucide-react';
import { useTranslation } from '../../i18n/i18n';

/**
 * QuickStatusModal Component
 * True 180-degree horizontal 3D card flip transition.
 * Physical Liquid Glass card rotates around its vertical center axis (0° -> 90° edge-on -> 180°).
 */
export default function QuickStatusModal({
  isOpen = false,
  onClose = () => {},
  activeSession = null,
}) {
  const { t } = useTranslation();
  const [displayedIndex, setDisplayedIndex] = useState(0);
  const [targetIndex, setTargetIndex] = useState(0);
  const [isFlipping, setIsFlipping] = useState(false);
  const [flipDirection, setFlipDirection] = useState('forward');

  const activeGrades = activeSession?.current_session_grades && activeSession.current_session_grades.length > 0
    ? activeSession.current_session_grades
    : (activeSession?.grade_selection || []);

  // Reset index & state when modal opens
  useEffect(() => {
    if (isOpen) {
      setDisplayedIndex(0);
      setTargetIndex(0);
      setIsFlipping(false);
      setFlipDirection('forward');
    }
  }, [isOpen]);

  // Keyboard Escape listener
  useEffect(() => {
    const handleKeyDown = (e) => {
      if (isOpen && e.key === 'Escape') {
        onClose();
      }
    };
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isOpen, onClose]);

  if (!isOpen || activeGrades.length === 0) return null;

  const canNavigate = activeGrades.length > 1;

  // Navigation Handlers with 180° Flip Trigger
  const handleNext = () => {
    if (isFlipping || !canNavigate) return;
    const nextIdx = (displayedIndex + 1) % activeGrades.length;
    setTargetIndex(nextIdx);
    setFlipDirection('forward');
    setIsFlipping(true);

    setTimeout(() => {
      setDisplayedIndex(nextIdx);
      setIsFlipping(false);
    }, 700);
  };

  const handlePrev = () => {
    if (isFlipping || !canNavigate) return;
    const prevIdx = (displayedIndex - 1 + activeGrades.length) % activeGrades.length;
    setTargetIndex(prevIdx);
    setFlipDirection('backward');
    setIsFlipping(true);

    setTimeout(() => {
      setDisplayedIndex(prevIdx);
      setIsFlipping(false);
    }, 700);
  };

  // Helper to normalize subject
  const normSubj = (s) => {
    if (!s) return 'Math';
    const clean = String(s).trim();
    if (['mathematics', 'maths', 'math'].includes(clean.toLowerCase())) return 'Math';
    return clean.charAt(0).toUpperCase() + clean.slice(1);
  };

  // Helper to derive display data for a given grade index
  const getGradeDetails = (gradeIdx) => {
    const currentSessionGrades = activeSession?.current_session_grades || [];
    const item = activeGrades[gradeIdx] || activeGrades[0] || {};

    const g = String(item.grade || '3');
    const subj = normSubj(item.subject || 'Math');
    const canonicalKey = item.grade_key || `Grade_${g}_${subj}`;
    const gov = item.gov_session || null;

    // Find exact current session grade item matching canonical key
    const csgMatch = currentSessionGrades.find((csg) => csg.grade_key === canonicalKey) || item;

    // Find delivered activity matching canonical key
    const deliveredActivities = activeSession?.delivered_activities || [];
    const delAct = csgMatch.delivered_activity || deliveredActivities.find((a) => {
      const actGk = `Grade_${a.grade}_${normSubj(a.subject)}`;
      return actGk === canonicalKey;
    });

    const started = !!delAct || !!gov || csgMatch.status === 'reconciled';

    // Derive per-grade recommended resource & activity type from backend agent results
    const rawResource = gov
      ? gov.requiredResource
      : (delAct?.activity_type || csgMatch.recommended_resource || 'printable_worksheet');

    const rawActType = gov
      ? 'Government Session Broadcast'
      : (delAct?.activity_type || csgMatch.recommended_resource || 'printable_worksheet');

    // Format Resource Requirement
    let reqRes = 'No materials needed';
    if (gov) {
      reqRes = gov.requiredResource;
    } else if (rawResource === 'digital_tablet_quiz' || rawResource === 'tablet_quiz') {
      reqRes = 'Digital Tablet Quiz (1 device/pair)';
    } else if (rawResource === 'printable_worksheet') {
      reqRes = 'Printable Worksheet';
    } else if (rawResource === 'whiteboard_activity') {
      reqRes = 'Interactive Whiteboard Practice';
    } else if (rawResource === 'tv_video') {
      reqRes = 'Shared TV Broadcast';
    } else {
      reqRes = String(rawResource).replace(/_/g, ' ');
    }

    // Format Activity Type
    let actType = 'Guided practice';
    if (gov) {
      actType = 'Government Session Broadcast';
    } else if (rawActType === 'digital_tablet_quiz' || rawActType === 'tablet_quiz') {
      actType = 'Tablet Quiz';
    } else if (rawActType === 'printable_worksheet') {
      actType = 'Printable Worksheet';
    } else if (rawActType === 'whiteboard_activity') {
      actType = 'Whiteboard Activity';
    } else if (rawActType === 'tv_video') {
      actType = 'TV Learning Video';
    } else {
      actType = String(rawActType).replace(/_/g, ' ');
    }

    const targetsMap = {
      '1': 'Basic counting & number line ordering',
      '2': 'Bridging ten in mental addition',
      '3': 'Visual fraction representations & scaling',
      '4': 'Converting fractions into decimals',
      '5': 'Equivalent fraction recognition & decimal operations',
      '6': 'Algebra & Multi-step linear equations',
      '7': 'Proportional reasoning & ratios',
      '8': 'Geometric proofs & linear equations',
    };
    const target = targetsMap[g] || `Core skill practice for Grade ${g} ${subj}`;
    const topic = gov ? gov.title : (delAct?.topic || csgMatch.decided_topic || `${subj} Concepts`);

    return {
      grade: g,
      subject: subj,
      govSession: gov,
      hasActivityStarted: started,
      resourceRequirement: reqRes,
      activityType: actType,
      targetExplanation: target,
      topicTitle: topic,
      status: csgMatch.status || 'reconciled',
      activityStatus: csgMatch.activity_status || 'passed_safety_gate',
    };
  };

  // Session Time
  const durationMinutes = activeSession?.duration_minutes || 30;
  const elapsedMin = activeSession?.started_at
    ? Math.max(1, Math.floor((Date.now() - activeSession.started_at) / 60000))
    : Math.round(durationMinutes * 0.4);
  const remainingMin = Math.max(1, durationMinutes - elapsedMin);

  // Render a Single 3D Glass Card Face
  const renderCardFace = (gradeIdx, isBackFace) => {
    const details = getGradeDetails(gradeIdx);

    return (
      <div
        className="absolute inset-0 w-full h-full liquid-glass-card rounded-[28px] p-6 sm:p-8 shadow-2xl flex flex-col justify-between border border-white/20 dark:border-white/10 text-[#0A0A0A] dark:text-[#F5F5F5] select-none"
        style={{
          backfaceVisibility: 'hidden',
          WebkitBackfaceVisibility: 'hidden',
          transform: isBackFace
            ? flipDirection === 'forward'
              ? 'rotateY(180deg)'
              : 'rotateY(-180deg)'
            : 'rotateY(0deg)',
        }}
      >
        {/* Header Bar */}
        <div className="flex items-center justify-between border-b border-black/[0.06] dark:border-white/[0.08] pb-4 shrink-0">
          <div className="flex items-center gap-2.5">
            <span className="px-2.5 py-0.5 rounded-full text-[10px] font-bold uppercase tracking-wider bg-black/5 dark:bg-white/10 text-[#0A0A0A] dark:text-[#F5F5F5]">
              QUICK CLASSROOM STATUS
            </span>
            <span className="text-xs text-[#6E6E6E] dark:text-[#A3A3A3] font-medium">
              Grade {gradeIdx + 1} of {activeGrades.length}
            </span>
          </div>

          <button
            type="button"
            onClick={onClose}
            aria-label="Close classroom status"
            className="liquid-glass-btn-icon w-8 h-8 rounded-full flex items-center justify-center cursor-pointer text-[#6E6E6E] hover:text-[#0A0A0A] dark:hover:text-[#F5F5F5] transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Content Area */}
        <div className="space-y-5 my-auto">
          <div className="space-y-1">
            <div className="text-xs font-bold uppercase tracking-wider text-[#6E6E6E] dark:text-[#A3A3A3]">
              Grade {details.grade} · {details.subject}
            </div>
            <h2 className="text-2xl font-bold tracking-tight text-[#0A0A0A] dark:text-[#F5F5F5] font-heading">
              {details.topicTitle}
            </h2>
          </div>

          <div>
            {!details.hasActivityStarted ? (
              <span className="px-3.5 py-1.5 rounded-full text-xs font-semibold tracking-wide bg-amber-500/15 text-amber-700 dark:text-amber-300 border border-amber-500/30 inline-flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-amber-500" />
                Waiting to begin
              </span>
            ) : details.govSession ? (
              <span className="px-3.5 py-1.5 rounded-full text-xs font-semibold tracking-wide bg-emerald-500/15 text-emerald-700 dark:text-emerald-300 border border-emerald-500/30 inline-flex items-center gap-2">
                <Landmark className="w-3.5 h-3.5" />
                Government Session
              </span>
            ) : (
              <span className="px-3.5 py-1.5 rounded-full text-xs font-semibold tracking-wide bg-emerald-500/15 text-emerald-700 dark:text-emerald-300 border border-emerald-500/30 inline-flex items-center gap-2">
                <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
                ● IN PROGRESS
              </span>
            )}
          </div>

          <div className="space-y-2 text-xs">
            <div className="flex items-center justify-between text-[#6E6E6E] dark:text-[#A3A3A3]">
              <span className="font-medium">Activity Type:</span>
              <span className="font-semibold text-[#0A0A0A] dark:text-[#F5F5F5]">{details.activityType}</span>
            </div>
            <div className="flex items-center justify-between text-[#6E6E6E] dark:text-[#A3A3A3]">
              <span className="font-medium">Resource Requirement:</span>
              <span className="font-semibold text-[#0A0A0A] dark:text-[#F5F5F5]">{details.resourceRequirement}</span>
            </div>
          </div>

          <div className="flex items-center justify-between p-3.5 rounded-2xl bg-black/[0.03] dark:bg-white/[0.04] border border-black/[0.05] dark:border-white/[0.06] text-xs">
            <div className="flex items-center gap-2 font-semibold text-[#0A0A0A] dark:text-[#F5F5F5]">
              <Clock className="w-4 h-4 text-emerald-600 dark:text-emerald-400 shrink-0" />
              <span>{elapsedMin} min elapsed</span>
            </div>
            <div className="text-[#6E6E6E] dark:text-[#A3A3A3] font-medium">
              {remainingMin} min remaining
            </div>
          </div>

          <div className="space-y-1.5 text-xs">
            <span className="text-[11px] font-semibold uppercase tracking-wider text-[#6E6E6E] dark:text-[#A3A3A3]">
              Targets:
            </span>
            <p className="text-[#0A0A0A] dark:text-[#F5F5F5] font-medium leading-relaxed">
              {details.targetExplanation}
            </p>
          </div>

          <div className="flex items-center gap-2 pt-1 text-[11px]">
            <span className="px-2.5 py-1 rounded-lg bg-black/5 dark:bg-white/10 font-medium text-[#6E6E6E] dark:text-[#A3A3A3]">
              On-level
            </span>
            <span className="px-2.5 py-1 rounded-lg bg-emerald-500/10 text-emerald-700 dark:text-emerald-300 font-semibold flex items-center gap-1">
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600 dark:text-emerald-400" /> Reviewed
            </span>
          </div>
        </div>

        {/* Bottom Navigation Buttons */}
        <div className="pt-4 border-t border-black/[0.06] dark:border-white/[0.08] flex items-center justify-between gap-4 shrink-0">
          <button
            type="button"
            onClick={handlePrev}
            disabled={!canNavigate || isFlipping}
            aria-label="Previous grade"
            className={`w-11 h-11 rounded-full liquid-glass-btn-icon flex items-center justify-center cursor-pointer transition-all ${
              !canNavigate || isFlipping
                ? 'opacity-40 cursor-not-allowed'
                : 'hover:scale-105 active:scale-95 text-[#0A0A0A] dark:text-[#F5F5F5]'
            }`}
          >
            <ChevronLeft className="w-5 h-5" />
          </button>

          <div className="text-xs font-semibold text-[#6E6E6E] dark:text-[#A3A3A3]">
            Grade {details.grade} ({gradeIdx + 1} of {activeGrades.length})
          </div>

          <button
            type="button"
            onClick={handleNext}
            disabled={!canNavigate || isFlipping}
            aria-label="Next grade"
            className={`w-11 h-11 rounded-full liquid-glass-btn-icon flex items-center justify-center cursor-pointer transition-all ${
              !canNavigate || isFlipping
                ? 'opacity-40 cursor-not-allowed'
                : 'hover:scale-105 active:scale-95 text-[#0A0A0A] dark:text-[#F5F5F5]'
            }`}
          >
            <ChevronRight className="w-5 h-5" />
          </button>
        </div>
      </div>
    );
  };

  return (
    <div
      className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6 overflow-hidden bg-black/40 dark:bg-black/70 backdrop-blur-sm transition-opacity duration-300"
      onClick={onClose}
      role="dialog"
      aria-label="Quick classroom status"
      aria-modal="true"
    >
      {/* Outer 3D Scene Container */}
      <div
        className="w-full max-w-lg relative"
        style={{ perspective: '1200px', height: '540px' }}
      >
        {/* Rotating Physical Glass Card Inner Container */}
        <div
          onClick={(e) => e.stopPropagation()}
          className={`w-full h-full relative transform-gpu ${
            isFlipping
              ? flipDirection === 'forward'
                ? 'animate-flip-180-forward'
                : 'animate-flip-180-backward'
              : ''
          }`}
          style={{ transformStyle: 'preserve-3d' }}
        >
          {/* Front Face (Current Grade) */}
          {renderCardFace(displayedIndex, false)}

          {/* Back Face (Target Grade during 180° flip) */}
          {isFlipping && renderCardFace(targetIndex, true)}
        </div>
      </div>

      {/* True 180-Degree Card Flip Keyframe Styles */}
      <style>{`
        @keyframes flip180Forward {
          0% {
            transform: rotateY(0deg);
          }
          100% {
            transform: rotateY(180deg);
          }
        }
        @keyframes flip180Backward {
          0% {
            transform: rotateY(0deg);
          }
          100% {
            transform: rotateY(-180deg);
          }
        }
        .animate-flip-180-forward {
          animation: flip180Forward 700ms cubic-bezier(0.22, 0.61, 0.36, 1) forwards;
        }
        .animate-flip-180-backward {
          animation: flip180Backward 700ms cubic-bezier(0.22, 0.61, 0.36, 1) forwards;
        }
        @media (prefers-reduced-motion: reduce) {
          .animate-flip-180-forward, .animate-flip-180-backward {
            animation: none !important;
            transition: opacity 200ms ease;
          }
        }
      `}</style>
    </div>
  );
}


