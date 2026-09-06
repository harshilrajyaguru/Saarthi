import React from 'react';
import AppShell from './components/layout/AppShell';
import GlassSurface from './components/ui/GlassSurface';
import GlassButton from './components/ui/GlassButton';
import { useTranslation } from './i18n/i18n';

export default function App() {
  const { t } = useTranslation();

  return (
    <AppShell>
      {/* Visual Component Verification Container */}
      <div className="max-w-4xl space-y-6">
        <div>
          <h2 className="text-[28px] font-semibold tracking-tight text-[#0A0A0A] dark:text-[#F5F5F5] mb-1">
            {t('app.foundation_title')}
          </h2>
          <p className="text-xs text-[#6E6E6E] dark:text-[#A3A3A3]">
            {t('app.foundation_desc')}
          </p>
        </div>

        <GlassSurface className="space-y-4">
          <div className="text-xs font-semibold uppercase tracking-wider text-[#6E6E6E] dark:text-[#A3A3A3]">
            {t('app.material_label')}
          </div>
          <div className="flex flex-wrap gap-3">
            <GlassButton variant="primary">
              {t('app.primary_action')}
            </GlassButton>
            <GlassButton variant="secondary">
              {t('app.secondary_surface')}
            </GlassButton>
          </div>
        </GlassSurface>

        <div className="liquid-glass-card text-center py-12 text-xs text-[#6E6E6E] dark:text-[#A3A3A3] rounded-[20px]">
          <span className="relative z-[1]">{t('app.page_content')}</span>
        </div>
      </div>
    </AppShell>
  );
}
