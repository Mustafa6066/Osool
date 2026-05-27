'use client';

/**
 * Currency context — closes audit ship-blocker A4 ("diaspora ICP cannot
 * see USD"). Provides:
 *
 *   - currency: 'EGP' | 'USD' — current preference, persisted in localStorage
 *   - setCurrency(): user override
 *   - egpPerUsd: live conversion rate, fetched once on mount from
 *     /api/fx/egp-usd (which is itself backed by MarketIndicator)
 *   - format(amountEgp): formats a raw EGP number into the user's chosen
 *     currency with locale-appropriate digits and a M/K suffix
 *
 * Design choices:
 *
 *   - Source of truth for the rate is the backend, not a third-party API.
 *     Same pattern as CBE rate — admin updates one row, all readers see
 *     the change. No FX API key to manage, no rate-limit headaches.
 *   - We don't store amounts in USD — every property in the DB is EGP.
 *     Conversion happens at render time, against the cached rate.
 *   - 1h cache via SWR-style state. If the API call fails, we keep using
 *     the 2026 fallback (49 EGP/USD) so the UI never shows broken prices.
 */

import { createContext, useContext, useEffect, useState, useCallback, type ReactNode } from 'react';

const STORAGE_KEY = 'osool.currency';
const FX_FALLBACK = 49.0; // matches backend _FX_FALLBACK_EGP_PER_USD
const FX_CACHE_MS = 60 * 60 * 1000; // 1h

export type Currency = 'EGP' | 'USD';

interface CurrencyContextValue {
  currency: Currency;
  setCurrency: (c: Currency) => void;
  egpPerUsd: number;
  /** Convert a raw EGP amount into the user's chosen currency. */
  convert: (amountEgp: number) => number;
  /** Format an EGP amount into a display string in the chosen currency. */
  format: (amountEgp: number, opts?: { lang?: 'en' | 'ar' }) => string;
}

const CurrencyContext = createContext<CurrencyContextValue | null>(null);

export function CurrencyProvider({ children }: { children: ReactNode }) {
  const [currency, setCurrencyState] = useState<Currency>('EGP');
  const [egpPerUsd, setEgpPerUsd] = useState<number>(FX_FALLBACK);

  // Restore persisted preference on first paint.
  useEffect(() => {
    if (typeof window === 'undefined') return;
    const saved = window.localStorage.getItem(STORAGE_KEY);
    if (saved === 'USD' || saved === 'EGP') setCurrencyState(saved);
  }, []);

  // Fetch the live rate once on mount (and refresh in background every 1h).
  useEffect(() => {
    let cancelled = false;
    const apiUrl = (process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000').replace(/\/$/, '');

    const load = async () => {
      try {
        const res = await fetch(`${apiUrl}/api/fx/egp-usd`, { cache: 'no-store' });
        if (!res.ok) return;
        const data = await res.json();
        if (cancelled) return;
        const rate = Number(data.egp_per_usd);
        if (Number.isFinite(rate) && rate > 0) {
          setEgpPerUsd(rate);
        }
      } catch {
        // Network blip — keep the previous (or fallback) value.
      }
    };

    void load();
    const interval = setInterval(load, FX_CACHE_MS);
    return () => {
      cancelled = true;
      clearInterval(interval);
    };
  }, []);

  const setCurrency = useCallback((c: Currency) => {
    setCurrencyState(c);
    try {
      window.localStorage.setItem(STORAGE_KEY, c);
    } catch {
      /* private mode — choice is in-memory only */
    }
  }, []);

  const convert = useCallback(
    (amountEgp: number) => (currency === 'EGP' ? amountEgp : amountEgp / egpPerUsd),
    [currency, egpPerUsd],
  );

  const format = useCallback(
    (amountEgp: number, opts?: { lang?: 'en' | 'ar' }) => {
      const lang = opts?.lang ?? 'en';
      const value = convert(amountEgp);
      if (currency === 'USD') {
        if (value >= 1_000_000) {
          const m = value / 1_000_000;
          return `$${m.toFixed(m >= 10 ? 1 : 2).replace(/\.?0+$/, '')}M`;
        }
        if (value >= 1_000) {
          return `$${Math.round(value / 1_000)}K`;
        }
        return `$${Math.round(value).toLocaleString('en-US')}`;
      }
      // EGP
      if (value >= 1_000_000) {
        const m = value / 1_000_000;
        const rounded = m.toFixed(m >= 10 ? 1 : 2).replace(/\.?0+$/, '');
        return lang === 'ar' ? `${rounded} مليون جنيه` : `${rounded}M EGP`;
      }
      if (value >= 1_000) {
        const k = Math.round(value / 1_000);
        return lang === 'ar' ? `${k} ألف جنيه` : `${k.toLocaleString('en-US')} EGP`;
      }
      return lang === 'ar'
        ? `${Math.round(value).toLocaleString('ar-EG')} جنيه`
        : `${Math.round(value).toLocaleString('en-US')} EGP`;
    },
    [currency, convert],
  );

  return (
    <CurrencyContext.Provider value={{ currency, setCurrency, egpPerUsd, convert, format }}>
      {children}
    </CurrencyContext.Provider>
  );
}

export function useCurrency(): CurrencyContextValue {
  const ctx = useContext(CurrencyContext);
  if (ctx === null) {
    // Safe default — usable outside the provider for components that
    // render before the tree mounts (rare, but Next.js does it on
    // some error pages).
    return {
      currency: 'EGP',
      setCurrency: () => {},
      egpPerUsd: FX_FALLBACK,
      convert: (n) => n,
      format: (n) => `${Math.round(n).toLocaleString('en-US')} EGP`,
    };
  }
  return ctx;
}
