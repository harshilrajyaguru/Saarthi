import React from 'react';
import { Calendar, CheckCircle2 } from 'lucide-react';

/**
 * TodayAtAGlanceCard Component
 * Secondary card on the Dashboard rendered ONLY when there is NO active classroom session.
 * Gives a clean, product-facing overview of today's planning and attention items.
 */
export default function TodayAtAGlanceCard({
  includedGovSessions = {},
  plannedGradesCount = 0,
  isAttendanceSaved = false,
  onNavigateToAttendance = () => {},
}) {
  // Count government sessions that have at least 1 grade assigned
  const includedGovCount = Object.values(includedGovSessions).filter(
    (grades) => Array.isArray(grades) && grades.length > 0
  ).length;

  // Outstanding backlog count from existing frontend backlog items
  const backlogCount = 3;

  return (
    <div className="liquid-glass-card rounded-[24px] p-6 space-y-5 border border-black/[0.08] dark:border-white/[0.10] transition-all duration-300">
      {/* Title Header */}
      <div className="space-y-1">
        <h3 className="text-xs font-bold uppercase tracking-wider text-[#6E6E6E] dark:text-[#A3A3A3] flex items-center gap-2">
          <Calendar className="w-3.5 h-3.5 text-[#0A0A0A] dark:text-[#F5F5F5]" />
          TODAY AT A GLANCE
        </h3>
        <p className="text-xs text-[#6E6E6E] dark:text-[#A3A3A3]">
          A quick view of what needs your attention today.
        </p>
      </div>

      {/* 3 Metric Columns */}
      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 pt-1">
        <div className="p-3.5 rounded-2xl bg-black/[0.025] dark:bg-white/[0.03] border border-black/[0.04] dark:border-white/[0.06] space-y-0.5">
          <div className="text-base font-bold text-[#0A0A0A] dark:text-[#F5F5F5]">
            {plannedGradesCount} {plannedGradesCount === 1 ? 'Grade' : 'Grades'}
          </div>
          <div className="text-xs text-[#6E6E6E] dark:text-[#A3A3A3]">
            Planned
          </div>
        </div>

        <div className="p-3.5 rounded-2xl bg-black/[0.025] dark:bg-white/[0.03] border border-black/[0.04] dark:border-white/[0.06] space-y-0.5">
          <div className="text-base font-bold text-[#0A0A0A] dark:text-[#F5F5F5]">
            {includedGovCount} {includedGovCount === 1 ? 'Government Session' : 'Government Sessions'}
          </div>
          <div className="text-xs text-[#6E6E6E] dark:text-[#A3A3A3]">
            Included today
          </div>
        </div>

        <div className="p-3.5 rounded-2xl bg-black/[0.025] dark:bg-white/[0.03] border border-black/[0.04] dark:border-white/[0.06] space-y-0.5">
          <div className="text-base font-bold text-[#0A0A0A] dark:text-[#F5F5F5]">
            {backlogCount} Outstanding
          </div>
          <div className="text-xs text-[#6E6E6E] dark:text-[#A3A3A3]">
            Backlog items
          </div>
        </div>
      </div>

      {/* Subtle Attendance Row Divider & Action */}
      <div className="pt-4 border-t border-black/[0.06] dark:border-white/[0.08] flex items-center justify-between gap-4 text-xs">
        {isAttendanceSaved ? (
          <div className="flex items-center gap-2 font-semibold text-emerald-700 dark:text-emerald-300">
            <CheckCircle2 className="w-4 h-4 text-emerald-600 dark:text-emerald-400 shrink-0" />
            <span>✓ Attendance marked today</span>
          </div>
        ) : (
          <>
            <span className="text-[#0A0A0A] dark:text-[#F5F5F5] font-medium">
              Attendance not marked today
            </span>
            <button
              type="button"
              onClick={onNavigateToAttendance}
              className="liquid-glass-btn-secondary px-3.5 py-1.5 rounded-xl text-xs font-semibold inline-flex items-center gap-1.5 cursor-pointer hover:scale-[1.02] active:scale-[0.98] transition-transform"
            >
              <span>View →</span>
            </button>
          </>
        )}
      </div>
    </div>
  );
}
