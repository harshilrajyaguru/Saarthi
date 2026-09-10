import React from 'react';
import { Activity } from 'lucide-react';

/**
 * QuickStatusCard Component
 * Secondary card on the Dashboard below/above active session view.
 * ONLY visible when an active classroom session exists.
 */
export default function QuickStatusCard({
  activeSession,
  onOpenStatusModal = () => {},
}) {
  const gradeSelection = (activeSession?.grade_selection && activeSession.grade_selection.length > 0)
    ? activeSession.grade_selection
    : (activeSession?.current_session_grades?.map((g) => ({
        grade: String(g.grade),
        subject: g.subject,
      })) || []);

  if (!activeSession || !gradeSelection.length) return null;

  const gradePillsText = gradeSelection.map((g) => `Grade ${g.grade}`).join(' · ');

  return (
    <div className="liquid-glass-card rounded-[24px] p-6 relative overflow-hidden transition-all duration-300 border border-black/[0.08] dark:border-white/[0.10]">
      <div className="flex items-center gap-2 mb-3">
        <span className="text-[11px] font-semibold tracking-wider text-[#6E6E6E] dark:text-[#A3A3A3] uppercase flex items-center gap-1.5">
          <Activity className="w-3.5 h-3.5 text-[#0A0A0A] dark:text-[#F5F5F5]" />
          QUICK CLASSROOM STATUS
        </span>
      </div>

      <div className="flex flex-col md:flex-row md:items-center justify-between gap-5 relative z-[1]">
        {/* Title & Active Grade Pills */}
        <div className="space-y-1.5 max-w-xl">
          <h3 className="text-xl font-bold tracking-tight text-[#0A0A0A] dark:text-[#F5F5F5] font-heading">
            See what each grade is doing
          </h3>
          <div className="pt-1 flex items-center gap-2 flex-wrap text-xs">
            <span className="px-3 py-1 rounded-full text-xs font-semibold bg-emerald-500/15 border border-emerald-500/30 text-emerald-700 dark:text-emerald-300">
              {gradePillsText}
            </span>
          </div>
        </div>

        {/* Primary Action Button */}
        <button
          type="button"
          onClick={onOpenStatusModal}
          className="liquid-glass-btn-primary rounded-[16px] px-5 py-2.5 text-xs font-semibold tracking-tight inline-flex items-center gap-2 cursor-pointer shrink-0 self-start md:self-auto hover:scale-[1.02] active:scale-[0.985] transition-transform"
        >
          <span>Check Status →</span>
        </button>
      </div>
    </div>
  );
}


