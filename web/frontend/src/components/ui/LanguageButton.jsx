import React, { useState, useEffect, useRef, useCallback } from 'react';
import { Check } from 'lucide-react';
import { useTranslation } from '../../i18n/i18n';
import { SUPPORTED_LANGUAGES } from '../../i18n/translations';

/**
 * LanguageButton Component
 * Horizontal rounded-rectangle Liquid Glass control (~100×40px) with cycling language animation.
 *
 * - Explicit local state `isLanguageMenuOpen` initialized to false.
 * - Continuously cycles through all supported languages (visual only — does not change app language).
 * - Clicking opens a Liquid Glass dropdown to select the actual language.
 * - Animation pauses while dropdown is open, showing the currently selected language.
 * - Click outside or Escape closes the dropdown and resumes animation.
 */
export default function LanguageButton({
  isOpen: propIsOpen,
  onToggle: propOnToggle,
  onClose: propOnClose
}) {
  const { language: selectedLanguage, setLanguage, t } = useTranslation();
  const [isLanguageMenuOpenLocal, setIsLanguageMenuOpenLocal] = useState(false);
  const isLanguageMenuOpen = propIsOpen !== undefined ? propIsOpen : isLanguageMenuOpenLocal;

  const [cycleIndex, setCycleIndex] = useState(0);
  const [isFading, setIsFading] = useState(false);
  const dropdownRef = useRef(null);
  const cycleTimerRef = useRef(null);

  // Cycle through languages visually (animation only)
  useEffect(() => {
    if (isLanguageMenuOpen) {
      // Pause animation when dropdown is open
      if (cycleTimerRef.current) {
        clearInterval(cycleTimerRef.current);
        cycleTimerRef.current = null;
      }
      return;
    }

    cycleTimerRef.current = setInterval(() => {
      setIsFading(true);
      setTimeout(() => {
        setCycleIndex((prev) => (prev + 1) % SUPPORTED_LANGUAGES.length);
        setIsFading(false);
      }, 350); // fade-out duration before switching text
    }, 1800);

    return () => {
      if (cycleTimerRef.current) {
        clearInterval(cycleTimerRef.current);
      }
    };
  }, [isLanguageMenuOpen]);

  // Click outside to close
  useEffect(() => {
    function handleClickOutside(event) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        if (propOnClose) propOnClose();
        else setIsLanguageMenuOpenLocal(false);
      }
    }
    if (isLanguageMenuOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [isLanguageMenuOpen, propOnClose]);

  // Escape to close
  useEffect(() => {
    function handleKeyDown(event) {
      if (event.key === 'Escape' && isLanguageMenuOpen) {
        if (propOnClose) propOnClose();
        else setIsLanguageMenuOpenLocal(false);
      }
    }
    if (isLanguageMenuOpen) {
      document.addEventListener('keydown', handleKeyDown);
    }
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [isLanguageMenuOpen, propOnClose]);

  const handleToggle = useCallback((e) => {
    e?.stopPropagation();
    if (propOnToggle) {
      propOnToggle();
    } else {
      setIsLanguageMenuOpenLocal((prev) => !prev);
    }
  }, [propOnToggle]);

  const handleMouseDown = useCallback((e) => {
    e?.stopPropagation();
  }, []);

  const handleSelect = useCallback((code, e) => {
    e?.stopPropagation();
    setLanguage(code);
    if (propOnClose) propOnClose();
    else setIsLanguageMenuOpenLocal(false);
  }, [setLanguage, propOnClose]);

  // Display: when dropdown is open, show currently selected language; otherwise cycle
  const displayLang = isLanguageMenuOpen
    ? SUPPORTED_LANGUAGES.find((l) => l.code === selectedLanguage)
    : SUPPORTED_LANGUAGES[cycleIndex];

  const displayLabel = displayLang?.nativeLabel || 'English';

  return (
    <div className="relative shrink-0" ref={dropdownRef} onMouseDown={handleMouseDown}>
      {/* Language Button — 112×42px rounded-rectangle Liquid Glass */}
      <button
        type="button"
        onClick={handleToggle}
        onMouseDown={handleMouseDown}
        aria-label={t('language.change')}
        title={t('language.change')}
        aria-expanded={isLanguageMenuOpen}
        className="liquid-glass-btn-icon flex items-center justify-center cursor-pointer shrink-0"
        style={{
          width: '112px',
          height: '42px',
          padding: '0 16px',
          boxSizing: 'border-box',
          borderRadius: '24px',
        }}
      >
        {/* Cycling language text — centered inside viewport */}
        <span
          className={`flex items-center justify-center w-full text-sm font-medium text-[#0A0A0A] dark:text-[#F5F5F5] leading-[1.3] select-none transition-opacity ease-out ${
            isFading && !isLanguageMenuOpen ? 'opacity-0' : 'opacity-100'
          }`}
          style={{
            whiteSpace: 'nowrap',
            transitionDuration: '350ms',
          }}
        >
          {displayLabel}
        </span>
      </button>

      {/* Liquid Glass Dropdown */}
      {isLanguageMenuOpen && (
        <div
          className="absolute top-full left-1/2 -translate-x-1/2 mt-2.5 w-48 liquid-glass-dropdown rounded-2xl p-2 z-50 text-left"
          role="menu"
          aria-label={t('language.title')}
        >
          {/* Header */}
          <div className="px-3 py-2 border-b border-black/[0.05] dark:border-white/[0.08] mb-1">
            <span className="text-[11px] font-semibold tracking-wider text-[#6E6E6E] dark:text-[#A3A3A3] uppercase">
              {t('language.title')}
            </span>
          </div>

          {/* Language Options */}
          <div className="space-y-0.5">
            {SUPPORTED_LANGUAGES.map((lang) => {
              const isSelected = lang.code === selectedLanguage;
              return (
                <button
                  key={lang.code}
                  type="button"
                  role="menuitem"
                  onClick={() => handleSelect(lang.code)}
                  className={`w-full flex items-center gap-2.5 px-3 py-2 text-xs rounded-xl transition-colors duration-100 text-left font-medium cursor-pointer select-none ${
                    isSelected
                      ? 'text-[#0A0A0A] dark:text-[#F5F5F5] bg-white/60 dark:bg-white/10'
                      : 'text-[#6E6E6E] dark:text-[#A3A3A3] hover:text-[#0A0A0A] dark:hover:text-[#F5F5F5] hover:bg-white/50 dark:hover:bg-white/8'
                  }`}
                >
                  {/* Checkmark or spacer */}
                  <div className="w-3.5 h-3.5 flex items-center justify-center shrink-0">
                    {isSelected && (
                      <Check className="w-3.5 h-3.5 text-[#0A0A0A] dark:text-[#F5F5F5]" />
                    )}
                  </div>
                  <span>{lang.nativeLabel}</span>
                </button>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}

