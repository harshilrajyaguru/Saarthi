import React, { useState, useEffect } from 'react';
import { Sun, Moon } from 'lucide-react';
import { useTranslation } from '../../i18n/i18n';

/**
 * Reusable ThemeToggle Component
 * Apple-style elevated 40px x 40px circular glass control for toggling Light/Dark theme.
 * Defaults strictly to 'light' unless 'dark' is stored under 'saarthi-theme'.
 * Completely ignores OS/browser prefers-color-scheme.
 * Button labels translated via centralized i18n system.
 */
export default function ThemeToggle() {
  const [theme, setTheme] = useState(() => {
    try {
      const stored = localStorage.getItem('saarthi-theme');
      if (stored === 'dark') {
        return 'dark';
      }
    } catch (e) {
      // Storage unavailable fallback
    }
    return 'light';
  });

  const { t } = useTranslation();

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

  const toggleTheme = () => {
    setTheme(prev => (prev === 'light' ? 'dark' : 'light'));
  };

  const isDark = theme === 'dark';

  return (
    <button
      type="button"
      onClick={toggleTheme}
      title={isDark ? t('theme.switch_light') : t('theme.switch_dark')}
      aria-label={isDark ? t('theme.switch_light') : t('theme.switch_dark')}
      className="w-10 h-10 rounded-full liquid-glass-btn-icon flex items-center justify-center cursor-pointer shrink-0"
    >
      {isDark ? (
        <Sun className="w-4 h-4 text-[#F5F5F5]" />
      ) : (
        <Moon className="w-4 h-4 text-[#0A0A0A]" />
      )}
    </button>
  );
}
