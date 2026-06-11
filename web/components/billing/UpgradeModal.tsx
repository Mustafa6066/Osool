'use client';

import { useRouter } from 'next/navigation';
import { Check, Crown, X } from 'lucide-react';
import { useLanguage } from '@/contexts/LanguageContext';

interface UpgradeModalProps {
  open: boolean;
  onClose: () => void;
  /** Analytics source tag, e.g. "reality-check" | "chat-limit" | "dashboard" */
  source?: string;
}

const BENEFITS = {
  en: [
    'Unlimited Reality Checks — no daily cap',
    'Unmasked broker contacts & exact unit IDs',
    'Unlimited AI advisor conversations',
    'Price-drop & La2ta (لقطة) alerts on saved searches',
    'Pro affordability analysis on every tool',
  ],
  ar: [
    'فحوصات حقيقية بلا حدود — من غير سقف يومي',
    'بيانات السماسرة وأرقام الوحدات كاملة',
    'محادثات غير محدودة مع المستشار الذكي',
    'تنبيهات انخفاض الأسعار واللقطات على بحثك المحفوظ',
    'تحليل القدرة الشرائية الاحترافي في كل الأدوات',
  ],
};

export default function UpgradeModal({ open, onClose, source }: UpgradeModalProps) {
  const router = useRouter();
  const { language, direction } = useLanguage();
  const isRTL = direction === 'rtl';

  if (!open) return null;

  const goToPricing = () => {
    onClose();
    router.push(source ? `/pricing?source=${encodeURIComponent(source)}` : '/pricing');
  };

  return (
    <div
      className="fixed inset-0 z-[100] flex items-center justify-center bg-black/60 p-4 backdrop-blur-sm"
      dir={direction}
      onClick={onClose}
      role="dialog"
      aria-modal="true"
    >
      <div
        className="w-full max-w-md rounded-[28px] border border-emerald-500/30 bg-[var(--color-surface)] p-7 shadow-2xl"
        onClick={(e) => e.stopPropagation()}
      >
        <div className="flex items-start justify-between">
          <div className="inline-flex h-12 w-12 items-center justify-center rounded-2xl bg-emerald-500 text-white">
            <Crown className="h-6 w-6" />
          </div>
          <button
            onClick={onClose}
            aria-label={isRTL ? 'إغلاق' : 'Close'}
            className="rounded-full p-2 text-[var(--color-text-muted)] transition hover:bg-[var(--color-background)]"
          >
            <X className="h-5 w-5" />
          </button>
        </div>

        <h2 className="mt-4 text-2xl font-semibold text-[var(--color-text-primary)]">
          {isRTL ? 'افتح القوة الكاملة مع أصول برو' : 'Unlock everything with Osool Pro'}
        </h2>
        <p className="mt-2 text-sm text-[var(--color-text-secondary)]">
          {isRTL
            ? 'الأرقام بتقولك في صفقة — برو بيوصلك لصاحبها.'
            : 'The numbers show you the deal — Pro connects you to it.'}
        </p>

        <ul className="mt-5 space-y-2.5">
          {BENEFITS[language].map((benefit) => (
            <li
              key={benefit}
              className="flex items-start gap-2 text-sm text-[var(--color-text-secondary)]"
            >
              <Check className="mt-0.5 h-4 w-4 shrink-0 text-emerald-500" />
              {benefit}
            </li>
          ))}
        </ul>

        <button
          onClick={goToPricing}
          className="mt-7 w-full rounded-2xl bg-emerald-500 py-3.5 text-sm font-semibold text-white transition hover:bg-emerald-600"
        >
          {isRTL ? 'شوف الباقات والأسعار' : 'See plans & pricing'}
        </button>
        <button
          onClick={onClose}
          className="mt-2 w-full py-2 text-xs text-[var(--color-text-muted)] transition hover:text-[var(--color-text-secondary)]"
        >
          {isRTL ? 'لاحقًا' : 'Maybe later'}
        </button>
      </div>
    </div>
  );
}
