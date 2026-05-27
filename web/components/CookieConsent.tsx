'use client';

/**
 * Cookie consent banner — minimal, bilingual, GDPR-safe defaults.
 *
 * Osool runs strictly-necessary cookies (auth JWT, session id) without
 * consent — that's the carve-out every regulator allows. Analytics and
 * any third-party scripts that drop tracking cookies require an opt-in,
 * which is what this banner exists to collect.
 *
 * Behaviour:
 *   1. On first paint: show banner if no decision in localStorage.
 *   2. "Accept all"    -> osool.cookie_consent = "all", banner dismissed.
 *   3. "Necessary only" -> osool.cookie_consent = "essential", banner dismissed.
 *   4. Once a value is set, the banner never reappears (user can toggle
 *      via /privacy in a future iteration).
 *
 * The decision is read by other components (analytics initialisers, etc.)
 * via `getCookieConsent()` so they only fire when consent is granted.
 */

import { useEffect, useState } from 'react';
import Link from 'next/link';
import { useLanguage } from '@/contexts/LanguageContext';

const CONSENT_KEY = 'osool.cookie_consent';

export type CookieConsentValue = 'all' | 'essential' | null;

export function getCookieConsent(): CookieConsentValue {
  if (typeof window === 'undefined') return null;
  const v = window.localStorage.getItem(CONSENT_KEY);
  return v === 'all' || v === 'essential' ? v : null;
}

export default function CookieConsent() {
  const { language } = useLanguage();
  const isAr = language === 'ar';

  // Hidden until we've checked localStorage on the client. Avoids SSR
  // flash + lets us render nothing for users who already decided.
  const [visible, setVisible] = useState(false);

  useEffect(() => {
    if (getCookieConsent() === null) {
      setVisible(true);
    }
  }, []);

  const decide = (choice: 'all' | 'essential') => {
    try {
      window.localStorage.setItem(CONSENT_KEY, choice);
    } catch {
      // Private mode or quota issue — banner still closes; user just won't
      // see persistence. Acceptable: re-prompting next visit is fine.
    }
    setVisible(false);
  };

  if (!visible) return null;

  const t = isAr
    ? {
        title: 'نستخدم ملفات تعريف الارتباط',
        body:
          'تستخدم أصول ملفات تعريف الارتباط الضرورية لتسجيل الدخول وحفظ تفضيلاتك. للتحليلات الاختيارية، نحتاج موافقتك.',
        accept: 'قبول الكل',
        essential: 'الضرورية فقط',
        learn: 'سياسة الخصوصية',
      }
    : {
        title: 'We use cookies',
        body:
          'Osool uses strictly-necessary cookies for sign-in and saving your preferences. Optional analytics need your consent.',
        accept: 'Accept all',
        essential: 'Necessary only',
        learn: 'Privacy policy',
      };

  return (
    <div
      role="dialog"
      aria-label={t.title}
      dir={isAr ? 'rtl' : 'ltr'}
      style={{
        position: 'fixed',
        insetInline: 12,
        bottom: 12,
        zIndex: 9999,
        maxWidth: 640,
        marginInline: 'auto',
        padding: 16,
        borderRadius: 16,
        border: '1px solid var(--color-border, rgba(0,0,0,0.1))',
        background: 'var(--color-surface, white)',
        boxShadow: '0 24px 48px rgba(0,0,0,0.18)',
        display: 'grid',
        gap: 12,
      }}
    >
      <div>
        <div style={{ fontWeight: 600, fontSize: 14, marginBottom: 4 }}>{t.title}</div>
        <p style={{ fontSize: 13, lineHeight: 1.5, margin: 0, color: 'var(--color-text-secondary, #64748b)' }}>
          {t.body}{' '}
          <Link
            href="/privacy"
            style={{
              color: 'var(--color-text-primary, #111)',
              textDecoration: 'underline',
            }}
          >
            {t.learn}
          </Link>
        </p>
      </div>
      <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap', justifyContent: 'flex-end' }}>
        <button
          type="button"
          onClick={() => decide('essential')}
          style={{
            fontSize: 13,
            padding: '8px 14px',
            borderRadius: 10,
            border: '1px solid var(--color-border, rgba(0,0,0,0.1))',
            background: 'transparent',
            color: 'var(--color-text-primary, #111)',
            cursor: 'pointer',
          }}
        >
          {t.essential}
        </button>
        <button
          type="button"
          onClick={() => decide('all')}
          style={{
            fontSize: 13,
            padding: '8px 14px',
            borderRadius: 10,
            border: 'none',
            background: 'var(--color-text-primary, #111)',
            color: 'var(--color-background, white)',
            fontWeight: 600,
            cursor: 'pointer',
          }}
        >
          {t.accept}
        </button>
      </div>
    </div>
  );
}
