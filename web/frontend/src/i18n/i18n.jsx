import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import translations from './translations';

const STORAGE_KEY = 'saarthi-language';
const DEFAULT_LANGUAGE = 'en';

/**
 * Language Context
 * Provides current language and translation function to all components.
 */
const LanguageContext = createContext({
  language: DEFAULT_LANGUAGE,
  setLanguage: () => {},
  t: (key) => key,
});

/**
 * Translate a key using the current language.
 * Falls back to English, then to the raw key if not found.
 * Supports simple interpolation: t('key', { count: 5 }) replaces {count} in the string.
 */
function translate(lang, key, params = {}) {
  const langDict = translations[lang] || translations[DEFAULT_LANGUAGE];
  let value = langDict[key] ?? translations[DEFAULT_LANGUAGE]?.[key] ?? key;

  // Simple interpolation
  if (params && typeof value === 'string') {
    Object.entries(params).forEach(([paramKey, paramValue]) => {
      value = value.replace(`{${paramKey}}`, paramValue);
    });
  }

  return value;
}

/**
 * LanguageProvider
 * Wraps the application to provide i18n context.
 * Persists language selection to localStorage under 'saarthi-language'.
 * Defaults to 'en' if no stored value exists.
 */
export function LanguageProvider({ children }) {
  const [language, setLanguageState] = useState(() => {
    try {
      const stored = localStorage.getItem(STORAGE_KEY);
      if (stored && translations[stored]) {
        return stored;
      }
    } catch (e) {
      // Storage unavailable
    }
    return DEFAULT_LANGUAGE;
  });

  const setLanguage = useCallback((lang) => {
    if (translations[lang]) {
      setLanguageState(lang);
      try {
        localStorage.setItem(STORAGE_KEY, lang);
      } catch (e) {
        // Storage unavailable
      }
    }
  }, []);

  const t = useCallback((key, params) => {
    return translate(language, key, params);
  }, [language]);

  // Set lang attribute on html element for accessibility
  useEffect(() => {
    document.documentElement.setAttribute('lang', language);
  }, [language]);

  return (
    <LanguageContext.Provider value={{ language, setLanguage, t }}>
      {children}
    </LanguageContext.Provider>
  );
}

/**
 * useTranslation hook
 * Returns { language, setLanguage, t } from LanguageContext.
 */
export function useTranslation() {
  return useContext(LanguageContext);
}

export default LanguageContext;
