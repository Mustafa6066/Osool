/**
 * EnrichedContent — Renders AI-generated SEO body content from the Orchestrator.
 * Renders as rich HTML with proper bilingual support.
 */

import type { EnrichedSEOContent } from '@/lib/seo-content';
import Link from 'next/link';

interface Props {
  content: EnrichedSEOContent;
  locale?: 'en' | 'ar';
}

export function EnrichedBody({ content, locale = 'en' }: Props) {
  const body = content.seo.body;
  if (!body) return null;

  return (
    <section
      className="rounded-[28px] border border-[var(--color-border)] bg-[var(--color-surface)] p-6 md:p-8"
      dir={locale === 'ar' ? 'rtl' : 'ltr'}
    >
      <div
        className="prose prose-sm md:prose-base dark:prose-invert max-w-none
          prose-headings:text-[var(--color-text-primary)]
          prose-p:text-[var(--color-text-secondary)]
          prose-a:text-emerald-600 dark:prose-a:text-emerald-400
          prose-strong:text-[var(--color-text-primary)]"
        dangerouslySetInnerHTML={{ __html: body }}
      />
    </section>
  );
}

export function LivePropertyCards({
  properties,
}: {
  properties: NonNullable<EnrichedSEOContent['liveData']['topROIProperties']>;
}) {
  if (!properties?.length) return null;

  return (
    <section>
      <h2 className="text-xl font-semibold mb-4">Top ROI Listings</h2>
      <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-4">
        {properties.map((p) => (
          <Link
            key={p.id}
            href={`/property/${p.id}`}
            className="block p-5 rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] hover:border-emerald-500/50 transition-all"
          >
            <h3 className="font-semibold text-sm mb-1 line-clamp-2">{p.title}</h3>
            <div className="flex flex-wrap gap-1.5 text-xs text-[var(--color-text-muted)] mt-2">
              <span className="px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-600">
                {p.location}
              </span>
              <span className="px-2 py-0.5 rounded-full bg-blue-500/10 text-blue-600">
                {p.developer}
              </span>
              {p.bedrooms > 0 && (
                <span>{p.bedrooms} BR</span>
              )}
            </div>
            <div className="mt-3 flex items-baseline gap-2">
              <span className="text-lg font-bold text-emerald-500">
                EGP {p.price.toLocaleString()}
              </span>
              {p.roi_estimate != null && (
                <span className="text-xs text-purple-500 font-medium">
                  {p.roi_estimate.toFixed(1)}% ROI
                </span>
              )}
            </div>
            {p.price_per_sqm > 0 && (
              <div className="text-xs text-[var(--color-text-muted)] mt-1">
                {p.price_per_sqm.toLocaleString()} EGP/m²
              </div>
            )}
          </Link>
        ))}
      </div>
    </section>
  );
}
