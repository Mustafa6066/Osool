'use client';

import React from 'react';
import { usePathname, useRouter } from 'next/navigation';
import { motion, AnimatePresence } from 'framer-motion';
import {
  TrendingUp,
  BarChart3,
  MapPin,
  MessageSquare,
  Building2,
  ArrowRight,
  Search,
} from 'lucide-react';
import { useLanguage } from '@/contexts/LanguageContext';

/* ─── route context configs ─────────────────────── */
const ROUTE_PANELS: Record<
  string,
  {
    chips: { label: string; labelAr: string; href?: string; icon: React.ElementType }[];
  }
> = {
  market: {
    chips: [
      { label: 'New Cairo', labelAr: 'القاهرة الجديدة', href: '/market?area=new-cairo', icon: MapPin },
      { label: 'Trending', labelAr: 'الأكثر رواجاً', href: '/market?sort=trending', icon: TrendingUp },
      { label: 'Top ROI', labelAr: 'أعلى عائد', href: '/market?sort=roi', icon: BarChart3 },
      { label: 'New Launch', labelAr: 'إطلاق جديد', href: '/market?sort=newest', icon: Building2 },
    ],
  },
  chat: {
    chips: [
      { label: 'Compare areas', labelAr: 'قارن المناطق', href: '/chat?q=compare+areas', icon: BarChart3 },
      { label: 'Investment tips', labelAr: 'نصائح استثمارية', href: '/chat?q=investment+tips', icon: TrendingUp },
      { label: 'Find 2BR under 3M', labelAr: 'ابحث عن شقتين أقل من 3 مليون', href: '/chat?q=2br+under+3m', icon: Search },
    ],
  },
  dashboard: {
    chips: [
      { label: 'Portfolio', labelAr: 'المحفظة', href: '/dashboard#portfolio', icon: BarChart3 },
      { label: 'Alerts', labelAr: 'التنبيهات', href: '/dashboard#alerts', icon: MessageSquare },
    ],
  },
  explore: {
    chips: [
      { label: '6th October', labelAr: 'أكتوبر', href: '/explore?area=6th-october', icon: MapPin },
      { label: 'North Coast', labelAr: 'الساحل الشمالي', href: '/explore?area=north-coast', icon: MapPin },
      { label: 'New Capital', labelAr: 'العاصمة الإدارية', href: '/explore?area=new-capital', icon: MapPin },
    ],
  },
};

function getRouteKey(pathname: string): string | null {
  if (pathname.startsWith('/market')) return 'market';
  if (pathname.startsWith('/chat')) return 'chat';
  if (pathname.startsWith('/dashboard') || pathname === '/') return 'dashboard';
  if (pathname.startsWith('/explore')) return 'explore';
  return null;
}

export default function DockContextPanel() {
  const pathname = usePathname();
  const router = useRouter();
  const { language } = useLanguage();

  const routeKey = getRouteKey(pathname);
  const panelData = routeKey ? ROUTE_PANELS[routeKey] : null;

  return (
    <AnimatePresence mode="wait">
      {panelData && (
        <motion.div
          key={routeKey}
          initial={{ opacity: 0, y: 12, scale: 0.96 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          exit={{ opacity: 0, y: 10, scale: 0.96 }}
          transition={{ type: 'spring', damping: 22, stiffness: 180, duration: 0.3 }}
          className="fixed bottom-[68px] sm:bottom-[92px] left-1/2 -translate-x-1/2 z-40 max-w-[94vw]"
        >
          <div className="flex items-center gap-1.5 sm:gap-2 px-2 py-1.5 rounded-2xl bg-[var(--color-surface)]/80 backdrop-blur-xl border border-[var(--color-border)] shadow-lg">
            {panelData.chips.map((chip) => {
              const Icon = chip.icon;
              return (
                <button
                  key={chip.label}
                  onClick={() => chip.href && router.push(chip.href)}
                  className="flex items-center gap-1.5 px-2.5 py-1.5 rounded-xl text-[11px] sm:text-xs font-medium text-[var(--color-text-secondary)] hover:text-emerald-600 dark:hover:text-emerald-400 hover:bg-emerald-500/8 transition-colors whitespace-nowrap"
                >
                  <Icon className="w-3 h-3 sm:w-3.5 sm:h-3.5 shrink-0" />
                  {language === 'ar' ? chip.labelAr : chip.label}
                  <ArrowRight className="w-2.5 h-2.5 opacity-40" />
                </button>
              );
            })}
          </div>
        </motion.div>
      )}
    </AnimatePresence>
  );
}
