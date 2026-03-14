import { getDevelopers } from '@/lib/seo-api';
import type { Developer } from '@/lib/seo-api';
import type { Metadata } from 'next';
import Link from 'next/link';
import SmartNav from '@/components/SmartNav';
import { developerBrief } from '@/lib/decision-support';

export const metadata: Metadata = {
  title: 'Top Egyptian Real Estate Developers — Ranked & Scored | Osool',
  description:
    'Compare Egypt\'s top property developers: Emaar Misr, Sodic, Orascom, Palm Hills, Mountain View, TMG & more. Delivery scores, finish quality, and resale retention.',
};

export const revalidate = 60;

function ScoreBar({ value, label }: { value: number; label: string }) {
  const color =
    value >= 85 ? 'bg-emerald-500' : value >= 70 ? 'bg-yellow-500' : 'bg-red-400';
  return (
    <div className="flex items-center gap-2 text-xs">
      <span className="w-20 text-[var(--color-text-muted)]">{label}</span>
      <div className="flex-1 h-1.5 rounded-full bg-[var(--color-border)]">
        <div className={`h-full rounded-full ${color}`} style={{ width: `${value}%` }} />
      </div>
      <span className="w-8 text-right font-medium">{value}</span>
    </div>
  );
}

export default async function DevelopersPage() {
  let developers: Developer[] = [];
  let loadError = false;

  try {
    developers = await getDevelopers();
  } catch {
    loadError = true;
  }

  return (
    <SmartNav>
    <main className="h-full overflow-y-auto bg-[var(--color-background)] text-[var(--color-text-primary)]">
      <div className="mx-auto flex max-w-7xl flex-col gap-8 px-4 py-8 sm:px-6 lg:px-8">
        <section className="grid gap-6 lg:grid-cols-[1fr_0.9fr] lg:items-start">
          <div className="rounded-[32px] border border-[var(--color-border)] bg-[var(--color-surface)] p-8">
            <div className="text-xs font-semibold uppercase tracking-[0.18em] text-emerald-600 dark:text-emerald-400">Developer trust board</div>
            <h1 className="mt-3 text-4xl font-semibold tracking-tight">Choose developers by confidence, not just brand familiarity.</h1>
            <p className="mt-4 max-w-2xl text-base leading-7 text-[var(--color-text-secondary)]">
              Compare Egypt&apos;s leading developers through the signals that matter most in a high-stakes purchase: delivery discipline,
              finish quality, resale resilience, and payment flexibility.
            </p>
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <div className="rounded-[28px] border border-[var(--color-border)] bg-[var(--color-surface)] p-5">
              <div className="text-[11px] font-semibold uppercase tracking-[0.18em] text-[var(--color-text-muted)]">Strategy view</div>
              <div className="mt-2 text-lg font-semibold">Trust-first, resale-led, and payment-flex options in one list.</div>
            </div>
            <div className="rounded-[28px] border border-[var(--color-border)] bg-[var(--color-surface)] p-5">
              <div className="text-[11px] font-semibold uppercase tracking-[0.18em] text-[var(--color-text-muted)]">Data rhythm</div>
              <div className="mt-2 text-lg font-semibold">Public SEO data, reframed for real decision support.</div>
            </div>
            <div className="rounded-[28px] border border-[var(--color-border)] bg-[var(--color-surface)] p-5 sm:col-span-2">
              <div className="flex flex-wrap gap-2 text-sm text-[var(--color-text-muted)]">
                <span className="rounded-full border border-[var(--color-border)] bg-[var(--color-background)] px-4 py-2">Lowest delivery risk</span>
                <span className="rounded-full border border-[var(--color-border)] bg-[var(--color-background)] px-4 py-2">Best resale premium</span>
                <span className="rounded-full border border-[var(--color-border)] bg-[var(--color-background)] px-4 py-2">Most flexible payments</span>
                <span className="rounded-full border border-[var(--color-border)] bg-[var(--color-background)] px-4 py-2">Best balanced option</span>
              </div>
            </div>
          </div>
        </section>

        {developers.length > 0 ? (
          <div className="grid gap-6 lg:grid-cols-2">
            {developers.map((dev, i) => (
              <Link
                key={dev.id}
                href={`/developers/${dev.slug}`}
                className="group block rounded-[28px] border border-[var(--color-border)] bg-[var(--color-surface)] p-6 transition-all hover:-translate-y-0.5 hover:border-emerald-500/40"
              >
                {(() => {
                  const brief = developerBrief(dev);
                  return (
                    <>
                      <div className="flex items-start justify-between gap-4">
                        <div>
                          <div className="flex items-center gap-2 mb-2">
                            <span className="text-xs font-bold text-emerald-500">#{i + 1}</span>
                            <span className="rounded-full bg-emerald-500/10 px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.16em] text-emerald-600 dark:text-emerald-400">
                              {brief.trustLabel}
                            </span>
                          </div>
                          <h2 className="text-2xl font-semibold tracking-tight group-hover:text-emerald-500 transition-colors">{dev.name}</h2>
                          <p className="mt-2 text-sm text-[var(--color-text-muted)]">
                            {dev.founded_year ? `Est. ${dev.founded_year}` : 'Established developer'}{dev.total_projects ? ` • ${dev.total_projects} projects` : ''}
                          </p>
                        </div>
                        <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-emerald-500/10 text-lg font-bold text-emerald-600 dark:text-emerald-400">
                          {dev.overall_score ?? '—'}
                        </div>
                      </div>

                      <div className="mt-5 rounded-2xl border border-[var(--color-border)] bg-[var(--color-background)] p-4">
                        <div className="text-sm font-semibold text-[var(--color-text-primary)]">{brief.verdict}</div>
                        <div className="mt-2 text-sm leading-6 text-[var(--color-text-secondary)]">Best for: {brief.bestFor}</div>
                        <div className="mt-2 text-xs leading-5 text-[var(--color-text-muted)]">{brief.risk}</div>
                      </div>

                      <div className="mt-5 space-y-2">
                        <ScoreBar value={dev.avg_delivery_score ?? 0} label="Delivery" />
                        <ScoreBar value={dev.avg_finish_quality ?? 0} label="Quality" />
                        <ScoreBar value={dev.avg_resale_retention ?? 0} label="Resale" />
                        <ScoreBar value={dev.payment_flexibility ?? 0} label="Payments" />
                      </div>
                    </>
                  );
                })()}
              </Link>
            ))}
          </div>
        ) : (
          <div className="rounded-[28px] border border-[var(--color-border)] bg-[var(--color-surface)] p-8 text-center">
            <h2 className="text-lg font-semibold mb-2">Developer data is not available yet</h2>
            <p className="text-sm text-[var(--color-text-muted)] max-w-2xl mx-auto">
              {loadError
                ? 'The public SEO API could not be loaded. A fresh deploy will retry the seed and page fetch.'
                : 'The backend returned no developer records. The seed bootstrap will repopulate this dataset on the next deploy.'}
            </p>
          </div>
        )}
      </div>
    </main>
    </SmartNav>
  );
}
