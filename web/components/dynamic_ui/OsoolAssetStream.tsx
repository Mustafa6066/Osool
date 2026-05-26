'use client';

/**
 * OsoolAssetStream.tsx
 * ─────────────────────────────────────────────────────────────────
 * Core orchestrator component for the dynamic_ui primitive library.
 *
 * Responsibilities
 * ────────────────
 * 1. Owns the full reactive fetch lifecycle (idle → loading → success | error)
 *    for a single property asset identified by `assetId`.
 * 2. Provides local contextual financial metrics via React Context, making
 *    them available to any deeply-nested consumer via `useAssetStream()`.
 * 3. Delegates all presentation to the `renderPipeline` render prop,
 *    keeping data-fetching concerns completely decoupled from layout.
 * 4. Surfaces granular per-phase UI slots: `loadingFallback`, `errorFallback`,
 *    and `idleFallback` for maximum consumer control.
 * 5. Supports optional polling via `pollIntervalMs` for live data streams.
 *
 * API shape expected from the backend endpoint
 * ─────────────────────────────────────────────
 * GET {apiEndpoint}/{assetId}
 *
 * Response (snake_case → camelCase mapping applied internally):
 * {
 *   "listing_id": "str",
 *   "compound_id": "str",
 *   "geographic_zone": "str",
 *   "total_price": number,          // EGP
 *   "size_sqm": number,
 *   "floor_level": number,
 *   "view_orientation": "str",
 *   "delivery_year": number,
 *   "is_secondary_market": boolean,
 *   "has_private_garden": boolean,
 *   "cash_npv_egp": number,
 *   "normalized_cash_price_sqm": number,
 *   "feature_multiplier": number,
 *   "effective_multiplier": number,
 *   "delivery_lag_penalty_pp": number,
 *   "is_la2ta": boolean,
 *   "la2ta_depth_pct": number | null,
 *   "ingested_at": "ISO-8601 | null",
 *   "cbe_rate_pct": number           // fraction, e.g. 0.22
 * }
 *
 * Usage
 * ─────
 * ```tsx
 * <OsoolAssetStream
 *   assetId="listing-abc-123"
 *   renderPipeline={(data, metrics) => (
 *     <div className="grid grid-cols-2 gap-4">
 *       <NPVMarginWidget {...metrics} />
 *       <La2taSignalBadge {...metrics} />
 *       <StructuralVarianceTable {...metrics} {...data} />
 *     </div>
 *   )}
 * />
 * ```
 *
 * Accessing context downstream (without prop drilling):
 * ```tsx
 * const { financialMetrics, state } = useAssetStream();
 * ```
 */

import React, {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useRef,
  useState,
} from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { RefreshCw, AlertTriangle, Loader2, Wifi } from 'lucide-react';
import type {
  AssetStreamContextValue,
  AssetStreamData,
  FinancialMetrics,
  StreamState,
} from './types';

// ── Context ───────────────────────────────────────────────────────

const AssetStreamCtx = createContext<AssetStreamContextValue | null>(null);

/**
 * Consume the nearest OsoolAssetStream context.
 * Must be called inside a component that is a descendant of OsoolAssetStream.
 */
export function useAssetStream(): AssetStreamContextValue {
  const ctx = useContext(AssetStreamCtx);
  if (!ctx) {
    throw new Error(
      'useAssetStream() must be called inside <OsoolAssetStream>. ' +
      'Ensure the component is wrapped by OsoolAssetStream before consuming the context.'
    );
  }
  return ctx;
}

// ── Default API endpoint ──────────────────────────────────────────

const DEFAULT_API_ENDPOINT =
  process.env.NEXT_PUBLIC_API_URL
    ? `${process.env.NEXT_PUBLIC_API_URL.replace(/\/$/, '')}/api/ingest/listing`
    : '/api/ingest/listing';

// ── Response → domain mapper ──────────────────────────────────────

// eslint-disable-next-line @typescript-eslint/no-explicit-any
function mapResponseToAssetData(raw: Record<string, any>): AssetStreamData {
  return {
    listingId:         String(raw.listing_id ?? ''),
    compoundId:        String(raw.compound_id ?? ''),
    geographicZone:    String(raw.geographic_zone ?? ''),
    totalPriceEgp:     Number(raw.total_price ?? 0),
    sizeSqm:           Number(raw.size_sqm ?? 0),
    floorLevel:        Number(raw.floor_level ?? 0),
    viewOrientation:   String(raw.view_orientation ?? ''),
    deliveryYear:      Number(raw.delivery_year ?? 2026),
    isSecondaryMarket: Boolean(raw.is_secondary_market ?? true),
    hasPrivateGarden:  Boolean(raw.has_private_garden ?? false),
  };
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
function mapResponseToMetrics(raw: Record<string, any>): FinancialMetrics {
  const nominalPriceEgp = Number(raw.total_price ?? 0);
  const cashNpvEgp      = Number(raw.cash_npv_egp ?? nominalPriceEgp);
  const discountEgp     = nominalPriceEgp - cashNpvEgp;

  return {
    cashNpvEgp,
    nominalPriceEgp,
    discountEgp,
    discountPct:               nominalPriceEgp > 0 ? discountEgp / nominalPriceEgp : 0,
    normalizedPricePerSqmEgp:  Number(raw.normalized_cash_price_sqm ?? 0),
    featureMultiplier:         Number(raw.feature_multiplier ?? 1),
    effectiveMultiplier:       Number(raw.effective_multiplier ?? 1),
    deliveryLagPenaltyPp:      Number(raw.delivery_lag_penalty_pp ?? 0),
    cbeRatePct:                Number(raw.cbe_rate_pct ?? 0.22),
    isLa2ta:                   Boolean(raw.is_la2ta ?? false),
    la2taDepthPct:             raw.la2ta_depth_pct != null
                                 ? Number(raw.la2ta_depth_pct)
                                 : undefined,
    ingestedAt:                raw.ingested_at ?? undefined,
  };
}

// ── Props ─────────────────────────────────────────────────────────

export interface OsoolAssetStreamProps {
  /** Unique listing identifier forwarded to the backend endpoint. */
  assetId: string;
  /**
   * Render prop called when data is available.
   * Receives the full asset record and computed financial metrics.
   */
  renderPipeline: (
    data: AssetStreamData,
    financialMetrics: FinancialMetrics,
  ) => React.ReactNode;
  /**
   * Base URL for the data endpoint.
   * The component appends `/{assetId}` automatically.
   * Defaults to NEXT_PUBLIC_API_URL + /api/ingest/listing.
   */
  apiEndpoint?: string;
  /**
   * When set, the component re-fetches on this interval (milliseconds).
   * Set to 0 or undefined to disable polling.
   */
  pollIntervalMs?: number;
  /** Custom loading skeleton. Falls back to a built-in glass skeleton. */
  loadingFallback?: React.ReactNode;
  /** Custom error UI. Falls back to a built-in retry card. */
  errorFallback?: (error: string, retry: () => void) => React.ReactNode;
  /** UI to render before the first fetch is triggered (idle state). */
  idleFallback?: React.ReactNode;
  /** Extra classes for the outermost container. */
  className?: string;
}

// ── Built-in skeleton ─────────────────────────────────────────────

function DefaultLoadingSkeleton() {
  return (
    <div className="space-y-3 p-5 animate-pulse" aria-busy aria-label="Loading asset data">
      {/* Header line */}
      <div className="h-3 w-32 rounded-full bg-[var(--color-surface-dark)]" />
      {/* Large value block */}
      <div className="h-8 w-48 rounded-xl bg-[var(--color-surface-dark)]" />
      {/* Bar */}
      <div className="h-2.5 w-full rounded-full bg-[var(--color-surface-dark)]" />
      {/* Footer lines */}
      <div className="flex gap-3 pt-1">
        <div className="h-3 w-24 rounded-full bg-[var(--color-surface-dark)]" />
        <div className="h-3 w-16 rounded-full bg-[var(--color-surface-dark)]" />
      </div>
    </div>
  );
}

// ── Built-in error card ───────────────────────────────────────────

function DefaultErrorCard({
  error,
  assetId,
  retry,
}: {
  error: string;
  assetId: string;
  retry: () => void;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.97 }}
      animate={{ opacity: 1, scale: 1 }}
      className="rounded-2xl border border-rose-400/30 bg-rose-500/5 p-5 space-y-3"
    >
      <div className="flex items-start gap-3">
        <AlertTriangle size={16} className="text-rose-500 shrink-0 mt-0.5" aria-hidden />
        <div className="space-y-1">
          <p className="text-sm font-semibold text-rose-600">
            Failed to load asset
          </p>
          <p className="text-[12px] text-rose-500/80 font-mono break-all">
            {assetId}
          </p>
          <p className="text-[12px] text-[var(--color-text-muted)]">{error}</p>
        </div>
      </div>
      <button
        onClick={retry}
        className="flex items-center gap-1.5 text-[12px] font-medium text-rose-500
                   hover:text-rose-600 transition-colors focus-visible:outline-none
                   focus-visible:ring-2 focus-visible:ring-rose-400 rounded px-1"
      >
        <RefreshCw size={12} strokeWidth={2.5} />
        Retry
      </button>
    </motion.div>
  );
}

// ── Component ─────────────────────────────────────────────────────

export function OsoolAssetStream({
  assetId,
  renderPipeline,
  apiEndpoint = DEFAULT_API_ENDPOINT,
  pollIntervalMs,
  loadingFallback,
  errorFallback,
  idleFallback,
  className = '',
}: OsoolAssetStreamProps) {
  const [state, setState] = useState<StreamState>('idle');
  const [data, setData] = useState<AssetStreamData | null>(null);
  const [financialMetrics, setFinancialMetrics] = useState<FinancialMetrics | null>(null);
  const [error, setError] = useState<string | null>(null);

  // Keep a stable ref to the latest assetId so the fetch closure never
  // captures a stale value across re-renders or polling ticks.
  const assetIdRef = useRef(assetId);
  assetIdRef.current = assetId;

  const pollTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  // ── Core fetch function ────────────────────────────────────────

  const fetchAsset = useCallback(async () => {
    // Cancel any in-flight request before starting a new one.
    abortRef.current?.abort();
    const controller = new AbortController();
    abortRef.current = controller;

    setState('loading');
    setError(null);

    try {
      // Sanitise assetId to prevent path-traversal; only alphanumerics,
      // hyphens, and underscores are allowed through.
      const safeId = assetIdRef.current.replace(/[^a-zA-Z0-9_-]/g, '');
      if (!safeId) throw new Error('Invalid assetId — only [a-zA-Z0-9_-] are permitted.');

      const url = `${apiEndpoint}/${encodeURIComponent(safeId)}`;
      const res = await fetch(url, {
        signal: controller.signal,
        headers: { Accept: 'application/json' },
        // Credentials are included automatically if the request is same-origin.
        // For cross-origin, cookies are not sent — rely on the JWT in Authorization
        // header if the backend requires auth here.
      });

      if (!res.ok) {
        const text = await res.text().catch(() => `HTTP ${res.status}`);
        throw new Error(`${res.status} — ${text.slice(0, 120)}`);
      }

      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const json: Record<string, any> = await res.json();

      const assetData     = mapResponseToAssetData(json);
      const metrics       = mapResponseToMetrics(json);

      setData(assetData);
      setFinancialMetrics(metrics);
      setState('success');
    } catch (err) {
      if ((err as Error).name === 'AbortError') {
        // Intentional cancellation — don't update state.
        return;
      }
      setError((err as Error).message || 'Unknown error');
      setState('error');
    }
  }, [apiEndpoint]);

  // ── Trigger on mount and assetId change ───────────────────────

  useEffect(() => {
    if (!assetId) {
      setState('idle');
      return;
    }
    fetchAsset();

    return () => {
      abortRef.current?.abort();
    };
  }, [assetId, fetchAsset]);

  // ── Optional polling ──────────────────────────────────────────

  useEffect(() => {
    if (!pollIntervalMs || pollIntervalMs <= 0 || !assetId) return;

    const schedule = () => {
      pollTimerRef.current = setTimeout(async () => {
        await fetchAsset();
        schedule(); // re-arm after completion
      }, pollIntervalMs);
    };

    schedule();

    return () => {
      if (pollTimerRef.current) clearTimeout(pollTimerRef.current);
    };
  }, [pollIntervalMs, assetId, fetchAsset]);

  // ── Build context value ───────────────────────────────────────

  const contextValue: AssetStreamContextValue = {
    state,
    data,
    financialMetrics,
    error,
    refetch: fetchAsset,
  };

  // ── Render ────────────────────────────────────────────────────

  return (
    <AssetStreamCtx.Provider value={contextValue}>
      <div className={className} data-asset-id={assetId} data-stream-state={state}>
        <AnimatePresence mode="wait">
          {/* IDLE */}
          {state === 'idle' && (
            <motion.div key="idle" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}>
              {idleFallback ?? (
                <div className="flex items-center gap-2 px-4 py-3 rounded-xl
                                bg-[var(--color-surface-hover)] border border-[var(--color-border)]
                                text-[var(--color-text-muted)] text-sm">
                  <Wifi size={14} strokeWidth={2} aria-hidden />
                  Waiting for asset stream…
                </div>
              )}
            </motion.div>
          )}

          {/* LOADING */}
          {state === 'loading' && (
            <motion.div
              key="loading"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.2 }}
            >
              {loadingFallback ?? (
                <div
                  className="rounded-2xl border border-[var(--color-border)]
                             bg-[var(--glass-bg)] backdrop-blur-[var(--glass-blur)]
                             overflow-hidden"
                  style={{ boxShadow: 'var(--glass-shadow)' }}
                >
                  <DefaultLoadingSkeleton />
                </div>
              )}
            </motion.div>
          )}

          {/* ERROR */}
          {state === 'error' && error && (
            <motion.div
              key="error"
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.25 }}
            >
              {errorFallback
                ? errorFallback(error, fetchAsset)
                : (
                  <DefaultErrorCard
                    error={error}
                    assetId={assetId}
                    retry={fetchAsset}
                  />
                )}
            </motion.div>
          )}

          {/* SUCCESS */}
          {state === 'success' && data && financialMetrics && (
            <motion.div
              key="success"
              initial={{ opacity: 0, y: 4 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.35, ease: [0.16, 1, 0.3, 1] }}
            >
              {renderPipeline(data, financialMetrics)}
            </motion.div>
          )}
        </AnimatePresence>
      </div>
    </AssetStreamCtx.Provider>
  );
}

export default OsoolAssetStream;
