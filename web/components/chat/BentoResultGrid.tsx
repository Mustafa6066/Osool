'use client';

import Image from 'next/image';
import { motion } from 'framer-motion';
import {
  MapPin,
  Heart,
  Scale,
  Sparkles,
  Bed,
  Bath,
  Maximize,
  BarChart2,
  TrendingUp,
} from 'lucide-react';

interface PropertyMetrics {
  size: number;
  bedrooms: number;
  bathrooms: number;
  wolf_score: number;
  roi: number;
  price_per_sqm: number;
  liquidity_rating: string;
}

interface Property {
  id: string;
  title: string;
  location: string;
  price: number;
  currency: string;
  metrics: PropertyMetrics;
  image: string;
  developer: string;
  tags: string[];
  status: string;
}

interface AnalyticsContext {
  has_analytics?: boolean;
  avg_price_sqm?: number;
  growth_rate?: number;
  rental_yield?: number;
  [key: string]: unknown;
}

interface BentoResultGridProps {
  properties: Property[];
  analyticsContext?: AnalyticsContext | null;
  language: string;
  savedIds: Set<string>;
  onOpenDetails: (prop: Property) => void;
  onSave: (prop: Property, e: React.MouseEvent) => void;
  onValuation: (prop: Property, e: React.MouseEvent) => void;
  onCompare: (prop: Property, e: React.MouseEvent) => void;
}

function QuickStat({ label, value }: { label: string; value: string }) {
  return (
    <div className="inline-flex items-center gap-1.5 rounded-full border border-[var(--color-border)]/60 bg-[var(--color-surface)] px-2.5 py-1 text-[11px] font-medium text-[var(--color-text-secondary)]">
      <span className="text-[var(--color-text-muted)]">{label}</span>
      <span className="text-[var(--color-text-primary)] font-semibold">{value}</span>
    </div>
  );
}

function PropertyLinePanel({
  prop,
  index,
  isRTL,
  isSaved,
  onOpen,
  onSave,
  onValuation,
  onCompare,
}: {
  prop: Property;
  index: number;
  isRTL: boolean;
  isSaved: boolean;
  onOpen: () => void;
  onSave: (e: React.MouseEvent) => void;
  onValuation: (e: React.MouseEvent) => void;
  onCompare: (e: React.MouseEvent) => void;
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.25, ease: [0.16, 1, 0.3, 1], delay: index * 0.03 }}
      onClick={onOpen}
      className="group flex items-stretch gap-2.5 sm:gap-3 rounded-2xl border border-[var(--color-border)]/55 bg-[var(--color-surface)]/55 hover:bg-[var(--color-surface)]/75 hover:border-emerald-500/35 transition-all duration-200 p-2.5 sm:p-3 cursor-pointer"
      dir={isRTL ? 'rtl' : 'ltr'}
    >
      <div className="relative w-28 h-20 sm:w-32 sm:h-24 rounded-xl overflow-hidden flex-shrink-0 bg-[var(--color-surface-elevated)]">
        <Image src={prop.image} alt={prop.title} fill className="object-cover group-hover:scale-105 transition-transform duration-500" sizes="(max-width: 640px) 112px, 128px" />
        {index === 0 && (
          <span className="absolute top-1.5 start-1.5 inline-flex items-center gap-1 rounded-full bg-emerald-500/90 text-white px-2 py-0.5 text-[9px] font-semibold">
            <Sparkles className="w-2.5 h-2.5" />
            {isRTL ? 'الأفضل' : 'Best'}
          </span>
        )}
      </div>

      <div className="min-w-0 flex-1 flex flex-col justify-center gap-1">
        <div className="flex items-center gap-1.5 flex-wrap">
          <h3 className="text-[13px] sm:text-[14px] font-semibold text-[var(--color-text-primary)] truncate" dir="auto">
            {prop.title}
          </h3>
          {prop.status && (
            <span className="text-[10px] px-1.5 py-0.5 rounded-full bg-[var(--color-surface-elevated)] text-[var(--color-text-muted)]">
              {prop.status}
            </span>
          )}
        </div>

        <p className="text-[11px] sm:text-[12px] text-[var(--color-text-muted)] flex items-center gap-1.5 truncate" dir="auto">
          <MapPin className="w-3 h-3 text-emerald-500 flex-shrink-0" />
          <span className="truncate">{prop.location}{prop.developer ? ` • ${prop.developer}` : ''}</span>
        </p>

        <div className="flex items-center gap-2.5 sm:gap-3 text-[10px] sm:text-[11px] text-[var(--color-text-secondary)] flex-wrap">
          {prop.metrics?.bedrooms > 0 && (
            <span className="inline-flex items-center gap-1">
              <Bed className="w-3 h-3" />
              {prop.metrics.bedrooms}
            </span>
          )}
          {prop.metrics?.bathrooms > 0 && (
            <span className="inline-flex items-center gap-1">
              <Bath className="w-3 h-3" />
              {prop.metrics.bathrooms}
            </span>
          )}
          {prop.metrics?.size > 0 && (
            <span className="inline-flex items-center gap-1">
              <Maximize className="w-3 h-3" />
              {prop.metrics.size} m2
            </span>
          )}
          {prop.metrics?.price_per_sqm > 0 && (
            <span className="inline-flex items-center gap-1 text-[var(--color-text-muted)]">
              {prop.metrics.price_per_sqm.toLocaleString()}/m2
            </span>
          )}
        </div>
      </div>

      <div className="flex flex-col justify-between items-end sm:min-w-[128px] border-s border-[var(--color-border)]/50 ps-2 sm:ps-3">
        <div className="text-end">
          <div className="text-[14px] sm:text-[16px] font-bold text-[var(--color-text-primary)] leading-tight">
            {(prop.price / 1_000_000).toFixed(1)}M
          </div>
          <div className="text-[10px] text-[var(--color-text-muted)]">EGP</div>
          {prop.metrics?.roi > 0 && (
            <div className="inline-flex items-center gap-1 text-[10px] font-semibold text-emerald-600 dark:text-emerald-400 mt-0.5">
              <TrendingUp className="w-3 h-3" /> +{prop.metrics.roi}% ROI
            </div>
          )}
        </div>

        <div className="flex items-center gap-1" dir="ltr">
          <button
            onClick={onSave}
            className={`p-1.5 rounded-lg transition-colors ${isSaved ? 'text-red-500 bg-red-500/10' : 'text-[var(--color-text-muted)] hover:text-red-500 hover:bg-red-500/10'}`}
            title={isSaved ? 'Saved' : 'Save'}
          >
            <Heart className="w-3.5 h-3.5" fill={isSaved ? 'currentColor' : 'none'} />
          </button>
          <button
            onClick={onValuation}
            className="p-1.5 rounded-lg text-[var(--color-text-muted)] hover:text-emerald-500 hover:bg-emerald-500/10 transition-colors"
            title="Run Valuation"
          >
            <BarChart2 className="w-3.5 h-3.5" />
          </button>
          <button
            onClick={onCompare}
            className="p-1.5 rounded-lg text-[var(--color-text-muted)] hover:text-blue-500 hover:bg-blue-500/10 transition-colors"
            title="Compare"
          >
            <Scale className="w-3.5 h-3.5" />
          </button>
        </div>
      </div>
    </motion.div>
  );
}

export default function BentoResultGrid({
  properties,
  analyticsContext,
  language,
  savedIds,
  onOpenDetails,
  onSave,
  onValuation,
  onCompare,
}: BentoResultGridProps) {
  if (!properties.length) return null;

  const isRTL = language === 'ar';
  const avgPrice = analyticsContext?.avg_price_sqm ?? 0;
  const growth = analyticsContext?.growth_rate ?? 0;
  const yield_ = analyticsContext?.rental_yield ?? 0;
  const showStats = !!analyticsContext?.has_analytics && (avgPrice > 0 || growth > 0 || yield_ > 0);

  return (
    <div className="mt-4 sm:mt-5" dir={isRTL ? 'rtl' : 'ltr'}>
      {showStats && (
        <div className="mb-2.5 sm:mb-3 flex flex-wrap gap-1.5">
          {avgPrice > 0 && (
            <QuickStat
              label={isRTL ? 'متوسط/م2' : 'Avg/m2'}
              value={`${avgPrice.toLocaleString()} EGP`}
            />
          )}
          {growth > 0 && (
            <QuickStat
              label={isRTL ? 'نمو سنوي' : 'YoY'}
              value={`+${(growth * 100).toFixed(0)}%`}
            />
          )}
          {yield_ > 0 && (
            <QuickStat
              label={isRTL ? 'عائد إيجاري' : 'Yield'}
              value={`${(yield_ * 100).toFixed(1)}%`}
            />
          )}
        </div>
      )}

      <div className="flex flex-col gap-2.5 sm:gap-3">
        {properties.map((prop, index) => (
          <PropertyLinePanel
            key={prop.id}
            prop={prop}
            index={index}
            isRTL={isRTL}
            isSaved={savedIds.has(String(prop.id))}
            onOpen={() => onOpenDetails(prop)}
            onSave={(e) => onSave(prop, e)}
            onValuation={(e) => onValuation(prop, e)}
            onCompare={(e) => onCompare(prop, e)}
          />
        ))}
      </div>
    </div>
  );
}
