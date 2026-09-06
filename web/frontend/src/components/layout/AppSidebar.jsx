import React from 'react';
import { LayoutDashboard, Activity, UserCheck, Landmark, Clock, Layers, Settings, HelpCircle } from 'lucide-react';
import PeacockLogo from '../brand/PeacockLogo';
import { useTranslation } from '../../i18n/i18n';

const MAIN_NAV_ITEMS = [
  { id: 'dashboard', labelKey: 'nav.dashboard', icon: LayoutDashboard },
  { id: 'activity', labelKey: 'nav.activity', icon: Activity },
  { id: 'attendance', labelKey: 'nav.attendance', icon: UserCheck },
  { id: 'government_session', labelKey: 'nav.government_session', icon: Landmark },
  { id: 'grade_backlog', labelKey: 'nav.grade_backlog', icon: Clock },
];

const SECONDARY_NAV_ITEMS = [
  { id: 'resource', labelKey: 'nav.resource', icon: Layers },
  { id: 'settings', labelKey: 'nav.settings', icon: Settings },
  { id: 'help', labelKey: 'nav.help', icon: HelpCircle },
];

/**
 * Reusable AppSidebar Component
 * Apple iOS-style Liquid Glass translucent sidebar with zero layout-shift navigation.
 * All labels are translated via the centralized i18n system.
 */
export default function AppSidebar({
  activeTab = 'dashboard',
  onTabChange = () => {}
}) {
  const { t } = useTranslation();

  return (
    <aside className="liquid-glass-sidebar w-[250px] flex flex-col justify-between h-screen sticky top-0 shrink-0 select-none z-30 transition-colors duration-300">
      {/* Top Section */}
      <div className="p-5 relative z-[1]">
        {/* Brand Header */}
        <div className="flex items-center gap-3 mb-8 px-1">
          <PeacockLogo className="h-[36px] w-auto object-contain" />
          <span className="font-semibold text-[18px] tracking-tight text-[#0A0A0A] dark:text-[#F5F5F5] font-['Inter_Tight',sans-serif]">
            Saarthi
          </span>
        </div>

        {/* Menu Navigation */}
        <div>
          <div className="text-[11px] font-semibold text-[#6E6E6E] dark:text-[#A3A3A3] uppercase tracking-wider mb-2 px-3">
            {t('nav.menu')}
          </div>
          <nav className="flex flex-col gap-1">
            {MAIN_NAV_ITEMS.map((item) => {
              const Icon = item.icon;
              const isActive = activeTab === item.id;
              return (
                <button
                  key={item.id}
                  type="button"
                  onClick={() => onTabChange(item.id)}
                  className={`w-full h-[40px] flex items-center gap-3 px-3 rounded-xl text-xs font-medium transition-colors duration-150 text-left cursor-pointer select-none shrink-0 border border-transparent ${
                    isActive
                      ? 'liquid-glass-nav-active text-[#0A0A0A] dark:text-[#FFFFFF] font-semibold'
                      : 'text-[#6E6E6E] dark:text-[#A3A3A3] hover:text-[#0A0A0A] dark:hover:text-[#F5F5F5] hover:bg-white/40 dark:hover:bg-white/5'
                  }`}
                >
                  <div className="w-5 h-5 flex items-center justify-center shrink-0">
                    <Icon className={`w-[18px] h-[18px] ${isActive ? 'text-[#0A0A0A] dark:text-[#FFFFFF]' : 'text-[#6E6E6E] dark:text-[#A3A3A3]'}`} />
                  </div>
                  <span className="truncate flex-1 min-w-0 text-xs">{t(item.labelKey)}</span>
                  <div className="w-4 h-4 flex items-center justify-center shrink-0 ml-auto">
                    <div className={`w-1.5 h-1.5 rounded-full bg-[#0A0A0A] dark:bg-[#FFFFFF] transition-opacity duration-150 ${isActive ? 'visible opacity-100' : 'invisible opacity-0'}`} />
                  </div>
                </button>
              );
            })}
          </nav>
        </div>
      </div>

      {/* Bottom Section */}
      <div className="p-4 border-t border-black/[0.05] dark:border-white/[0.07] relative z-[1]">
        {/* Secondary Menu (Resource, Settings, Help & Support) */}
        <nav className="flex flex-col gap-1">
          {SECONDARY_NAV_ITEMS.map((item) => {
            const Icon = item.icon;
            const isActive = activeTab === item.id;
            return (
              <button
                key={item.id}
                type="button"
                onClick={() => onTabChange(item.id)}
                className={`w-full h-[36px] flex items-center gap-3 px-3 rounded-xl text-xs font-medium transition-colors duration-150 text-left cursor-pointer select-none shrink-0 border border-transparent ${
                  isActive
                    ? 'liquid-glass-nav-active text-[#0A0A0A] dark:text-[#FFFFFF] font-semibold'
                    : 'text-[#6E6E6E] dark:text-[#A3A3A3] hover:text-[#0A0A0A] dark:hover:text-[#F5F5F5] hover:bg-white/40 dark:hover:bg-white/5'
                }`}
              >
                <div className="w-5 h-5 flex items-center justify-center shrink-0">
                  <Icon className="w-4 h-4 text-[#6E6E6E] dark:text-[#A3A3A3]" />
                </div>
                <span className="truncate flex-1 min-w-0 text-xs">{t(item.labelKey)}</span>
              </button>
            );
          })}
        </nav>
      </div>
    </aside>
  );
}
