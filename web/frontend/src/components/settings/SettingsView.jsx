import React, { useState, useEffect } from 'react';
import { Sun, Moon, Globe, Bell, Sliders, User, Info, CheckCircle2 } from 'lucide-react';
import { useTranslation } from '../../i18n/i18n';
import { SUPPORTED_LANGUAGES } from '../../i18n/translations';

export default function SettingsView() {
  const { language, setLanguage } = useTranslation();

  // Existing theme state initialization
  const [theme, setTheme] = useState(() => {
    try {
      const stored = localStorage.getItem('saarthi-theme');
      if (stored === 'dark') return 'dark';
    } catch (e) {}
    return 'light';
  });

  // Notifications State
  const [sessionReminders, setSessionReminders] = useState(true);
  const [classroomUpdates, setClassroomUpdates] = useState(true);
  const [importantAlerts, setImportantAlerts] = useState(true);

  // Classroom Defaults State
  const [defaultDuration, setDefaultDuration] = useState(40);
  const [defaultGrade, setDefaultGrade] = useState('3');

  // Toast notification
  const [toastMessage, setToastMessage] = useState(null);

  // Effect to synchronize existing theme system with documentElement
  useEffect(() => {
    const root = document.documentElement;
    if (theme === 'dark') {
      root.classList.add('dark');
      root.classList.remove('light');
      try {
        localStorage.setItem('saarthi-theme', 'dark');
      } catch (e) {}
    } else {
      root.classList.add('light');
      root.classList.remove('dark');
      try {
        localStorage.setItem('saarthi-theme', 'light');
      } catch (e) {}
    }
  }, [theme]);

  const handleProfileClick = () => {
    setToastMessage('Profile settings ready');
    setTimeout(() => setToastMessage(null), 3000);
  };

  return (
    <div className="space-y-7 max-w-4xl relative">
      {/* Toast Notification */}
      {toastMessage && (
        <div className="fixed bottom-6 right-6 z-50 liquid-glass-card rounded-2xl px-4 py-3 shadow-xl border border-emerald-500/30 flex items-center gap-3 animate-fade-in">
          <CheckCircle2 className="w-5 h-5 text-emerald-500 shrink-0" />
          <div className="text-xs font-semibold text-[#0A0A0A] dark:text-[#F5F5F5]">
            {toastMessage}
          </div>
        </div>
      )}

      {/* Page Header */}
      <div className="space-y-1">
        <h1 className="text-2xl font-bold tracking-tight text-[#0A0A0A] dark:text-[#F5F5F5] font-heading">
          Settings
        </h1>
        <p className="text-xs sm:text-sm text-[#6E6E6E] dark:text-[#A3A3A3]">
          Manage your Saarthi preferences.
        </p>
      </div>

      <div className="space-y-6">
        {/* SECTION 1 — APPEARANCE */}
        <div className="liquid-glass-card rounded-[24px] p-6 space-y-4 border border-black/[0.08] dark:border-white/[0.10]">
          <div className="flex items-center gap-2 border-b border-black/[0.05] dark:border-white/[0.07] pb-3">
            <Sun className="w-4 h-4 text-[#0A0A0A] dark:text-[#F5F5F5]" />
            <h2 className="text-xs font-bold uppercase tracking-wider text-[#0A0A0A] dark:text-[#F5F5F5]">
              Appearance
            </h2>
          </div>

          <div className="flex items-center justify-between gap-4 flex-wrap text-xs">
            <div>
              <div className="font-semibold text-[#0A0A0A] dark:text-[#F5F5F5]">Theme</div>
              <div className="text-[#6E6E6E] dark:text-[#A3A3A3] text-[11px]">
                Choose your preferred visual theme.
              </div>
            </div>

            <div className="flex items-center gap-2">
              <button
                type="button"
                onClick={() => setTheme('light')}
                className={`px-4 py-2 rounded-xl text-xs font-semibold inline-flex items-center gap-1.5 transition-all cursor-pointer border ${
                  theme === 'light'
                    ? 'liquid-glass-nav-active border-black/20 text-[#0A0A0A] font-bold shadow-xs'
                    : 'liquid-glass-btn-secondary opacity-70 hover:opacity-100'
                }`}
              >
                <Sun className="w-3.5 h-3.5" />
                <span>Light</span>
              </button>
              <button
                type="button"
                onClick={() => setTheme('dark')}
                className={`px-4 py-2 rounded-xl text-xs font-semibold inline-flex items-center gap-1.5 transition-all cursor-pointer border ${
                  theme === 'dark'
                    ? 'liquid-glass-nav-active border-white/20 text-[#FFFFFF] font-bold shadow-xs'
                    : 'liquid-glass-btn-secondary opacity-70 hover:opacity-100'
                }`}
              >
                <Moon className="w-3.5 h-3.5" />
                <span>Dark</span>
              </button>
            </div>
          </div>
        </div>

        {/* SECTION 2 — LANGUAGE */}
        <div className="liquid-glass-card rounded-[24px] p-6 space-y-4 border border-black/[0.08] dark:border-white/[0.10]">
          <div className="flex items-center gap-2 border-b border-black/[0.05] dark:border-white/[0.07] pb-3">
            <Globe className="w-4 h-4 text-[#0A0A0A] dark:text-[#F5F5F5]" />
            <h2 className="text-xs font-bold uppercase tracking-wider text-[#0A0A0A] dark:text-[#F5F5F5]">
              Language
            </h2>
          </div>

          <div className="flex items-center justify-between gap-4 flex-wrap text-xs">
            <div>
              <div className="font-semibold text-[#0A0A0A] dark:text-[#F5F5F5]">Interface Language</div>
              <div className="text-[#6E6E6E] dark:text-[#A3A3A3] text-[11px]">
                Select the primary display language for Saarthi.
              </div>
            </div>

            <select
              value={language}
              onChange={(e) => setLanguage(e.target.value)}
              className="bg-white/80 dark:bg-white/10 text-xs font-semibold text-[#0A0A0A] dark:text-[#F5F5F5] px-3.5 py-2 rounded-xl border border-black/10 dark:border-white/15 focus:outline-none cursor-pointer"
            >
              {SUPPORTED_LANGUAGES.map((lang) => (
                <option key={lang.code} value={lang.code} className="bg-white dark:bg-[#1C1E22] text-[#0A0A0A] dark:text-[#F5F5F5]">
                  {lang.label} ({lang.nativeLabel})
                </option>
              ))}
            </select>
          </div>
        </div>

        {/* SECTION 3 — NOTIFICATIONS */}
        <div className="liquid-glass-card rounded-[24px] p-6 space-y-4 border border-black/[0.08] dark:border-white/[0.10]">
          <div className="flex items-center gap-2 border-b border-black/[0.05] dark:border-white/[0.07] pb-3">
            <Bell className="w-4 h-4 text-[#0A0A0A] dark:text-[#F5F5F5]" />
            <h2 className="text-xs font-bold uppercase tracking-wider text-[#0A0A0A] dark:text-[#F5F5F5]">
              Notifications
            </h2>
          </div>

          <div className="space-y-3.5 divide-y divide-black/[0.04] dark:divide-white/[0.06] text-xs">
            <div className="pt-1 flex items-center justify-between gap-4">
              <div>
                <div className="font-semibold text-[#0A0A0A] dark:text-[#F5F5F5]">Session reminders</div>
                <div className="text-[#6E6E6E] dark:text-[#A3A3A3] text-[11px]">Remind teacher before scheduled session start time</div>
              </div>
              <button
                type="button"
                onClick={() => setSessionReminders(!sessionReminders)}
                className={`w-11 h-6 rounded-full transition-colors p-1 cursor-pointer flex items-center ${
                  sessionReminders ? 'bg-emerald-500 justify-end' : 'bg-black/20 dark:bg-white/20 justify-start'
                }`}
              >
                <div className="w-4 h-4 rounded-full bg-white shadow-xs" />
              </button>
            </div>

            <div className="pt-3 flex items-center justify-between gap-4">
              <div>
                <div className="font-semibold text-[#0A0A0A] dark:text-[#F5F5F5]">Classroom updates</div>
                <div className="text-[#6E6E6E] dark:text-[#A3A3A3] text-[11px]">Receive updates on student completion</div>
              </div>
              <button
                type="button"
                onClick={() => setClassroomUpdates(!classroomUpdates)}
                className={`w-11 h-6 rounded-full transition-colors p-1 cursor-pointer flex items-center ${
                  classroomUpdates ? 'bg-emerald-500 justify-end' : 'bg-black/20 dark:bg-white/20 justify-start'
                }`}
              >
                <div className="w-4 h-4 rounded-full bg-white shadow-xs" />
              </button>
            </div>

            <div className="pt-3 flex items-center justify-between gap-4">
              <div>
                <div className="font-semibold text-[#0A0A0A] dark:text-[#F5F5F5]">Important alerts</div>
                <div className="text-[#6E6E6E] dark:text-[#A3A3A3] text-[11px]">Alerts when resource constraints arise</div>
              </div>
              <button
                type="button"
                onClick={() => setImportantAlerts(!importantAlerts)}
                className={`w-11 h-6 rounded-full transition-colors p-1 cursor-pointer flex items-center ${
                  importantAlerts ? 'bg-emerald-500 justify-end' : 'bg-black/20 dark:bg-white/20 justify-start'
                }`}
              >
                <div className="w-4 h-4 rounded-full bg-white shadow-xs" />
              </button>
            </div>
          </div>
        </div>

        {/* SECTION 4 — CLASSROOM DEFAULTS */}
        <div className="liquid-glass-card rounded-[24px] p-6 space-y-4 border border-black/[0.08] dark:border-white/[0.10]">
          <div className="flex items-center gap-2 border-b border-black/[0.05] dark:border-white/[0.07] pb-3">
            <Sliders className="w-4 h-4 text-[#0A0A0A] dark:text-[#F5F5F5]" />
            <h2 className="text-xs font-bold uppercase tracking-wider text-[#0A0A0A] dark:text-[#F5F5F5]">
              Classroom Defaults
            </h2>
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 text-xs">
            <div className="space-y-1">
              <label htmlFor="default-duration" className="font-semibold text-[#0A0A0A] dark:text-[#F5F5F5]">
                Default session duration
              </label>
              <select
                id="default-duration"
                value={defaultDuration}
                onChange={(e) => setDefaultDuration(Number(e.target.value))}
                className="w-full bg-white/80 dark:bg-white/10 text-xs font-semibold text-[#0A0A0A] dark:text-[#F5F5F5] px-3.5 py-2 rounded-xl border border-black/10 dark:border-white/15 focus:outline-none cursor-pointer"
              >
                {[30, 40, 45, 60, 90].map((dur) => (
                  <option key={dur} value={dur} className="bg-white dark:bg-[#1C1E22] text-[#0A0A0A] dark:text-[#F5F5F5]">
                    {dur} minutes
                  </option>
                ))}
              </select>
            </div>

            <div className="space-y-1">
              <label htmlFor="default-grade" className="font-semibold text-[#0A0A0A] dark:text-[#F5F5F5]">
                Default grade
              </label>
              <select
                id="default-grade"
                value={defaultGrade}
                onChange={(e) => setDefaultGrade(e.target.value)}
                className="w-full bg-white/80 dark:bg-white/10 text-xs font-semibold text-[#0A0A0A] dark:text-[#F5F5F5] px-3.5 py-2 rounded-xl border border-black/10 dark:border-white/15 focus:outline-none cursor-pointer"
              >
                {['1', '2', '3', '4', '5', '6', '7', '8'].map((g) => (
                  <option key={g} value={g} className="bg-white dark:bg-[#1C1E22] text-[#0A0A0A] dark:text-[#F5F5F5]">
                    Grade {g}
                  </option>
                ))}
              </select>
            </div>
          </div>
        </div>

        {/* SECTION 5 — ACCOUNT */}
        <div className="liquid-glass-card rounded-[24px] p-6 space-y-4 border border-black/[0.08] dark:border-white/[0.10]">
          <div className="flex items-center gap-2 border-b border-black/[0.05] dark:border-white/[0.07] pb-3">
            <User className="w-4 h-4 text-[#0A0A0A] dark:text-[#F5F5F5]" />
            <h2 className="text-xs font-bold uppercase tracking-wider text-[#0A0A0A] dark:text-[#F5F5F5]">
              Account
            </h2>
          </div>

          <div className="flex items-center justify-between gap-4 flex-wrap text-xs">
            <div>
              <div className="font-semibold text-[#0A0A0A] dark:text-[#F5F5F5] text-sm">
                Sarah Jenkins
              </div>
              <div className="text-[#6E6E6E] dark:text-[#A3A3A3]">
                teacher@school.edu
              </div>
            </div>

            <button
              type="button"
              onClick={handleProfileClick}
              className="liquid-glass-btn-secondary px-4 py-2 rounded-xl text-xs font-semibold cursor-pointer"
            >
              Profile Settings
            </button>
          </div>
        </div>

        {/* SECTION 6 — ABOUT */}
        <div className="liquid-glass-card rounded-[24px] p-6 space-y-2 border border-black/[0.08] dark:border-white/[0.10]">
          <div className="flex items-center gap-2 border-b border-black/[0.05] dark:border-white/[0.07] pb-3">
            <Info className="w-4 h-4 text-[#0A0A0A] dark:text-[#F5F5F5]" />
            <h2 className="text-xs font-bold uppercase tracking-wider text-[#0A0A0A] dark:text-[#F5F5F5]">
              About
            </h2>
          </div>

          <div className="pt-1 flex items-center justify-between gap-4 text-xs">
            <div>
              <div className="font-bold text-[#0A0A0A] dark:text-[#F5F5F5] text-sm font-heading">
                Saarthi
              </div>
              <div className="text-[#6E6E6E] dark:text-[#A3A3A3]">
                AI Classroom Copilot
              </div>
            </div>

            <span className="px-3 py-1 rounded-full text-xs font-semibold bg-black/5 dark:bg-white/10 text-[#6E6E6E] dark:text-[#A3A3A3]">
              Version 1.0
            </span>
          </div>
        </div>
      </div>
    </div>
  );
}
