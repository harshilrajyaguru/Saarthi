import React from 'react';
import { ArrowRight, Sparkles, Clock, Layers, Monitor } from 'lucide-react';
import { useTranslation } from '../../i18n/i18n';

/**
 * StartSessionCard Component
 * Primary initial content card on the Saarthi Dashboard.
 * Serves as the visual focal point prompting the teacher to initialize today's classroom.
 */
export default function StartSessionCard({ onOpenModal }) {
  const { t } = useTranslation();

  return (
    <div className="liquid-glass-card rounded-[24px] p-7 mb-8 relative overflow-hidden transition-all duration-300">
      {/* Top subtle badge */}
      <div className="flex items-center gap-2 mb-3">
        <span className="text-[11px] font-semibold tracking-wider text-[#6E6E6E] dark:text-[#A3A3A3] uppercase flex items-center gap-1.5">
          <Sparkles className="w-3.5 h-3.5 text-[#0A0A0A] dark:text-[#F5F5F5]" />
          {t('session.ready_title')}
        </span>
      </div>

      <div className="flex flex-col md:flex-row md:items-center justify-between gap-6 relative z-[1]">
        {/* Title & Description */}
        <div className="space-y-1.5 max-w-xl">
          <h2 className="text-2xl font-semibold tracking-tight text-[#0A0A0A] dark:text-[#F5F5F5]">
            {t('session.start_title')}
          </h2>
          <p className="text-xs text-[#6E6E6E] dark:text-[#A3A3A3] leading-relaxed">
            {t('session.start_desc')}
          </p>
        </div>

        {/* Start Session CTA Button */}
        <button
          type="button"
          onClick={onOpenModal}
          className="liquid-glass-btn-primary rounded-[16px] px-6 py-3 text-sm font-semibold tracking-tight inline-flex items-center gap-2 cursor-pointer shrink-0 self-start md:self-auto hover:scale-[1.02] active:scale-[0.985] transition-transform"
        >
          <span>{t('session.start_btn')}</span>
        </button>
      </div>

      {/* Metrics / Constraints Preview Row */}
      <div className="mt-6 pt-5 border-t border-black/[0.05] dark:border-white/[0.08] grid grid-cols-2 sm:grid-cols-4 gap-4 text-xs">
        <div className="flex items-center gap-2.5 text-[#6E6E6E] dark:text-[#A3A3A3]">
          <Layers className="w-4 h-4 text-[#0A0A0A] dark:text-[#F5F5F5] shrink-0" />
          <div>
            <div className="text-[10px] uppercase font-semibold text-[#8E8E8E]">Grades</div>
            <div className="font-medium text-[#0A0A0A] dark:text-[#F5F5F5]">—</div>
          </div>
        </div>

        <div className="flex items-center gap-2.5 text-[#6E6E6E] dark:text-[#A3A3A3]">
          <Layers className="w-4 h-4 text-[#0A0A0A] dark:text-[#F5F5F5] shrink-0" />
          <div>
            <div className="text-[10px] uppercase font-semibold text-[#8E8E8E]">Subjects</div>
            <div className="font-medium text-[#0A0A0A] dark:text-[#F5F5F5]">—</div>
          </div>
        </div>

        <div className="flex items-center gap-2.5 text-[#6E6E6E] dark:text-[#A3A3A3]">
          <Clock className="w-4 h-4 text-[#0A0A0A] dark:text-[#F5F5F5] shrink-0" />
          <div>
            <div className="text-[10px] uppercase font-semibold text-[#8E8E8E]">Time</div>
            <div className="font-medium text-[#0A0A0A] dark:text-[#F5F5F5]">—</div>
          </div>
        </div>

        <div className="flex items-center gap-2.5 text-[#6E6E6E] dark:text-[#A3A3A3]">
          <Monitor className="w-4 h-4 text-[#0A0A0A] dark:text-[#F5F5F5] shrink-0" />
          <div>
            <div className="text-[10px] uppercase font-semibold text-[#8E8E8E]">Resources</div>
            <div className="font-medium text-[#0A0A0A] dark:text-[#F5F5F5]">—</div>
          </div>
        </div>
      </div>
    </div>
  );
}
