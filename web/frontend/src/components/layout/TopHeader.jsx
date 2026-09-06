import React, { useState, useEffect } from 'react';
import ThemeToggle from '../ui/ThemeToggle';
import NotificationButton from '../ui/NotificationButton';
import TeacherProfile from '../ui/TeacherProfile';
import LanguageButton from '../ui/LanguageButton';

/**
 * Reusable TopHeader Component
 * Apple iOS-style Liquid Glass floating toolbar with sharp typography hierarchy and elevated glass controls.
 * Manages explicit local popover states for Language, Notification, and Teacher Profile.
 */
export default function TopHeader({ title = "Dashboard", activeTab = "dashboard" }) {
  const [isLanguageMenuOpen, setIsLanguageMenuOpen] = useState(false);
  const [isNotificationOpen, setIsNotificationOpen] = useState(false);
  const [isProfileOpen, setIsProfileOpen] = useState(false);

  // Close all popovers whenever activeTab/route changes
  useEffect(() => {
    setIsLanguageMenuOpen(false);
    setIsNotificationOpen(false);
    setIsProfileOpen(false);
  }, [activeTab]);

  const handleToggleLanguage = () => {
    setIsLanguageMenuOpen((prev) => {
      const next = !prev;
      if (next) {
        setIsNotificationOpen(false);
        setIsProfileOpen(false);
      }
      return next;
    });
  };

  const handleToggleNotification = () => {
    setIsNotificationOpen((prev) => {
      const next = !prev;
      if (next) {
        setIsLanguageMenuOpen(false);
        setIsProfileOpen(false);
      }
      return next;
    });
  };

  const handleToggleProfile = () => {
    setIsProfileOpen((prev) => {
      const next = !prev;
      if (next) {
        setIsLanguageMenuOpen(false);
        setIsNotificationOpen(false);
      }
      return next;
    });
  };

  const handleCloseLanguage = () => setIsLanguageMenuOpen(false);
  const handleCloseNotification = () => setIsNotificationOpen(false);
  const handleCloseProfile = () => setIsProfileOpen(false);

  return (
    <header className="liquid-glass-header h-16 flex items-center justify-between px-8 sticky top-0 z-20 shrink-0 transition-colors duration-300">
      {/* Left: Page Title */}
      <div className="relative z-[1]">
        <h1 className="text-2xl font-semibold text-[#0A0A0A] dark:text-[#F5F5F5] tracking-tight">
          {title}
        </h1>
      </div>

      {/* Right: Controls -> [ Language ] [ Theme Toggle ] [ Notification ] [ Teacher Profile ] */}
      <div className="flex items-center gap-3 relative z-[1]">
        <LanguageButton
          isOpen={isLanguageMenuOpen}
          onToggle={handleToggleLanguage}
          onClose={handleCloseLanguage}
        />
        <ThemeToggle />
        <NotificationButton
          isOpen={isNotificationOpen}
          onToggle={handleToggleNotification}
          onClose={handleCloseNotification}
        />
        <div className="h-4 w-px bg-black/[0.08] dark:bg-white/[0.10] hidden sm:block mx-1" />
        <TeacherProfile
          isOpen={isProfileOpen}
          onToggle={handleToggleProfile}
          onClose={handleCloseProfile}
        />
      </div>
    </header>
  );
}

