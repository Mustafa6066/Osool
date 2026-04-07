import { getAreas } from '@/lib/seo-api';
import type { Area } from '@/lib/seo-api';
import type { Metadata } from 'next';
import Link from 'next/link';
import AppShell from '@/components/nav/AppShell';
import { areaBrief, formatRate } from '@/lib/decision-support';
import { T } from '@/components/T';

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
    <AppShell>
    <main className="h-full overflow-y-auto bg-[var(--color-background)] text-[var(--color-text-primary)]">
      <div className="mx-auto flex max-w-7xl flex-col gap-8 px-4 py-8 sm:px-6 lg:px-8">
        <section className="grid gap-6 lg:grid-cols-[1fr_0.9fr] lg:items-start">
          <div className="rounded-[32px] border border-[var(--color-border)] bg-[var(--color-surface)] p-8">
            <div className="text-xs font-semibold uppercase tracking-[0.18em] text-emerald-600 dark:text-emerald-400"><T k="areaPage.badge" /></div>
            <h1 className="mt-3 text-4xl font-semibold tracking-tight"><T k="areaPage.heroTitle" /></h1>
            <p className="mt-4 max-w-2xl text-base leading-7 text-[var(--color-text-secondary)]">
              <T k="areaPage.heroDesc" />
            </p>
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <div className="rounded-[28px] border border-[var(--color-border)] bg-[var(--color-surface)] p-5">
              <div className="text-[11px] font-semibold uppercase tracking-[0.18em] text-[var(--color-text-muted)]"><T k="areaPage.modes" /></div>
              <div className="mt-2 text-lg font-semibold"><T k="areaPage.modesDesc" /></div>
            </div>
            <div className="rounded-[28px] border border-[var(--color-border)] bg-[var(--color-surface)] p-5">
              <div className="text-[11px] font-semibold uppercase tracking-[0.18em] text-[var(--color-text-muted)]"><T k="areaPage.decisionGoal" /></div>
              <div className="mt-2 text-lg font-semibold"><T k="areaPage.decisionGoalDesc" /></div>
            </div>
            <div className="rounded-[28px] border border-[var(--color-border)] bg-[var(--color-surface)] p-5 sm:col-span-2">
              <div className="flex flex-wrap gap-2 text-sm text-[var(--color-text-muted)]">
                <span className="rounded-full border border-[var(--color-border)] bg-[var(--color-background)] px-4 py-2"><T k="areaPage.yieldLed" /></span>
                <span className="rounded-full border border-[var(--color-border)] bg-[var(--color-background)] px-4 py-2"><T k="areaPage.appreciationLed" /></span>
                <span className="rounded-full border border-[var(--color-border)] bg-[var(--color-background)] px-4 py-2"><T k="areaPage.stabilityLed" /></span>
                <span className="rounded-full border border-[var(--color-border)] bg-[var(--color-background)] px-4 py-2"><T k="areaPage.balanced" /></span>
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
                        <div className="mt-2 text-sm leading-6 text-[var(--color-text-secondary)]"><T k="areaPage.bestFor" />: {brief.bestFor}</div>
                        <div className="mt-2 text-xs leading-5 text-[var(--color-text-muted)]">{brief.risk}</div>
                      </div>

                      <div className="mt-4 grid grid-cols-3 gap-3 text-center">
                        <div className="rounded-2xl border border-[var(--color-border)] bg-[var(--color-background)] p-3">
                          <div className="text-lg font-bold text-emerald-500">{area.avg_price_per_meter ? `${(area.avg_price_per_meter / 1000).toFixed(0)}K` : '—'}</div>
                          <div className="text-[10px] text-[var(--color-text-muted)] uppercase tracking-[0.15em]"><T k="areaPage.egpSqm" /></div>
                        </div>
                        <div className="rounded-2xl border border-[var(--color-border)] bg-[var(--color-background)] p-3">
                          <div className="text-lg font-bold text-[var(--color-primary-dark)]">{formatRate(area.price_growth_ytd)}</div>
                          <div className="text-[10px] text-[var(--color-text-muted)] uppercase tracking-[0.15em]"><T k="areaPage.growth" /></div>
                        </div>
                        <div className="rounded-2xl border border-[var(--color-border)] bg-[var(--color-background)] p-3">
                          <div className="text-lg font-bold text-[var(--color-teal-accent)]">{formatRate(area.rental_yield)}</div>
                          <div className="text-[10px] text-[var(--color-text-muted)] uppercase tracking-[0.15em]"><T k="areaPage.yield" /></div>
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
            <h2 className="text-lg font-semibold mb-2"><T k="areaPage.noData" /></h2>
            <p className="text-sm text-[var(--color-text-muted)] max-w-2xl mx-auto">
              {loadError
                ? <T k="areaPage.noDataError" />
                : <T k="areaPage.noDataEmpty" />}
            </p>
          </div>
        )}
      </div>
    </main>
    </AppShell>
  );
}
