import React, { useState, useRef, useEffect } from 'react';
import { ChevronDown, Settings, LogOut } from 'lucide-react';
import { useTranslation } from '../../i18n/i18n';

/**
 * Reusable TeacherProfile Control Component
 * Avatar + Teacher Name + Email + Dropdown Chevron + Frosted Glass Popover
 * Dropdown labels translated via centralized i18n system.
 */
export default function TeacherProfile({
  name = "Sarah Jenkins",
  email = "teacher@school.edu",
  avatarUrl = null,
  isOpen: propIsOpen,
  onToggle: propOnToggle,
  onClose: propOnClose
}) {
  const [isProfileOpenLocal, setIsProfileOpenLocal] = useState(false);
  const isProfileOpen = propIsOpen !== undefined ? propIsOpen : isProfileOpenLocal;

  const dropdownRef = useRef(null);
  const { t } = useTranslation();

  // Click outside to close
  useEffect(() => {
    function handleClickOutside(event) {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        if (propOnClose) propOnClose();
        else setIsProfileOpenLocal(false);
      }
    }
    if (isProfileOpen) {
      document.addEventListener('mousedown', handleClickOutside);
    }
    return () => document.removeEventListener('mousedown', handleClickOutside);
  }, [isProfileOpen, propOnClose]);

  // Escape key to close
  useEffect(() => {
    function handleKeyDown(event) {
      if (event.key === 'Escape' && isProfileOpen) {
        if (propOnClose) propOnClose();
        else setIsProfileOpenLocal(false);
      }
    }
    if (isProfileOpen) {
      document.addEventListener('keydown', handleKeyDown);
    }
    return () => document.removeEventListener('keydown', handleKeyDown);
  }, [isProfileOpen, propOnClose]);

  const handleButtonClick = (e) => {
    e?.stopPropagation();
    if (propOnToggle) {
      propOnToggle();
    } else {
      setIsProfileOpenLocal((prev) => !prev);
    }
  };

  const handleMouseDown = (e) => {
    e?.stopPropagation();
  };

  const handleMenuItemClick = (e) => {
    e?.stopPropagation();
    if (propOnClose) propOnClose();
    else setIsProfileOpenLocal(false);
  };

  return (
    <div className="relative shrink-0" ref={dropdownRef} onMouseDown={handleMouseDown}>
      <button
        type="button"
        onClick={handleButtonClick}
        onMouseDown={handleMouseDown}
        aria-expanded={isProfileOpen}
        className="flex items-center gap-3 p-1.5 pr-2.5 rounded-xl border border-transparent hover:border-white/70 dark:hover:border-white/10 hover:bg-white/50 dark:hover:bg-white/5 transition-all duration-150 cursor-pointer select-none text-left"
      >
        {/* Avatar */}
        <div className="w-8 h-8 rounded-full bg-[#0A0A0A] dark:bg-white text-white dark:text-[#0A0A0A] flex items-center justify-center font-medium text-xs shadow-xs overflow-hidden shrink-0 border border-black/10 dark:border-white/20">
          {avatarUrl ? (
            <img src={avatarUrl} alt={name} className="w-full h-full object-cover" />
          ) : (
            name.split(' ').map(n => n[0]).join('').substring(0, 2).toUpperCase()
          )}
        </div>

        {/* Info */}
        <div className="hidden sm:block leading-tight">
          <div className="text-xs font-semibold text-[#0A0A0A] dark:text-[#F5F5F5] truncate max-w-[130px]">
            {name}
          </div>
          <div className="text-[11px] text-[#6E6E6E] dark:text-[#A3A3A3] truncate max-w-[130px]">
            {email}
          </div>
        </div>

        <ChevronDown className="w-3.5 h-3.5 text-[#6E6E6E] dark:text-[#A3A3A3] shrink-0 ml-0.5" />
      </button>

      {/* Frosted Liquid Glass Profile Popover */}
      {isProfileOpen && (
        <div className="absolute top-full right-0 mt-2.5 w-56 liquid-glass-card rounded-2xl p-2 z-50 text-left">
          <div className="px-3 py-2.5 border-b border-black/[0.05] dark:border-white/[0.08] mb-1">
            <div className="text-xs font-semibold text-[#0A0A0A] dark:text-[#F5F5F5]">{name}</div>
            <div className="text-[11px] text-[#6E6E6E] dark:text-[#A3A3A3]">{email}</div>
          </div>

          <div className="space-y-0.5">
            <button
              type="button"
              onClick={handleMenuItemClick}
              className="w-full flex items-center gap-2.5 px-3 py-2 text-xs text-[#0A0A0A] dark:text-[#F5F5F5] hover:bg-white/60 dark:hover:bg-white/10 rounded-xl transition-colors text-left font-medium cursor-pointer"
            >
              <Settings className="w-3.5 h-3.5 text-[#6E6E6E] dark:text-[#A3A3A3]" />
              <span>{t('profile.settings')}</span>
            </button>
            <button
              type="button"
              onClick={handleMenuItemClick}
              className="w-full flex items-center gap-2.5 px-3 py-2 text-xs text-[#6E6E6E] dark:text-[#A3A3A3] hover:text-[#0A0A0A] dark:hover:text-[#F5F5F5] hover:bg-white/60 dark:hover:bg-white/10 rounded-xl transition-colors text-left font-medium cursor-pointer"
            >
              <LogOut className="w-3.5 h-3.5 text-[#6E6E6E] dark:text-[#A3A3A3]" />
              <span>{t('profile.sign_out')}</span>
            </button>
          </div>
        </div>
      )}
    </div>
  );
}

