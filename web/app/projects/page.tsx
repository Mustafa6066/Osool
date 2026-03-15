import { getProjects } from '@/lib/seo-api';
import type { Metadata } from 'next';
import Link from 'next/link';
import AppShell from '@/components/nav/AppShell';
import { formatPriceBand, projectBrief } from '@/lib/decision-support';
import { T } from '@/components/T';

export const metadata: Metadata = {
  title: 'Egyptian Real Estate Projects â€” Prices & Payment Plans | Osool',
  description:
    'Browse 30+ verified Egyptian real estate projects: compounds, resorts, towers. Filter by area, developer, price, and bedrooms. Updated weekly.',
};

export default async function ProjectsPage() {
  const projects = await getProjects().catch(() => []);

  return (
    <AppShell>
    <main className="h-full overflow-y-auto bg-[var(--color-background)] text-[var(--color-text-primary)]">
      <div className="mx-auto flex max-w-7xl flex-col gap-8 px-4 py-8 sm:px-6 lg:px-8">
        <section className="grid gap-6 lg:grid-cols-[1fr_0.9fr] lg:items-start">
          <div className="rounded-[32px] border border-[var(--color-border)] bg-[var(--color-surface)] p-8">
            <div className="text-xs font-semibold uppercase tracking-[0.18em] text-emerald-600 dark:text-emerald-400"><T k="projPage.badge" /></div>
            <h1 className="mt-3 text-4xl font-semibold tracking-tight"><T k="projPage.heroTitle" /></h1>
            <p className="mt-4 max-w-2xl text-base leading-7 text-[var(--color-text-secondary)]">
              <T k="projPage.heroDesc" />
            </p>
          </div>

          <div className="grid gap-4 sm:grid-cols-2">
            <div className="rounded-[28px] border border-[var(--color-border)] bg-[var(--color-surface)] p-5">
              <div className="text-[11px] font-semibold uppercase tracking-[0.18em] text-[var(--color-text-muted)]"><T k="projPage.focusAreas" /></div>
              <div className="mt-2 text-lg font-semibold"><T k="projPage.focusAreasDesc" /></div>
            </div>
            <div className="rounded-[28px] border border-[var(--color-border)] bg-[var(--color-surface)] p-5">
              <div className="text-[11px] font-semibold uppercase tracking-[0.18em] text-[var(--color-text-muted)]"><T k="projPage.useThisFor" /></div>
              <div className="mt-2 text-lg font-semibold"><T k="projPage.useThisForDesc" /></div>
            </div>
          </div>
        </section>

        <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-3">
          {projects.map((p) => (
            <Link
              key={p.id}
              href={`/projects/${p.slug}`}
              className="group block rounded-[28px] border border-[var(--color-border)] bg-[var(--color-surface)] p-5 transition-all hover:-translate-y-0.5 hover:border-emerald-500/40"
            >
              {(() => {
                const brief = projectBrief(p);
                return (
                  <>
                    <div className="flex flex-wrap items-center gap-2">
                      {p.project_type && (
                        <span className="rounded-full bg-emerald-500/10 px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.16em] text-emerald-600 dark:text-emerald-400">
                          {p.project_type}
                        </span>
                      )}
                      {p.status && (
                        <span className="rounded-full bg-blue-500/10 px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.16em] text-blue-600 dark:text-blue-400">
                          {p.status}
                        </span>
                      )}
                    </div>

                    <h2 className="mt-4 text-2xl font-semibold tracking-tight group-hover:text-emerald-500 transition-colors">{p.name}</h2>
                    {p.name_ar && <p className="mt-1 text-sm text-[var(--color-text-muted)]" dir="rtl">{p.name_ar}</p>}

                    <div className="mt-4 rounded-2xl border border-[var(--color-border)] bg-[var(--color-background)] p-4">
                      <div className="text-sm font-semibold text-[var(--color-text-primary)]">{brief.thesis}</div>
                      <div className="mt-2 text-sm leading-6 text-[var(--color-text-secondary)]"><T k="projPage.bestFor" />: {brief.bestFor}</div>
                      <div className="mt-2 text-xs leading-5 text-[var(--color-text-muted)]">{brief.risk}</div>
                    </div>

                    <div className="mt-4 space-y-2 text-sm text-[var(--color-text-secondary)]">
                      <div>{formatPriceBand(p.min_price_per_meter, p.max_price_per_meter)}</div>
                      {p.expected_delivery && <div><T k="projPage.delivery" /> {new Date(p.expected_delivery).getFullYear()}</div>}
                      {p.min_unit_size && p.max_unit_size && <div>{p.min_unit_size}-{p.max_unit_size} mÂ²</div>}
                      {p.down_payment_min != null && p.installment_years != null && <div>{p.down_payment_min}% down â€¢ {p.installment_years} years</div>}
                    </div>
                  </>
                );
              })()}
            </Link>
          ))}
        </div>
      </div>
    </main>
    </AppShell>
  );
}
