import { getAreas } from '@/lib/seo-api';
import type { Area } from '@/lib/seo-api';
import type { Metadata } from 'next';
import Link from 'next/link';
import PublicPageNav from '@/components/PublicPageNav';
import { areaBrief, formatRate } from '@/lib/decision-support';

export const metadata: Metadata = {
  title: 'Best Investment Areas in Egypt — Prices, Growth & Yield | Osool',
  description:
    'Compare Egypt\'s top investment zones: Sheikh Zayed, New Capital, Ras El Hikma, Ain Sokhna, North Coast & more. Price per sqm, appreciation rates, rental yields.',
};

export const revalidate = 60;

export default async function AreasPage() {
  let areas: Area[] = [];
  let loadError = false;

  try {
    areas = await getAreas();
  } catch {
    loadError = true;
  }

  return (
    <PublicPageNav>
    <main className="h-full overflow-y-auto bg-[var(--color-background)] text-[var(--color-text-primary)]">
      <div className="mx-auto flex max-w-7xl flex-col gap-8 px-4 py-8 sm:px-6 lg:px-8">
        <section className="grid gap-6 lg:grid-cols-[1fr_0.9fr] lg:items-start">
          <div className="rounded-[32px] border border-[var(--color-border)] bg-[var(--color-surface)] p-8">
            <div className="text-xs font-semibold uppercase tracking-[0.18em] text-emerald-600 dark:text-emerald-400">Area strategy map</div>
            <h1 className="mt-3 text-4xl font-semibold tracking-tight">Browse Egyptian investment areas by strategy, not just by headline metrics.</h1>
            <p className="mt-4 max-w-2xl text-base leading-7 text-[var(--color-text-secondary)]">
              Use Osool&apos;s area view to separate yield-led corridors, appreciation plays, and steadier entry zones before you go deeper into specific projects.
            </p>
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <div className="rounded-[28px] border border-[var(--color-border)] bg-[var(--color-surface)] p-5">
              <div className="text-[11px] font-semibold uppercase tracking-[0.18em] text-[var(--color-text-muted)]">Modes</div>
              <div className="mt-2 text-lg font-semibold">Yield, appreciation, stability, and balanced entry.</div>
            </div>
            <div className="rounded-[28px] border border-[var(--color-border)] bg-[var(--color-surface)] p-5">
              <div className="text-[11px] font-semibold uppercase tracking-[0.18em] text-[var(--color-text-muted)]">Decision goal</div>
              <div className="mt-2 text-lg font-semibold">Move from corridor curiosity to a shortlist-worthy area thesis.</div>
            </div>
            <div className="rounded-[28px] border border-[var(--color-border)] bg-[var(--color-surface)] p-5 sm:col-span-2">
              <div className="flex flex-wrap gap-2 text-sm text-[var(--color-text-muted)]">
                <span className="rounded-full border border-[var(--color-border)] bg-[var(--color-background)] px-4 py-2">Yield-led</span>
                <span className="rounded-full border border-[var(--color-border)] bg-[var(--color-background)] px-4 py-2">Appreciation-led</span>
                <span className="rounded-full border border-[var(--color-border)] bg-[var(--color-background)] px-4 py-2">Stability-led</span>
                <span className="rounded-full border border-[var(--color-border)] bg-[var(--color-background)] px-4 py-2">Balanced</span>
              </div>
            </div>
          </div>
        </section>

        {areas.length > 0 ? (
          <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-3">
            {areas.map((area) => (
              <Link
                key={area.id}
                href={`/areas/${area.slug}`}
                className="group block rounded-[28px] border border-[var(--color-border)] bg-[var(--color-surface)] p-5 transition-all hover:-translate-y-0.5 hover:border-emerald-500/40"
              >
                {(() => {
                  const brief = areaBrief(area);
                  return (
                    <>
                      <div className="flex items-start justify-between gap-3">
                        <div>
                          <h2 className="text-2xl font-semibold tracking-tight group-hover:text-emerald-500 transition-colors">{area.name}</h2>
                          <p className="mt-1 text-sm text-[var(--color-text-muted)]">{area.city || 'Egypt'}</p>
                        </div>
                        <span className="rounded-full bg-emerald-500/10 px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.16em] text-emerald-600 dark:text-emerald-400">
                          {brief.strategy}
                        </span>
                      </div>

                      <div className="mt-4 rounded-2xl border border-[var(--color-border)] bg-[var(--color-background)] p-4">
                        <div className="text-sm font-semibold text-[var(--color-text-primary)]">{brief.thesis}</div>
                        <div className="mt-2 text-sm leading-6 text-[var(--color-text-secondary)]">Best for: {brief.bestFor}</div>
                        <div className="mt-2 text-xs leading-5 text-[var(--color-text-muted)]">{brief.risk}</div>
                      </div>

                      <div className="mt-4 grid grid-cols-3 gap-3 text-center">
                        <div className="rounded-2xl border border-[var(--color-border)] bg-[var(--color-background)] p-3">
                          <div className="text-lg font-bold text-emerald-500">{area.avg_price_per_meter ? `${(area.avg_price_per_meter / 1000).toFixed(0)}K` : '—'}</div>
                          <div className="text-[10px] text-[var(--color-text-muted)] uppercase tracking-[0.15em]">EGP/m²</div>
                        </div>
                        <div className="rounded-2xl border border-[var(--color-border)] bg-[var(--color-background)] p-3">
                          <div className="text-lg font-bold text-blue-500">{formatRate(area.price_growth_ytd)}</div>
                          <div className="text-[10px] text-[var(--color-text-muted)] uppercase tracking-[0.15em]">Growth</div>
                        </div>
                        <div className="rounded-2xl border border-[var(--color-border)] bg-[var(--color-background)] p-3">
                          <div className="text-lg font-bold text-violet-500">{formatRate(area.rental_yield)}</div>
                          <div className="text-[10px] text-[var(--color-text-muted)] uppercase tracking-[0.15em]">Yield</div>
                        </div>
                      </div>
                    </>
                  );
                })()}
              </Link>
            ))}
          </div>
        ) : (
          <div className="rounded-[28px] border border-[var(--color-border)] bg-[var(--color-surface)] p-8 text-center">
            <h2 className="text-lg font-semibold mb-2">Area data is not available yet</h2>
            <p className="text-sm text-[var(--color-text-muted)] max-w-2xl mx-auto">
              {loadError
                ? 'The public SEO API could not be loaded. A fresh deploy will retry the seed and page fetch.'
                : 'The backend returned no area records. The seed bootstrap will repopulate this dataset on the next deploy.'}
            </p>
          </div>
        )}
      </div>
    </main>
    </PublicPageNav>
  );
}
