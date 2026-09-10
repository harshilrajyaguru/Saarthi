import React, { useState } from 'react';
import { X, Plus, Minus, Monitor, Wifi, Printer, Tv, Landmark } from 'lucide-react';
import { useTranslation } from '../../i18n/i18n';
import { OFFICIAL_GOVERNMENT_CATALOG } from '../government/GovernmentSessionView';

const AVAILABLE_GRADES = ['1', '2', '3', '4', '5', '6', '7', '8'];
const SUBJECT_OPTIONS = ['Mathematics', 'Science', 'English', 'Social Studies', 'Environmental Studies'];
const PRESET_DURATIONS = [30, 40, 45, 60, 90];

export default function StartSessionModal({
  isOpen,
  onClose,
  onStartSession,
  includedGovSessions = {},
  onNavigateToGovSessions = () => {},
}) {
  const { t } = useTranslation();

  // Form State
  const [selectedGrades, setSelectedGrades] = useState(['3', '4', '5']);
  const [gradeSubjects, setGradeSubjects] = useState({
    '3': 'Mathematics',
    '4': 'Mathematics',
    '5': 'Mathematics',
  });
  const [durationMode, setDurationMode] = useState(40); // 30, 40, 45, 60, 90, or 'custom'
  const [customDuration, setCustomDuration] = useState(40);
  const [tablets, setTablets] = useState(2);
  const [tvAvailable, setTvAvailable] = useState(true);
  const [printerAvailable, setPrinterAvailable] = useState(true);
  const [internetConnected, setInternetConnected] = useState(true);
  const [constraintsList, setConstraintsList] = useState(['']);

  const handleAddConstraint = () => {
    setConstraintsList((prev) => [...prev, '']);
  };

  const handleRemoveConstraint = (index) => {
    setConstraintsList((prev) => prev.filter((_, i) => i !== index));
  };

  const handleConstraintChange = (index, value) => {
    setConstraintsList((prev) => {
      const updated = [...prev];
      updated[index] = value;
      return updated;
    });
  };

  // Helper: Find government session for a grade
  const getGovSessionForGrade = (grade) => {
    for (const [sessionId, grades] of Object.entries(includedGovSessions)) {
      if (grades && grades.includes(String(grade))) {
        return OFFICIAL_GOVERNMENT_CATALOG.find((s) => s.id === sessionId) || null;
      }
    }
    return null;
  };

  // Reset or initialize subjects when grades change
  const toggleGrade = (grade) => {
    if (selectedGrades.includes(grade)) {
      const next = selectedGrades.filter((g) => g !== grade);
      setSelectedGrades(next);
      const nextSubjects = { ...gradeSubjects };
      delete nextSubjects[grade];
      setGradeSubjects(nextSubjects);
    } else {
      setSelectedGrades([...selectedGrades, grade].sort((a, b) => Number(a) - Number(b)));
      setGradeSubjects({
        ...gradeSubjects,
        [grade]: gradeSubjects[grade] || 'Mathematics',
      });
    }
  };

  const handleSubjectChange = (grade, subject) => {
    setGradeSubjects({
      ...gradeSubjects,
      [grade]: subject,
    });
  };

  const activeDuration = durationMode === 'custom' ? Number(customDuration) || 0 : Number(durationMode);

  // Validation
  const isValid =
    selectedGrades.length > 0 &&
    selectedGrades.every((g) => gradeSubjects[g] && gradeSubjects[g].trim() !== '') &&
    activeDuration > 0;

  const handleSubmit = () => {
    if (!isValid) return;

    const payload = {
      grades: selectedGrades.map((g) => ({
        grade: g,
        subject: gradeSubjects[g] || 'Mathematics',
      })),
      grade_selection: selectedGrades.map((g) => ({
        grade: g,
        subject: gradeSubjects[g] || 'Mathematics',
      })),
      session_minutes: activeDuration,
      duration_minutes: activeDuration,
      resources: {
        tablets: Math.max(0, tablets),
        tv: tvAvailable,
        printer: printerAvailable,
        internet: internetConnected,
      },
      connectivity: internetConnected ? 'online' : 'offline',
      teacher_constraints: constraintsList.map((c) => c.trim()).filter((c) => c.length > 0),
      notes: constraintsList.map((c) => c.trim()).filter((c) => c.length > 0).join('; '),
      included_gov_sessions: includedGovSessions,
    };

    onClose();
    if (onStartSession) {
      onStartSession(payload);
    }
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6 overflow-y-auto">
      {/* Subtle dimming backdrop layer */}
      <div
        className="fixed inset-0 bg-black/40 dark:bg-black/65 backdrop-blur-sm transition-opacity duration-300"
        onClick={onClose}
      />

      {/* Large Centered Liquid Glass Modal Sheet */}
      <div className="relative w-full max-w-3xl liquid-glass-card rounded-[28px] p-6 sm:p-8 z-10 shadow-2xl transition-all duration-300 max-h-[90vh] flex flex-col">
        {/* Header */}
        <div className="flex items-center justify-between border-b border-black/[0.06] dark:border-white/[0.08] pb-4 mb-6 shrink-0">
          <div>
            <h2 className="text-xl font-semibold tracking-tight text-[#0A0A0A] dark:text-[#F5F5F5]">
              {t('session.modal_title')}
            </h2>
            <p className="text-xs text-[#6E6E6E] dark:text-[#A3A3A3] mt-0.5">
              Configure today's multi-grade classroom constraints & priorities.
            </p>
          </div>
          <button
            type="button"
            onClick={onClose}
            className="liquid-glass-btn-icon w-8 h-8 rounded-full flex items-center justify-center cursor-pointer text-[#6E6E6E] hover:text-[#0A0A0A] dark:hover:text-[#F5F5F5]"
          >
            <X className="w-4 h-4" />
          </button>
        </div>

        {/* Content Area */}
        <div className="flex-1 overflow-y-auto pr-1 space-y-7">
          {/* SECTION 1 — YOUR CLASSROOM */}
          <div className="space-y-3.5">
            <div>
              <h3 className="text-sm font-semibold text-[#0A0A0A] dark:text-[#F5F5F5]">
                {t('session.section1_title')}
              </h3>
              <p className="text-xs text-[#6E6E6E] dark:text-[#A3A3A3]">
                {t('session.section1_subtitle')}
              </p>
            </div>

            {/* Grade Cards (Multi-Select) */}
            <div className="grid grid-cols-4 sm:grid-cols-8 gap-2.5">
              {AVAILABLE_GRADES.map((g) => {
                const isSelected = selectedGrades.includes(g);
                return (
                  <button
                    key={g}
                    type="button"
                    onClick={() => toggleGrade(g)}
                    className={`h-12 rounded-xl flex flex-col items-center justify-center cursor-pointer transition-all duration-150 border select-none ${
                      isSelected
                        ? 'liquid-glass-nav-active border-black/20 dark:border-white/20 text-[#0A0A0A] dark:text-[#FFFFFF] font-bold shadow-xs'
                        : 'border-transparent text-[#6E6E6E] dark:text-[#A3A3A3] hover:text-[#0A0A0A] dark:hover:text-[#F5F5F5] hover:bg-white/40 dark:hover:bg-white/5'
                    }`}
                  >
                    <span className="text-[10px] uppercase tracking-wider opacity-70">Grade</span>
                    <span className="text-sm font-semibold leading-none">{g}</span>
                  </button>
                );
              })}
            </div>

            {/* Subject Selectors for Each Selected Grade */}
            {selectedGrades.length > 0 && (
              <div className="pt-2 grid grid-cols-1 sm:grid-cols-2 md:grid-cols-3 gap-3">
                {selectedGrades.map((g) => (
                  <div
                    key={g}
                    className="liquid-glass-control p-3 rounded-2xl flex items-center justify-between gap-2"
                  >
                    <span className="text-xs font-semibold text-[#0A0A0A] dark:text-[#F5F5F5] shrink-0">
                      Grade {g}
                    </span>
                    <select
                      value={gradeSubjects[g] || 'Mathematics'}
                      onChange={(e) => handleSubjectChange(g, e.target.value)}
                      className="bg-transparent text-xs font-medium text-[#0A0A0A] dark:text-[#F5F5F5] focus:outline-none cursor-pointer text-right"
                    >
                      {SUBJECT_OPTIONS.map((sub) => (
                        <option key={sub} value={sub} className="bg-white dark:bg-[#1A1C20] text-[#0A0A0A] dark:text-[#F5F5F5]">
                          {sub}
                        </option>
                      ))}
                    </select>
                  </div>
                ))}
              </div>
            )}
          </div>

          {/* SECTION 2 — TODAY'S GOVERNMENT SESSIONS */}
          {selectedGrades.length > 0 && (
            <div className="space-y-3 pt-2">
              <div className="flex items-center justify-between gap-3">
                <div>
                  <h3 className="text-sm font-semibold text-[#0A0A0A] dark:text-[#F5F5F5] flex items-center gap-1.5">
                    <Landmark className="w-4 h-4 text-[#0A0A0A] dark:text-[#F5F5F5]" />
                    <span>TODAY'S GOVERNMENT SESSIONS</span>
                  </h3>
                  <p className="text-xs text-[#6E6E6E] dark:text-[#A3A3A3]">
                    Pre-selected government sessions for your active grades.
                  </p>
                </div>
                <button
                  type="button"
                  onClick={() => {
                    onClose();
                    onNavigateToGovSessions();
                  }}
                  className="text-xs font-semibold text-emerald-600 dark:text-emerald-400 hover:underline cursor-pointer shrink-0"
                >
                  Edit Government Sessions
                </button>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-2 gap-2.5">
                {selectedGrades.map((g) => {
                  const govSess = getGovSessionForGrade(g);
                  return (
                    <div
                      key={g}
                      className={`p-3 rounded-2xl border text-xs flex items-center justify-between gap-2 ${
                        govSess
                          ? 'bg-emerald-500/10 border-emerald-500/30 text-[#0A0A0A] dark:text-[#F5F5F5]'
                          : 'liquid-glass-control text-[#6E6E6E] dark:text-[#A3A3A3]'
                      }`}
                    >
                      <div className="space-y-0.5 min-w-0 pr-1">
                        <div className="font-semibold text-[11px] text-[#0A0A0A] dark:text-[#F5F5F5] flex items-center gap-1">
                          <span>Grade {g}</span>
                          {govSess && <span className="text-emerald-600 dark:text-emerald-400 font-bold">✓</span>}
                        </div>
                        <div className="truncate text-[11px]">
                          {govSess ? govSess.title : 'No government session included'}
                        </div>
                      </div>
                      {govSess && (
                        <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-500/20 text-emerald-700 dark:text-emerald-300 shrink-0">
                          {govSess.durationMinutes}m · {govSess.requiredResource}
                        </span>
                      )}
                    </div>
                  );
                })}
              </div>
            </div>
          )}

          {/* SECTION 3 — TIME AVAILABLE */}
          <div className="space-y-3 pt-2">
            <h3 className="text-sm font-semibold text-[#0A0A0A] dark:text-[#F5F5F5]">
              {t('session.section2_title')}
            </h3>
            <div className="flex flex-wrap items-center gap-2">
              {PRESET_DURATIONS.map((dur) => {
                const isSelected = durationMode === dur;
                return (
                  <button
                    key={dur}
                    type="button"
                    onClick={() => setDurationMode(dur)}
                    className={`px-4 py-2 rounded-xl text-xs font-semibold transition-all cursor-pointer border ${
                      isSelected
                        ? 'liquid-glass-nav-active border-black/20 dark:border-white/20 text-[#0A0A0A] dark:text-[#FFFFFF]'
                        : 'border-transparent text-[#6E6E6E] dark:text-[#A3A3A3] hover:bg-white/40 dark:hover:bg-white/5'
                    }`}
                  >
                    {dur} min
                  </button>
                );
              })}
              <button
                type="button"
                onClick={() => setDurationMode('custom')}
                className={`px-4 py-2 rounded-xl text-xs font-semibold transition-all cursor-pointer border ${
                  durationMode === 'custom'
                    ? 'liquid-glass-nav-active border-black/20 dark:border-white/20 text-[#0A0A0A] dark:text-[#FFFFFF]'
                    : 'border-transparent text-[#6E6E6E] dark:text-[#A3A3A3] hover:bg-white/40 dark:hover:bg-white/5'
                }`}
              >
                Custom
              </button>
            </div>

            {durationMode === 'custom' && (
              <div className="flex items-center gap-3 pt-1">
                <input
                  type="number"
                  min="1"
                  max="300"
                  value={customDuration}
                  onChange={(e) => setCustomDuration(e.target.value)}
                  placeholder="Enter minutes"
                  className="w-32 px-3 py-1.5 rounded-xl border border-black/10 dark:border-white/15 bg-white/50 dark:bg-white/5 text-xs text-[#0A0A0A] dark:text-[#F5F5F5] focus:outline-none"
                />
                <span className="text-xs text-[#6E6E6E] dark:text-[#A3A3A3]">minutes</span>
              </div>
            )}
          </div>

          {/* SECTION 4 — TODAY'S RESOURCES */}
          <div className="space-y-3 pt-2">
            <div>
              <h3 className="text-sm font-semibold text-[#0A0A0A] dark:text-[#F5F5F5]">
                {t('session.section3_title')}
              </h3>
              <p className="text-xs text-[#6E6E6E] dark:text-[#A3A3A3]">
                {t('session.section3_subtitle')}
              </p>
            </div>

            <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
              {/* Resource 1: Tablets */}
              <div className="liquid-glass-control p-3.5 rounded-2xl flex items-center justify-between">
                <div className="flex items-center gap-2.5">
                  <Monitor className="w-4 h-4 text-[#6E6E6E] dark:text-[#A3A3A3]" />
                  <span className="text-xs font-medium text-[#0A0A0A] dark:text-[#F5F5F5]">
                    {t('session.resource_tablets')}
                  </span>
                </div>
                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    onClick={() => setTablets((prev) => Math.max(0, prev - 1))}
                    className="w-7 h-7 rounded-lg liquid-glass-btn-icon flex items-center justify-center cursor-pointer text-xs"
                  >
                    <Minus className="w-3 h-3" />
                  </button>
                  <span className="text-xs font-semibold w-5 text-center text-[#0A0A0A] dark:text-[#F5F5F5]">
                    {tablets}
                  </span>
                  <button
                    type="button"
                    onClick={() => setTablets((prev) => prev + 1)}
                    className="w-7 h-7 rounded-lg liquid-glass-btn-icon flex items-center justify-center cursor-pointer text-xs"
                  >
                    <Plus className="w-3 h-3" />
                  </button>
                </div>
              </div>

              {/* Resource 2: TV */}
              <div className="liquid-glass-control p-3.5 rounded-2xl flex items-center justify-between">
                <div className="flex items-center gap-2.5">
                  <Tv className="w-4 h-4 text-[#6E6E6E] dark:text-[#A3A3A3]" />
                  <span className="text-xs font-medium text-[#0A0A0A] dark:text-[#F5F5F5]">
                    {t('session.resource_tv')}
                  </span>
                </div>
                <button
                  type="button"
                  onClick={() => setTvAvailable((prev) => !prev)}
                  className={`px-3 py-1 rounded-xl text-[11px] font-semibold transition-colors cursor-pointer border ${
                    tvAvailable
                      ? 'bg-emerald-500/15 border-emerald-500/30 text-emerald-600 dark:text-emerald-400'
                      : 'bg-black/5 dark:bg-white/5 border-transparent text-[#6E6E6E]'
                  }`}
                >
                  {tvAvailable ? t('session.available') : t('session.not_available')}
                </button>
              </div>

              {/* Resource 3: Printer */}
              <div className="liquid-glass-control p-3.5 rounded-2xl flex items-center justify-between">
                <div className="flex items-center gap-2.5">
                  <Printer className="w-4 h-4 text-[#6E6E6E] dark:text-[#A3A3A3]" />
                  <span className="text-xs font-medium text-[#0A0A0A] dark:text-[#F5F5F5]">
                    {t('session.resource_printer')}
                  </span>
                </div>
                <button
                  type="button"
                  onClick={() => setPrinterAvailable((prev) => !prev)}
                  className={`px-3 py-1 rounded-xl text-[11px] font-semibold transition-colors cursor-pointer border ${
                    printerAvailable
                      ? 'bg-emerald-500/15 border-emerald-500/30 text-emerald-600 dark:text-emerald-400'
                      : 'bg-black/5 dark:bg-white/5 border-transparent text-[#6E6E6E]'
                  }`}
                >
                  {printerAvailable ? t('session.available') : t('session.not_available')}
                </button>
              </div>

              {/* Resource 4: Internet */}
              <div className="liquid-glass-control p-3.5 rounded-2xl flex items-center justify-between">
                <div className="flex items-center gap-2.5">
                  <Wifi className="w-4 h-4 text-[#6E6E6E] dark:text-[#A3A3A3]" />
                  <span className="text-xs font-medium text-[#0A0A0A] dark:text-[#F5F5F5]">
                    {t('session.resource_internet')}
                  </span>
                </div>
                <button
                  type="button"
                  onClick={() => setInternetConnected((prev) => !prev)}
                  className={`px-3 py-1 rounded-xl text-[11px] font-semibold transition-colors cursor-pointer border ${
                    internetConnected
                      ? 'bg-emerald-500/15 border-emerald-500/30 text-emerald-600 dark:text-emerald-400'
                      : 'bg-black/5 dark:bg-white/5 border-transparent text-[#6E6E6E]'
                  }`}
                >
                  {internetConnected ? t('session.connected') : t('session.offline')}
                </button>
              </div>
            </div>
          </div>

          {/* SECTION 4.5 — DYNAMIC CONTEXT & TEACHER CONSTRAINTS */}
          <div className="space-y-3 pt-2">
            <div>
              <h3 className="text-sm font-semibold text-[#0A0A0A] dark:text-[#F5F5F5]">
                Context & Teacher Constraints (Optional)
              </h3>
              <p className="text-xs text-[#6E6E6E] dark:text-[#A3A3A3]">
                Provide any specific student situations, topic focus, or exam constraints for today's session.
              </p>
            </div>

            <div className="space-y-2.5">
              {constraintsList.map((constraint, idx) => (
                <div key={idx} className="flex items-center gap-2">
                  <input
                    type="text"
                    value={constraint}
                    onChange={(e) => handleConstraintChange(idx, e.target.value)}
                    placeholder={
                      idx === 0
                        ? "e.g. Grade 3 is struggling with equivalent fractions."
                        : idx === 1
                        ? "e.g. Grade 5 has an exam tomorrow."
                        : "e.g. Internet is unreliable today."
                    }
                    className="flex-1 px-3.5 py-2.5 rounded-xl border border-black/10 dark:border-white/15 bg-white/50 dark:bg-white/5 text-xs text-[#0A0A0A] dark:text-[#F5F5F5] focus:outline-none focus:ring-2 focus:ring-amber-500/50"
                  />
                  {constraintsList.length > 1 && (
                    <button
                      type="button"
                      onClick={() => handleRemoveConstraint(idx)}
                      className="w-9 h-9 rounded-xl liquid-glass-btn-icon flex items-center justify-center cursor-pointer text-[#6E6E6E] hover:text-red-500 dark:hover:text-red-400 shrink-0 transition-colors"
                      title="Remove constraint"
                    >
                      <Minus className="w-4 h-4" />
                    </button>
                  )}
                </div>
              ))}

              <div className="pt-1">
                <button
                  type="button"
                  onClick={handleAddConstraint}
                  className="liquid-glass-btn-secondary px-3.5 py-2 rounded-xl text-xs font-medium text-[#0A0A0A] dark:text-[#F5F5F5] inline-flex items-center gap-1.5 cursor-pointer hover:border-black/20 dark:hover:border-white/20 transition-all"
                >
                  <Plus className="w-3.5 h-3.5 text-amber-500" />
                  <span>+ Add another</span>
                </button>
              </div>
            </div>
          </div>

          {/* SECTION 5 — SESSION SUMMARY */}
          <div className="p-4 rounded-2xl bg-black/[0.03] dark:bg-white/[0.03] border border-black/[0.05] dark:border-white/[0.08] space-y-2.5">
            <div className="text-[11px] font-semibold text-[#6E6E6E] dark:text-[#A3A3A3] uppercase tracking-wider">
              {t('session.section4_title')}
            </div>
            <div className="space-y-2 text-xs">
              <div className="space-y-1">
                <div className="font-semibold text-[#0A0A0A] dark:text-[#F5F5F5]">
                  Grades & Today's Plan:
                </div>
                <div className="space-y-1 pl-1">
                  {selectedGrades.map((g) => {
                    const govSess = getGovSessionForGrade(g);
                    return (
                      <div key={g} className="flex items-center gap-1.5 text-xs text-[#0A0A0A] dark:text-[#F5F5F5] flex-wrap">
                        <span className="font-semibold">Grade {g} ({gradeSubjects[g] || 'Mathematics'}):</span>
                        {govSess ? (
                          <span className="text-emerald-600 dark:text-emerald-400 font-medium">
                            → {govSess.title} ({govSess.durationMinutes} min · {govSess.requiredResource})
                          </span>
                        ) : (
                          <span className="text-[#6E6E6E] dark:text-[#A3A3A3]">
                            → Saarthi Activity
                          </span>
                        )}
                      </div>
                    );
                  })}
                </div>
              </div>

              <div className="text-[11px] text-[#6E6E6E] dark:text-[#A3A3A3] pt-2 border-t border-black/[0.05] dark:border-white/[0.07]">
                {activeDuration} minutes total · {tablets} tablets · {tvAvailable ? 'TV' : 'No TV'} ·{' '}
                {printerAvailable ? 'Printer' : 'No Printer'} ·{' '}
                {internetConnected ? 'Internet' : 'Offline'}
              </div>
            </div>
          </div>
        </div>

        {/* Modal Footer / Primary CTA */}
        <div className="pt-4 mt-4 border-t border-black/[0.06] dark:border-white/[0.08] flex items-center justify-end gap-3 shrink-0">
          <button
            type="button"
            onClick={onClose}
            className="liquid-glass-btn-secondary px-5 py-2.5 rounded-xl text-xs font-semibold cursor-pointer"
          >
            Cancel
          </button>
          <button
            type="button"
            onClick={handleSubmit}
            disabled={!isValid}
            className="liquid-glass-btn-primary px-6 py-2.5 rounded-xl text-xs font-semibold cursor-pointer disabled:opacity-40 disabled:cursor-not-allowed"
          >
            {t('session.start_btn')}
          </button>
        </div>
      </div>
    </div>
  );
}

