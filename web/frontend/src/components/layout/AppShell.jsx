import React, { useState } from 'react';
import AppSidebar from './AppSidebar';
import TopHeader from './TopHeader';
import { useTranslation } from '../../i18n/i18n';

/**
 * Reusable AppShell Component
 * Master layout shell integrating Sidebar, TopHeader, and Main Content area.
 * Includes environmental depth layer for Liquid Glass material visibility.
 * Header titles are translated via the centralized i18n system.
 */
export default function AppShell({ children }) {
  const [activeTab, setActiveTab] = useState('dashboard');
  const { t } = useTranslation();

  // Translation keys for header titles, mapped to tab ids
  const titleKeys = {
    dashboard: 'header.dashboard',
    activity: 'header.activity',
    attendance: 'header.attendance',
    government_session: 'header.government_session',
    grade_backlog: 'header.grade_backlog',
    resource: 'header.resource',
    settings: 'header.settings',
    help: 'header.help',
  };

  return (
    <div className="flex min-h-screen text-[#0A0A0A] dark:text-[#F5F5F5] font-sans antialiased transition-colors duration-300 relative">
      {/* Environmental depth layer — subtle tonal gradients behind glass (light mode) */}
      <div
        className="fixed inset-0 pointer-events-none z-0 dark:opacity-0 transition-opacity duration-300"
        aria-hidden="true"
        style={{
          background: `
            radial-gradient(ellipse 80% 60% at 20% 30%, rgba(220, 225, 235, 0.30) 0%, transparent 70%),
            radial-gradient(ellipse 60% 50% at 75% 70%, rgba(225, 220, 215, 0.22) 0%, transparent 70%),
            radial-gradient(ellipse 50% 40% at 50% 10%, rgba(230, 232, 238, 0.18) 0%, transparent 60%)
          `,
        }}
      />
      {/* Environmental depth layer — dark mode subtle depth */}
      <div
        className="fixed inset-0 pointer-events-none z-0 opacity-0 dark:opacity-100 transition-opacity duration-300"
        aria-hidden="true"
        style={{
          background: `
            radial-gradient(ellipse 70% 50% at 25% 25%, rgba(30, 35, 50, 0.25) 0%, transparent 70%),
            radial-gradient(ellipse 55% 45% at 70% 75%, rgba(25, 22, 20, 0.18) 0%, transparent 70%)
          `,
        }}
      />

      {/* App Sidebar */}
      <AppSidebar
        activeTab={activeTab}
        onTabChange={setActiveTab}
      />

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0 relative z-[1]">
        {/* Top Header */}
        <TopHeader title={t(titleKeys[activeTab] || 'header.dashboard')} activeTab={activeTab} />

        {/* Viewport Main Container */}
        <main className="flex-1 p-8 overflow-y-auto">
          {children || (
            <div className="liquid-glass-card flex items-center justify-center h-64 rounded-[20px] text-[#6E6E6E] dark:text-[#A3A3A3] text-sm">
              <span className="relative z-[1]">{t('app.page_content')}</span>
            </div>
          )}
        </main>
      </div>
    </div>
  );
}
