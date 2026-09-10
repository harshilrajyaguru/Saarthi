import React, { useState, useMemo } from 'react';
import { Landmark, Calendar, Clock, Monitor, X, ExternalLink, Filter, AlertCircle, Eye, Check } from 'lucide-react';

/**
 * CURATED OFFICIAL GOVERNMENT SESSION CATALOG
 * Discovered and verified from official government portals:
 * - DIKSHA (https://diksha.gov.in/)
 * - PM eVIDYA / NCERT ePathshala (https://epathshala.ncert.gov.in/)
 */
export const OFFICIAL_GOVERNMENT_CATALOG = [
  {
    id: 'gov_evidya_math_4',
    title: 'PM eVIDYA Class 4 Mathematics: Fractions & Decimals',
    description: 'Official PM eVIDYA TV broadcast class covering visual fraction models and introduction to decimal parts.',
    source: 'DIKSHA / PM eVIDYA (Government of India)',
    sourceUrl: 'https://diksha.gov.in/search/Library/1?id=ekstep_ncert_k-12&primaryCategory=explanation%20content&se_boards=ncert&se_mediums=english&&selectedTab=all',
    thumbnail: 'https://obj.diksha.gov.in/ntp-content-production/homepage/prod/assets/newimages/icon_videos.png',
    gradeRange: 'Grades 3–5',
    eligibleGrades: ['3', '4', '5'],
    subject: 'Mathematics',
    durationMinutes: 25,
    schedule: 'Every Tuesday',
    requiredResource: 'TV required',
    contentType: 'TV Classes',
    language: 'English',
  },
  {
    id: 'gov_evidya_evs_5',
    title: 'PM eVIDYA Class 5 EVS: Natural Ecosystems & Biodiversity',
    description: 'Government-sponsored instructional video exploring plant adaptation, soil types, and regional biodiversity.',
    source: 'DIKSHA / NCERT (Government of India)',
    sourceUrl: 'https://diksha.gov.in/search/Library/1?id=ekstep_ncert_k-12&primaryCategory=explanation%20content&se_boards=ncert&se_mediums=english&&selectedTab=all',
    thumbnail: 'https://obj.diksha.gov.in/ntp-content-production/homepage/prod/assets/newimages/icon_videos.png',
    gradeRange: 'Grades 4–6',
    eligibleGrades: ['4', '5', '6'],
    subject: 'Environmental Studies',
    durationMinutes: 30,
    schedule: 'Every Wednesday',
    requiredResource: 'TV required',
    contentType: 'TV Classes',
    language: 'English',
  },
  {
    id: 'gov_diksha_virtuallabs_science',
    title: 'DIKSHA Virtual Science Lab: Light, Shadows & Reflections',
    description: 'Interactive NCERT virtual laboratory module allowing students to manipulate light sources and shadow distances.',
    source: 'DIKSHA Virtual Labs (Ministry of Education)',
    sourceUrl: 'https://diksha.gov.in/virtuallabs.html',
    thumbnail: 'https://obj.diksha.gov.in/ntp-content-production/homepage/prod/assets/newimages/icon_interactive_content.png',
    gradeRange: 'Grades 6–8',
    eligibleGrades: ['6', '7', '8'],
    subject: 'Science',
    durationMinutes: 20,
    schedule: 'First Friday of every month',
    requiredResource: 'Tablet required',
    contentType: 'Interactive Content',
    language: 'English',
  },
  {
    id: 'gov_epathshala_english_3',
    title: 'NCERT Class 3 English: Reading & Vocabulary Hour',
    description: 'NCERT digital textbook audio-assisted reading session for vocabulary enhancement and sentence structure.',
    source: 'DIKSHA / ePathshala (NCERT)',
    sourceUrl: 'https://diksha.gov.in/resources?id=ekstep_ncert_k-12&board=NCERT&medium=English&selectedTab=textbook',
    thumbnail: 'https://obj.diksha.gov.in/ntp-content-production/homepage/prod/assets/newimages/icon_textbooks.png',
    gradeRange: 'Grades 1–5',
    eligibleGrades: ['1', '2', '3', '4', '5'],
    subject: 'English',
    durationMinutes: 30,
    schedule: 'Every Thursday',
    requiredResource: 'No special resources',
    contentType: 'Digital Textbook',
    language: 'English',
  },
  {
    id: 'gov_nipun_fln_math',
    title: 'Nipun Bharat FLN: Foundational Numeracy & Arithmetic',
    description: 'Nipun Bharat foundational literacy and numeracy printed practice sheets for primary grade arithmetic.',
    source: 'DIKSHA / Nipun Bharat Mission',
    sourceUrl: 'https://diksha.gov.in/',
    thumbnail: 'https://diksha.gov.in/assets/newimages/img_logo_diksha.png',
    gradeRange: 'Grades 1–3',
    eligibleGrades: ['1', '2', '3'],
    subject: 'Mathematics',
    durationMinutes: 20,
    schedule: 'Daily',
    requiredResource: 'Printer required',
    contentType: 'Worksheets',
    language: 'Hindi',
  },
  {
    id: 'gov_evidya_sst_6',
    title: 'PM eVIDYA Class 6 Social Science: Earth & Solar System',
    description: 'Educational broadcast on planetary orbits, seasonal shifts, and satellite rotation produced by NCERT.',
    source: 'DIKSHA / PM eVIDYA',
    sourceUrl: 'https://diksha.gov.in/search/Library/1?id=ekstep_ncert_k-12&primaryCategory=explanation%20content&se_boards=ncert&se_mediums=english&&selectedTab=all',
    thumbnail: 'https://obj.diksha.gov.in/ntp-content-production/homepage/prod/assets/newimages/icon_videos.png',
    gradeRange: 'Grades 5–8',
    eligibleGrades: ['5', '6', '7', '8'],
    subject: 'Social Studies',
    durationMinutes: 25,
    schedule: 'Every Monday',
    requiredResource: 'TV required',
    contentType: 'TV Classes',
    language: 'English',
  },
];

const ALL_GRADES = ['1', '2', '3', '4', '5', '6', '7', '8'];
const SUBJECT_OPTIONS = ['Mathematics', 'Science', 'English', 'Social Studies', 'Environmental Studies'];
const CONTENT_TYPE_OPTIONS = ['TV Classes', 'Interactive Content', 'Digital Textbook', 'Worksheets'];
const LANGUAGE_OPTIONS = ['English', 'Hindi'];

/**
 * Thumbnail component with fallback handling
 */
function ImageWithFallback({ src, alt, className }) {
  const [hasError, setHasError] = useState(false);

  if (hasError || !src) {
    return (
      <div className={`bg-gradient-to-br from-black/10 to-black/5 dark:from-white/10 dark:to-white/5 flex flex-col items-center justify-center p-4 border-b border-black/[0.06] dark:border-white/[0.08] ${className}`}>
        <Landmark className="w-8 h-8 text-[#0A0A0A] dark:text-[#F5F5F5] opacity-60 mb-1" />
        <span className="text-[10px] font-semibold tracking-wider text-[#6E6E6E] dark:text-[#A3A3A3] uppercase">
          DIKSHA · Official Content
        </span>
      </div>
    );
  }

  return (
    <div className={`relative overflow-hidden bg-black/5 dark:bg-white/5 border-b border-black/[0.06] dark:border-white/[0.08] ${className}`}>
      <img
        src={src}
        alt={alt}
        onError={() => setHasError(true)}
        className="w-full h-full object-cover transition-transform duration-300 hover:scale-105"
      />
      <div className="absolute top-2 right-2 px-2 py-0.5 rounded-full bg-black/60 backdrop-blur-xs text-white text-[10px] font-semibold">
        DIKSHA
      </div>
    </div>
  );
}

/**
 * GovernmentSessionView Component
 */
export default function GovernmentSessionView({
  includedSessions = {},
  onUpdateInclusion = () => {},
  isSessionActive = false,
}) {

  // Filters State
  const [gradeFilter, setGradeFilter] = useState('');
  const [subjectFilter, setSubjectFilter] = useState('');
  const [contentTypeFilter, setContentTypeFilter] = useState('');
  const [languageFilter, setLanguageFilter] = useState('');

  // Active Preview Drawer / Modal
  const [previewSession, setPreviewSession] = useState(null);

  // Active Grade Inclusion Modal
  const [activeModalSession, setActiveModalSession] = useState(null);
  const [modalSelectedGrades, setModalSelectedGrades] = useState([]);

  // Active Removal Confirmation Session
  const [sessionToRemove, setSessionToRemove] = useState(null);

  // Filter Catalog Items
  const filteredCatalog = useMemo(() => {
    return OFFICIAL_GOVERNMENT_CATALOG.filter((item) => {
      if (gradeFilter && !item.eligibleGrades.includes(gradeFilter)) return false;
      if (subjectFilter && item.subject !== subjectFilter) return false;
      if (contentTypeFilter && item.contentType !== contentTypeFilter) return false;
      if (languageFilter && item.language !== languageFilter) return false;
      return true;
    });
  }, [gradeFilter, subjectFilter, contentTypeFilter, languageFilter]);

  // Modal actions
  const handleOpenAddModal = (session) => {
    if (isSessionActive) return;
    setActiveModalSession(session);
    setModalSelectedGrades(includedSessions[session.id] || []);
  };

  const handleCloseAddModal = () => {
    setActiveModalSession(null);
    setModalSelectedGrades([]);
  };

  const handleToggleModalGrade = (grade) => {
    if (modalSelectedGrades.includes(grade)) {
      setModalSelectedGrades(modalSelectedGrades.filter((g) => g !== grade));
    } else {
      setModalSelectedGrades([...modalSelectedGrades, grade].sort((a, b) => Number(a) - Number(b)));
    }
  };

  const handleSaveModal = () => {
    if (!activeModalSession) return;
    if (modalSelectedGrades.length > 0) {
      onUpdateInclusion(activeModalSession.id, modalSelectedGrades);
      handleCloseAddModal();
    }
  };

  const handleOpenRemoveConfirm = (session) => {
    if (isSessionActive) return;
    setSessionToRemove(session);
  };

  const handleConfirmRemove = () => {
    if (sessionToRemove) {
      onUpdateInclusion(sessionToRemove.id, []);
      setSessionToRemove(null);
    }
  };

  const includedCount = Object.keys(includedSessions).filter(
    (id) => (includedSessions[id] || []).length > 0
  ).length;

  return (
    <div className="space-y-7">
      {/* Page Header */}
      <div className="space-y-1">
        <h1 className="text-2xl font-bold tracking-tight text-[#0A0A0A] dark:text-[#F5F5F5] font-heading">
          Government Session
        </h1>
        <p className="text-xs sm:text-sm text-[#6E6E6E] dark:text-[#A3A3A3]">
          Pre-session planning input: Select government sessions to include in today's classroom.
        </p>
      </div>

      {/* ACTIVE SESSION LOCK BANNER */}
      {isSessionActive && (
        <div className="liquid-glass-card p-4 rounded-2xl border border-amber-500/30 bg-amber-500/[0.04] flex items-center gap-3">
          <AlertCircle className="w-5 h-5 text-amber-500 shrink-0" />
          <div className="text-xs text-[#0A0A0A] dark:text-[#F5F5F5]">
            <span className="font-semibold">Your classroom session is already in progress.</span>{' '}
            <span className="text-[#6E6E6E] dark:text-[#A3A3A3]">
              Government sessions can be added before starting the next session.
            </span>
          </div>
        </div>
      )}

      {/* TODAY'S PLAN SECTION */}
      <div className="liquid-glass-card rounded-[24px] p-5 space-y-4 border border-black/[0.08] dark:border-white/[0.10]">
        <div className="flex items-center justify-between gap-3 border-b border-black/[0.05] dark:border-white/[0.07] pb-3">
          <div className="flex items-center gap-2">
            <Landmark className="w-4.5 h-4.5 text-[#0A0A0A] dark:text-[#F5F5F5]" />
            <h2 className="text-xs font-bold uppercase tracking-wider text-[#0A0A0A] dark:text-[#F5F5F5]">
              TODAY'S PLAN
            </h2>
          </div>

          <span className="px-3 py-1 rounded-full text-xs font-semibold bg-black/5 dark:bg-white/10 text-[#0A0A0A] dark:text-[#F5F5F5]">
            {includedCount} {includedCount === 1 ? 'included' : 'included'}
          </span>
        </div>

        {includedCount === 0 ? (
          <div className="py-2 space-y-1">
            <div className="text-xs font-semibold text-[#0A0A0A] dark:text-[#F5F5F5]">
              No government sessions included today.
            </div>
            <p className="text-xs text-[#6E6E6E] dark:text-[#A3A3A3]">
              Add a government session below if you want to include it in today's classroom.
            </p>
          </div>
        ) : (
          <div className="space-y-2.5">
            {OFFICIAL_GOVERNMENT_CATALOG.filter(
              (s) => (includedSessions[s.id] || []).length > 0
            ).map((s) => {
              const selectedG = includedSessions[s.id];
              return (
                <div
                  key={s.id}
                  className="flex flex-col sm:flex-row sm:items-center justify-between p-3.5 rounded-xl bg-white/60 dark:bg-white/[0.04] border border-black/[0.05] dark:border-white/[0.07] gap-3 text-xs"
                >
                  <div className="space-y-1 min-w-0">
                    <div className="font-semibold text-[#0A0A0A] dark:text-[#F5F5F5] flex items-center gap-1.5">
                      <Check className="w-3.5 h-3.5 text-emerald-500 shrink-0" />
                      <span className="truncate">{s.title}</span>
                    </div>
                    <div className="text-[11px] text-[#6E6E6E] dark:text-[#A3A3A3] flex items-center gap-2 flex-wrap">
                      <span className="font-semibold text-[#0A0A0A] dark:text-[#F5F5F5]">
                        Grades {selectedG.join(', ')}
                      </span>
                      <span>·</span>
                      <span>{s.durationMinutes} min</span>
                      <span>·</span>
                      <span>{s.requiredResource}</span>
                    </div>
                  </div>

                  {!isSessionActive && (
                    <div className="flex items-center gap-2 shrink-0 self-end sm:self-center">
                      <button
                        type="button"
                        onClick={() => handleOpenAddModal(s)}
                        className="liquid-glass-btn-secondary px-3 py-1.5 rounded-xl text-xs font-semibold cursor-pointer"
                      >
                        Edit Grades
                      </button>
                      <button
                        type="button"
                        onClick={() => handleOpenRemoveConfirm(s)}
                        className="liquid-glass-btn-secondary px-3 py-1.5 rounded-xl text-xs font-semibold text-red-600 dark:text-red-400 hover:bg-red-500/10 cursor-pointer"
                      >
                        Remove
                      </button>
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* LIGHTWEIGHT CATALOG FILTERS */}
      <div className="flex flex-wrap items-center gap-3 p-4 rounded-2xl bg-black/[0.02] dark:bg-white/[0.03] border border-black/[0.05] dark:border-white/[0.08]">
        <div className="flex items-center gap-1.5 text-xs font-semibold text-[#6E6E6E] dark:text-[#A3A3A3] mr-1">
          <Filter className="w-3.5 h-3.5" />
          <span>Filters:</span>
        </div>

        {/* Grade Filter */}
        <select
          value={gradeFilter}
          onChange={(e) => setGradeFilter(e.target.value)}
          className="bg-white/80 dark:bg-white/10 text-xs font-medium text-[#0A0A0A] dark:text-[#F5F5F5] px-3 py-1.5 rounded-xl border border-black/10 dark:border-white/15 focus:outline-none cursor-pointer"
        >
          <option value="">All Grades</option>
          {ALL_GRADES.map((g) => (
            <option key={g} value={g} className="bg-white dark:bg-[#1C1E22] text-[#0A0A0A] dark:text-[#F5F5F5]">
              Grade {g}
            </option>
          ))}
        </select>

        {/* Subject Filter */}
        <select
          value={subjectFilter}
          onChange={(e) => setSubjectFilter(e.target.value)}
          className="bg-white/80 dark:bg-white/10 text-xs font-medium text-[#0A0A0A] dark:text-[#F5F5F5] px-3 py-1.5 rounded-xl border border-black/10 dark:border-white/15 focus:outline-none cursor-pointer"
        >
          <option value="">All Subjects</option>
          {SUBJECT_OPTIONS.map((sub) => (
            <option key={sub} value={sub} className="bg-white dark:bg-[#1C1E22] text-[#0A0A0A] dark:text-[#F5F5F5]">
              {sub}
            </option>
          ))}
        </select>

        {/* Content Type Filter */}
        <select
          value={contentTypeFilter}
          onChange={(e) => setContentTypeFilter(e.target.value)}
          className="bg-white/80 dark:bg-white/10 text-xs font-medium text-[#0A0A0A] dark:text-[#F5F5F5] px-3 py-1.5 rounded-xl border border-black/10 dark:border-white/15 focus:outline-none cursor-pointer"
        >
          <option value="">All Content Types</option>
          {CONTENT_TYPE_OPTIONS.map((ct) => (
            <option key={ct} value={ct} className="bg-white dark:bg-[#1C1E22] text-[#0A0A0A] dark:text-[#F5F5F5]">
              {ct}
            </option>
          ))}
        </select>

        {/* Language Filter */}
        <select
          value={languageFilter}
          onChange={(e) => setLanguageFilter(e.target.value)}
          className="bg-white/80 dark:bg-white/10 text-xs font-medium text-[#0A0A0A] dark:text-[#F5F5F5] px-3 py-1.5 rounded-xl border border-black/10 dark:border-white/15 focus:outline-none cursor-pointer"
        >
          <option value="">All Languages</option>
          {LANGUAGE_OPTIONS.map((lang) => (
            <option key={lang} value={lang} className="bg-white dark:bg-[#1C1E22] text-[#0A0A0A] dark:text-[#F5F5F5]">
              {lang}
            </option>
          ))}
        </select>

        {/* Reset Filters button */}
        {(gradeFilter || subjectFilter || contentTypeFilter || languageFilter) && (
          <button
            type="button"
            onClick={() => {
              setGradeFilter('');
              setSubjectFilter('');
              setContentTypeFilter('');
              setLanguageFilter('');
            }}
            className="text-xs text-[#6E6E6E] dark:text-[#A3A3A3] hover:text-[#0A0A0A] dark:hover:text-[#F5F5F5] underline cursor-pointer ml-auto"
          >
            Clear Filters
          </button>
        )}
      </div>

      {/* CATALOG CARDS GRID */}
      {filteredCatalog.length === 0 ? (
        <div className="liquid-glass-card rounded-[24px] p-8 text-center space-y-2 border border-black/[0.08] dark:border-white/[0.10]">
          <h3 className="text-base font-bold text-[#0A0A0A] dark:text-[#F5F5F5] font-heading">
            No sessions found
          </h3>
          <p className="text-xs text-[#6E6E6E] dark:text-[#A3A3A3]">
            Try selecting another grade, subject, or content type.
          </p>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredCatalog.map((session) => {
            const selectedGrades = includedSessions[session.id] || [];
            const isIncluded = selectedGrades.length > 0;

            return (
              <div
                key={session.id}
                className={`liquid-glass-card rounded-[24px] overflow-hidden border flex flex-col justify-between transition-all duration-200 ${
                  isIncluded
                    ? 'border-emerald-500/30 bg-emerald-500/[0.02] dark:bg-emerald-500/[0.03]'
                    : 'border-black/[0.08] dark:border-white/[0.12]'
                }`}
              >
                <div>
                  {/* Thumbnail / Header */}
                  <div
                    className="cursor-pointer relative"
                    onClick={() => setPreviewSession(session)}
                  >
                    <ImageWithFallback
                      src={session.thumbnail}
                      alt={session.title}
                      className="h-36"
                    />
                    <button
                      type="button"
                      onClick={(e) => {
                        e.stopPropagation();
                        setPreviewSession(session);
                      }}
                      className="absolute bottom-2 left-2 px-2.5 py-1 rounded-xl bg-black/60 hover:bg-black/80 backdrop-blur-xs text-white text-[11px] font-medium flex items-center gap-1 cursor-pointer transition-colors"
                    >
                      <Eye className="w-3 h-3" />
                      <span>Preview</span>
                    </button>
                  </div>

                  {/* Body Content */}
                  <div className="p-5 space-y-3.5">
                    {/* Header Label & Included Badge */}
                    <div className="flex items-center justify-between gap-2">
                      <span className="text-[10px] font-semibold tracking-wider text-[#6E6E6E] dark:text-[#A3A3A3] uppercase truncate">
                        {session.source}
                      </span>
                      {isIncluded && (
                        <span className="px-2 py-0.5 rounded-full text-[10px] font-semibold bg-emerald-500/15 text-emerald-700 dark:text-emerald-300 border border-emerald-500/30 shrink-0">
                          ✓ Added · Grades {selectedGrades.join(', ')}
                        </span>
                      )}
                    </div>

                    {/* Title & Description */}
                    <div className="space-y-1">
                      <h3
                        onClick={() => setPreviewSession(session)}
                        className="text-base font-bold tracking-tight text-[#0A0A0A] dark:text-[#F5F5F5] font-heading cursor-pointer hover:underline line-clamp-2"
                      >
                        {session.title}
                      </h3>
                      <p className="text-xs text-[#6E6E6E] dark:text-[#A3A3A3] line-clamp-2 leading-relaxed">
                        {session.description}
                      </p>
                    </div>

                    {/* Metadata Row */}
                    <div className="pt-2 grid grid-cols-2 gap-2 text-xs text-[#6E6E6E] dark:text-[#A3A3A3]">
                      <div className="flex items-center gap-1.5 truncate">
                        <Clock className="w-3.5 h-3.5 shrink-0 text-[#0A0A0A] dark:text-[#F5F5F5]" />
                        <span>{session.durationMinutes} min</span>
                      </div>
                      <div className="flex items-center gap-1.5 truncate">
                        <Calendar className="w-3.5 h-3.5 shrink-0 text-[#0A0A0A] dark:text-[#F5F5F5]" />
                        <span className="truncate">{session.schedule}</span>
                      </div>
                      <div className="flex items-center gap-1.5 truncate">
                        <span className="font-semibold text-[#0A0A0A] dark:text-[#F5F5F5]">For:</span>
                        <span>{session.gradeRange}</span>
                      </div>
                      <div className="flex items-center gap-1.5 truncate">
                        <Monitor className="w-3.5 h-3.5 shrink-0 text-[#0A0A0A] dark:text-[#F5F5F5]" />
                        <span className="truncate">{session.requiredResource}</span>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Card Actions Footer */}
                <div className="p-5 pt-3 border-t border-black/[0.06] dark:border-white/[0.08] flex items-center justify-between gap-2">
                  {isIncluded ? (
                    <div className="flex items-center gap-2 flex-1">
                      <button
                        type="button"
                        onClick={() => handleOpenAddModal(session)}
                        disabled={isSessionActive}
                        className="liquid-glass-btn-secondary flex-1 py-2 rounded-xl text-xs font-semibold cursor-pointer disabled:opacity-40"
                      >
                        Edit Grades
                      </button>
                      <button
                        type="button"
                        onClick={() => handleOpenRemoveConfirm(session)}
                        disabled={isSessionActive}
                        className="liquid-glass-btn-secondary px-3 py-2 rounded-xl text-xs font-semibold text-red-600 dark:text-red-400 hover:bg-red-500/10 cursor-pointer disabled:opacity-40"
                      >
                        Remove
                      </button>
                    </div>
                  ) : (
                    <button
                      type="button"
                      onClick={() => handleOpenAddModal(session)}
                      disabled={isSessionActive}
                      className="liquid-glass-btn-primary flex-1 py-2 rounded-xl text-xs font-semibold cursor-pointer disabled:opacity-40"
                    >
                      Add to Today's Session
                    </button>
                  )}

                  {/* View Official Source Link */}
                  <a
                    href={session.sourceUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="liquid-glass-btn-secondary p-2 rounded-xl text-xs font-medium cursor-pointer shrink-0 flex items-center justify-center text-[#6E6E6E] hover:text-[#0A0A0A] dark:hover:text-[#F5F5F5]"
                    title="View Official Source on DIKSHA / Government Portal"
                  >
                    <ExternalLink className="w-4 h-4" />
                  </a>
                </div>
              </div>
            );
          })}
        </div>
      )}

      {/* CONTENT PREVIEW SHEET / MODAL */}
      {previewSession && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6 overflow-y-auto">
          <div
            className="fixed inset-0 bg-black/40 dark:bg-black/65 backdrop-blur-sm transition-opacity duration-300"
            onClick={() => setPreviewSession(null)}
          />

          <div className="relative w-full max-w-lg liquid-glass-card rounded-[28px] overflow-hidden z-10 shadow-2xl space-y-0">
            {/* Preview Image Header */}
            <div className="relative h-48">
              <ImageWithFallback
                src={previewSession.thumbnail}
                alt={previewSession.title}
                className="h-full"
              />
              <button
                type="button"
                onClick={() => setPreviewSession(null)}
                className="absolute top-3 right-3 w-8 h-8 rounded-full bg-black/60 backdrop-blur-xs text-white flex items-center justify-center cursor-pointer hover:bg-black/80"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* Preview Body Details */}
            <div className="p-6 space-y-4 text-xs">
              <div className="space-y-1">
                <span className="text-[10px] font-semibold tracking-wider text-[#6E6E6E] dark:text-[#A3A3A3] uppercase">
                  {previewSession.source}
                </span>
                <h3 className="text-xl font-bold tracking-tight text-[#0A0A0A] dark:text-[#F5F5F5] font-heading">
                  {previewSession.title}
                </h3>
              </div>

              <p className="text-[#6E6E6E] dark:text-[#A3A3A3] leading-relaxed">
                {previewSession.description}
              </p>

              <div className="grid grid-cols-2 gap-3 p-3 rounded-xl bg-black/[0.03] dark:bg-white/[0.03] border border-black/[0.05] dark:border-white/[0.08]">
                <div>
                  <span className="font-semibold text-[#0A0A0A] dark:text-[#F5F5F5]">Subject: </span>
                  <span className="text-[#6E6E6E] dark:text-[#A3A3A3]">{previewSession.subject}</span>
                </div>
                <div>
                  <span className="font-semibold text-[#0A0A0A] dark:text-[#F5F5F5]">Eligible Grades: </span>
                  <span className="text-[#6E6E6E] dark:text-[#A3A3A3]">{previewSession.gradeRange}</span>
                </div>
                <div>
                  <span className="font-semibold text-[#0A0A0A] dark:text-[#F5F5F5]">Duration: </span>
                  <span className="text-[#6E6E6E] dark:text-[#A3A3A3]">{previewSession.durationMinutes} min</span>
                </div>
                <div>
                  <span className="font-semibold text-[#0A0A0A] dark:text-[#F5F5F5]">Language: </span>
                  <span className="text-[#6E6E6E] dark:text-[#A3A3A3]">{previewSession.language}</span>
                </div>
                <div className="col-span-2">
                  <span className="font-semibold text-[#0A0A0A] dark:text-[#F5F5F5]">Resource Required: </span>
                  <span className="text-[#6E6E6E] dark:text-[#A3A3A3]">{previewSession.requiredResource}</span>
                </div>
              </div>

              {/* Preview Footer CTAs */}
              <div className="pt-3 flex items-center justify-end gap-2.5">
                <a
                  href={previewSession.sourceUrl}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="liquid-glass-btn-secondary px-4 py-2.5 rounded-xl text-xs font-semibold inline-flex items-center gap-1.5 cursor-pointer"
                >
                  <span>View on DIKSHA ↗</span>
                </a>

                {!isSessionActive && (
                  <button
                    type="button"
                    onClick={() => {
                      const sess = previewSession;
                      setPreviewSession(null);
                      handleOpenAddModal(sess);
                    }}
                    className="liquid-glass-btn-primary px-5 py-2.5 rounded-xl text-xs font-semibold cursor-pointer"
                  >
                    Add to Today's Session
                  </button>
                )}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* GRADE SELECTION SHEET / MODAL */}
      {activeModalSession && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6 overflow-y-auto">
          <div
            className="fixed inset-0 bg-black/40 dark:bg-black/65 backdrop-blur-sm transition-opacity duration-300"
            onClick={handleCloseAddModal}
          />

          <div className="relative w-full max-w-lg liquid-glass-card rounded-[28px] p-6 sm:p-7 z-10 shadow-2xl space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between border-b border-black/[0.06] dark:border-white/[0.08] pb-4">
              <div>
                <h3 className="text-lg font-bold tracking-tight text-[#0A0A0A] dark:text-[#F5F5F5] font-heading">
                  {(includedSessions[activeModalSession.id] || []).length > 0 ? "Edit Grade Assignment" : "Add to Today's Session"}
                </h3>
                <p className="text-xs font-semibold text-[#0A0A0A] dark:text-[#F5F5F5] mt-1">
                  {activeModalSession.title}
                </p>
                <p className="text-[11px] text-[#6E6E6E] dark:text-[#A3A3A3]">
                  {activeModalSession.durationMinutes} min · {activeModalSession.requiredResource}
                </p>
              </div>
              <button
                type="button"
                onClick={handleCloseAddModal}
                className="liquid-glass-btn-icon w-8 h-8 rounded-full flex items-center justify-center cursor-pointer text-[#6E6E6E]"
              >
                <X className="w-4 h-4" />
              </button>
            </div>

            {/* GRADE SELECTION GRID */}
            <div className="space-y-4">
              <div className="text-xs font-semibold text-[#0A0A0A] dark:text-[#F5F5F5]">
                Select eligible grades to receive this session:
              </div>

              <div className="grid grid-cols-2 sm:grid-cols-4 gap-2.5">
                {ALL_GRADES.map((g) => {
                  const isEligible = activeModalSession.eligibleGrades.includes(g);
                  const isSelected = modalSelectedGrades.includes(g);

                  if (!isEligible) {
                    return (
                      <div
                        key={g}
                        className="h-14 p-2 rounded-xl border border-black/[0.04] dark:border-white/[0.04] bg-black/[0.02] dark:bg-white/[0.02] opacity-40 select-none flex flex-col items-center justify-center text-center cursor-not-allowed"
                      >
                        <span className="text-xs font-medium text-[#6E6E6E] dark:text-[#A3A3A3]">
                          Grade {g}
                        </span>
                        <span className="text-[9px] text-[#8E8E8E] leading-tight">
                          Not eligible
                        </span>
                      </div>
                    );
                  }

                  return (
                    <button
                      key={g}
                      type="button"
                      onClick={() => handleToggleModalGrade(g)}
                      className={`h-14 rounded-xl flex flex-col items-center justify-center cursor-pointer transition-all duration-150 border select-none ${
                        isSelected
                          ? 'liquid-glass-nav-active border-black/20 dark:border-white/20 text-[#0A0A0A] dark:text-[#FFFFFF] font-bold shadow-xs'
                          : 'border-black/10 dark:border-white/10 text-[#6E6E6E] dark:text-[#A3A3A3] hover:text-[#0A0A0A] dark:hover:text-[#F5F5F5] hover:bg-white/40 dark:hover:bg-white/5'
                      }`}
                    >
                      <div className="flex items-center gap-1.5">
                        {isSelected && (
                          <span className="text-xs text-emerald-600 dark:text-emerald-400 font-bold">
                            ✓
                          </span>
                        )}
                        <span className="text-xs font-semibold">Grade {g}</span>
                      </div>
                    </button>
                  );
                })}
              </div>

              {/* Footer Confirmation Bar */}
              <div className="pt-4 border-t border-black/[0.06] dark:border-white/[0.08] flex items-center justify-between gap-3">
                <div className="text-xs text-[#6E6E6E] dark:text-[#A3A3A3]">
                  {modalSelectedGrades.length > 0 ? (
                    <span className="font-semibold text-[#0A0A0A] dark:text-[#F5F5F5]">
                      {modalSelectedGrades.length} {modalSelectedGrades.length === 1 ? 'grade' : 'grades'} selected (Grade {modalSelectedGrades.join(', ')})
                    </span>
                  ) : (
                    <span>Select at least 1 grade</span>
                  )}
                </div>

                <div className="flex items-center gap-2">
                  <button
                    type="button"
                    onClick={handleCloseAddModal}
                    className="liquid-glass-btn-secondary px-4 py-2.5 rounded-xl text-xs font-semibold cursor-pointer"
                  >
                    Cancel
                  </button>

                  <button
                    type="button"
                    onClick={handleSaveModal}
                    disabled={modalSelectedGrades.length === 0}
                    className="liquid-glass-btn-primary px-5 py-2.5 rounded-xl text-xs font-semibold cursor-pointer disabled:opacity-40 disabled:cursor-not-allowed"
                  >
                    {(includedSessions[activeModalSession.id] || []).length > 0
                      ? 'Save Changes'
                      : "Add to Today's Session"}
                  </button>
                </div>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* REMOVAL CONFIRMATION MODAL */}
      {sessionToRemove && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6 overflow-y-auto">
          <div
            className="fixed inset-0 bg-black/40 dark:bg-black/65 backdrop-blur-sm transition-opacity duration-300"
            onClick={() => setSessionToRemove(null)}
          />

          <div className="relative w-full max-w-md liquid-glass-card rounded-[28px] p-6 sm:p-7 z-10 shadow-2xl space-y-5">
            <div className="flex items-center gap-2.5 text-amber-600 dark:text-amber-400 font-bold text-base font-heading">
              <AlertCircle className="w-5 h-5 text-amber-500 shrink-0" />
              <span>Remove from today's session?</span>
            </div>

            <p className="text-xs text-[#6E6E6E] dark:text-[#A3A3A3] leading-relaxed">
              <span className="font-semibold text-[#0A0A0A] dark:text-[#F5F5F5]">{sessionToRemove.title}</span> will no longer be included for Grades {(includedSessions[sessionToRemove.id] || []).join(', ')}.
            </p>

            <div className="pt-2 flex items-center justify-end gap-2.5 border-t border-black/[0.06] dark:border-white/[0.08]">
              <button
                type="button"
                onClick={() => setSessionToRemove(null)}
                className="liquid-glass-btn-secondary px-4 py-2.5 rounded-xl text-xs font-semibold cursor-pointer"
              >
                Keep
              </button>
              <button
                type="button"
                onClick={handleConfirmRemove}
                className="liquid-glass-btn-secondary px-5 py-2.5 rounded-xl text-xs font-semibold text-red-600 dark:text-red-400 hover:bg-red-500/10 border-red-500/20 cursor-pointer"
              >
                Remove
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
