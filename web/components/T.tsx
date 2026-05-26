'use client';

import { useLanguage } from '@/contexts/LanguageContext';

export function T({ k }: { k: string }) {
  const { t } = useLanguage();
  return <>{t(k)}</>;
}
