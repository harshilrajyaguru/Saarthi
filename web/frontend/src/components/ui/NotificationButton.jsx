import React, { useState, useRef, useEffect } from 'react';
import { Bell } from 'lucide-react';
import { useTranslation } from '../../i18n/i18n';

/**
 * Reusable NotificationButton Component
 * Apple iOS-style elevated 40px x 40px circular Liquid Glass control with Bell icon & frosted popover.
 * All labels translated via centralized i18n system.
 */
export default function NotificationButton({
  hasUnread = true,
  isOpen: propIsOpen,
  onToggle: propOnToggle,
  onClose: propOnClose
}) {
  const [isNotificationOpenLocal, setIsNotificationOpenLocal] = useState(false);
  const isNotificationOpen = propIsOpen !== undefined ? propIsOpen : isNotificationOpenLocal;

  const popoverRef = useRef(null);
  const { t } = useTranslation();

  // Click outside to close
  useEffect(() => {
    function handleClickOutside(event) {
      if (popoverRef.current && !popoverRef.current.contains(event.target)) {
        if (propOnClose) propOnClose();
        else setIsNotificationOpenLocal(false);
      }
    }
    if (isNotificationOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [isNotificationOpen, propOnClose]);

  // Escape key to close
  useEffect(() => {
    function handleKeyDown(event) {
      if (event.key === 'Escape' && isNotificationOpen) {
        if (propOnClose) propOnClose();
        else setIsNotificationOpenLocal(false);
      }
    }
    if (isNotificationOpen) {
      document.addEventListener('keydown', handleKeyDown);
    }
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [isNotificationOpen, propOnClose]);

  const handleButtonClick = (e) => {
    e?.stopPropagation();
    if (propOnToggle) {
      propOnToggle();
    } else {
      setIsNotificationOpenLocal((prev) => !prev);
    }
  };

  const handleMouseDown = (e) => {
    e?.stopPropagation();
  };

  return (
    <div className="relative shrink-0" ref={popoverRef} onMouseDown={handleMouseDown}>
      <button
        type="button"
        onClick={handleButtonClick}
        onMouseDown={handleMouseDown}
        title={t('notifications.title')}
        aria-label={t('notifications.title')}
        aria-expanded={isNotificationOpen}
        className="w-10 h-10 rounded-full liquid-glass-btn-icon flex items-center justify-center cursor-pointer relative"
      >
        <Bell className="w-4 h-4 text-[#0A0A0A] dark:text-[#F5F5F5]" />
        {/* Subtle unread indicator dot */}
        {hasUnread && (
          <span className="absolute top-2.5 right-2.5 w-1.5 h-1.5 bg-[#0A0A0A] dark:bg-white rounded-full ring-2 ring-white/80 dark:ring-[#1E1E1E]" />
        )}
      </button>

      {/* Frosted Liquid Glass Notification Popover */}
      {isNotificationOpen && (
        <div className="absolute top-full right-0 mt-2.5 w-72 liquid-glass-card rounded-2xl p-4 z-50 text-left">
          <div className="flex items-center justify-between border-b border-black/[0.05] dark:border-white/[0.08] pb-2.5 mb-3">
            <span className="text-[11px] font-semibold tracking-wider text-[#6E6E6E] dark:text-[#A3A3A3] uppercase">
              {t('notifications.title')}
            </span>
            <span className="text-[11px] text-[#6E6E6E] dark:text-[#A3A3A3]">{t('notifications.new_count', { count: 0 })}</span>
          </div>

          <div className="py-6 text-center">
            <p className="text-xs text-[#6E6E6E] dark:text-[#A3A3A3] font-medium">
              {t('notifications.empty')}
            </p>
          </div>
        </div>
      )}
    </div>
  );
}

