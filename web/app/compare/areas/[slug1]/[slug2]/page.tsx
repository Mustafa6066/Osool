import { getArea, getAreaProjects, getAreaPriceHistory } from '@/lib/seo-api';
import { comparisonJsonLd } from '@/lib/json-ld';
import type { Metadata } from 'next';
import type React from 'react';
import Link from 'next/link';
import { notFound } from 'next/navigation';
import AppShell from '@/components/nav/AppShell';
import { areaBrief, formatRate, pickWinnerLabel } from '@/lib/decision-support';
import { T } from '@/components/T';

export const revalidate = 3600; // ISR: 1 hour

interface Props {
  params: Promise<{ slug1: string; slug2: string }>;
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { slug1, slug2 } = await params;
  try {
    const [a1, a2] = await Promise.all([getArea(slug1), getArea(slug2)]);
    return {
      title: `${a1.name} vs ${a2.name} — Area Investment Comparison | Osool`,
      description: `Compare ${a1.name} and ${a2.name}: price per sqm, YoY growth, rental yield, available projects.`,
    };
  } catch {
    return { title: 'Area Comparison | Osool' };
  }
}

export default async function AreaComparisonPage({ params }: Props) {
  const { slug1, slug2 } = await params;

  let a1, a2;
  try {
    [a1, a2] = await Promise.all([getArea(slug1), getArea(slug2)]);
  } catch {
    return notFound();
  }

  const [projects1, projects2, history1, history2] = await Promise.all([
    getAreaProjects(slug1).catch(() => []),
    getAreaProjects(slug2).catch(() => []),
    getAreaPriceHistory(slug1, 6).catch(() => []),
    getAreaPriceHistory(slug2, 6).catch(() => []),
  ]);

  const fmt = (n: number) => new Intl.NumberFormat('en-EG').format(Math.round(n));
  const pct = (n: number) => `${(n * 100).toFixed(1)}%`;

  const metrics: { label: React.ReactNode; v1: string; v2: string; raw1: number; raw2: number }[] = [
    {
      label: <T k="comparePage.avgPrice" />,
      v1: a1.avg_price_per_meter ? fmt(a1.avg_price_per_meter) : '—',
      v2: a2.avg_price_per_meter ? fmt(a2.avg_price_per_meter) : '—',
      raw1: a1.avg_price_per_meter ?? 0,
      raw2: a2.avg_price_per_meter ?? 0,
    },
    {
      label: <T k="comparePage.yoyGrowth" />,
      v1: a1.price_growth_ytd ? pct(a1.price_growth_ytd) : '—',
      v2: a2.price_growth_ytd ? pct(a2.price_growth_ytd) : '—',
      raw1: a1.price_growth_ytd ?? 0,
      raw2: a2.price_growth_ytd ?? 0,
    },
    {
      label: <T k="comparePage.rentalYield" />,
      v1: a1.rental_yield ? pct(a1.rental_yield) : '—',
      v2: a2.rental_yield ? pct(a2.rental_yield) : '—',
      raw1: a1.rental_yield ?? 0,
      raw2: a2.rental_yield ?? 0,
    },
    {
      label: <T k="comparePage.projectsListed" />,
      v1: String(projects1.length),
      v2: String(projects2.length),
      raw1: projects1.length,
      raw2: projects2.length,
    },
  ];

  const brief1 = areaBrief(a1);
  const brief2 = areaBrief(a2);
  const summaryCards = [
    {
      label: <T k="comparePage.bestYield" />,
      winner: pickWinnerLabel((a1.rental_yield ?? 0), (a2.rental_yield ?? 0), a1.name, a2.name),
      detail: `${a1.name}: ${formatRate(a1.rental_yield)} • ${a2.name}: ${formatRate(a2.rental_yield)}`,
    },
    {
      label: <T k="comparePage.bestAppreciation" />,
      winner: pickWinnerLabel((a1.price_growth_ytd ?? 0), (a2.price_growth_ytd ?? 0), a1.name, a2.name),
      detail: `${a1.name}: ${formatRate(a1.price_growth_ytd)} • ${a2.name}: ${formatRate(a2.price_growth_ytd)}`,
    },
    {
      label: <T k="comparePage.bestSupply" />,
      winner: pickWinnerLabel(projects1.length, projects2.length, a1.name, a2.name),
      detail: `${a1.name}: ${projects1.length} • ${a2.name}: ${projects2.length}`,
    },
  ];

  return (
    <AppShell>
    <main className="h-full overflow-y-auto bg-[var(--color-background)] text-[var(--color-text-primary)]">
      <div className="mx-auto flex max-w-6xl flex-col gap-8 px-4 py-8 sm:px-6 lg:px-8">
        {/* Breadcrumb */}
        <nav className="text-sm text-[var(--color-text-muted)] mb-6 flex items-center gap-1">
          <Link href="/" className="hover:text-emerald-500"><T k="comparePage.home" /></Link>
          <span>/</span>
          <Link href="/areas" className="hover:text-emerald-500"><T k="comparePage.areas" /></Link>
          <span>/</span>
          <span className="text-[var(--color-text-primary)]"><T k="comparePage.compare" /></span>
        </nav>

        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: JSON.stringify(comparisonJsonLd('areas', a1.name, a2.name, a1.slug, a2.slug)) }}
        />
        <h1 className="text-3xl font-bold mb-2">
          {a1.name} vs {a2.name}
        </h1>
        <p className="text-[var(--color-text-muted)]">
          <T k="comparePage.areaSideBySide" />
        </p>

        <section className="grid gap-4 md:grid-cols-3">
          {summaryCards.map((card, i) => (
            <div key={i} className="rounded-[28px] border border-[var(--color-border)] bg-[var(--color-surface)] p-5">
              <div className="text-[11px] font-semibold uppercase tracking-[0.18em] text-[var(--color-text-muted)]">{card.label}</div>
              <div className="mt-2 text-lg font-semibold">{card.winner}</div>
              <div className="mt-2 text-sm text-[var(--color-text-secondary)]">{card.detail}</div>
            </div>
          ))}
        </section>

        <section className="grid gap-4 md:grid-cols-2">
          <div className="rounded-[28px] border border-[var(--color-border)] bg-[var(--color-surface)] p-5">
            <div className="text-sm font-semibold text-[var(--color-text-primary)]">{a1.name}</div>
            <div className="mt-2 text-sm leading-6 text-[var(--color-text-secondary)]">{brief1.thesis}</div>
            <div className="mt-2 text-xs leading-5 text-[var(--color-text-muted)]"><T k="areaPage.bestFor" />: {brief1.bestFor}</div>
          </div>
          <div className="rounded-[28px] border border-[var(--color-border)] bg-[var(--color-surface)] p-5">
            <div className="text-sm font-semibold text-[var(--color-text-primary)]">{a2.name}</div>
            <div className="mt-2 text-sm leading-6 text-[var(--color-text-secondary)]">{brief2.thesis}</div>
            <div className="mt-2 text-xs leading-5 text-[var(--color-text-muted)]"><T k="areaPage.bestFor" />: {brief2.bestFor}</div>
          </div>
        </section>

        {/* Metrics Table */}
        <div className="rounded-2xl border border-[var(--color-border)] overflow-hidden mb-10">
          <table className="w-full text-sm">
            <thead className="bg-[var(--color-surface)]">
              <tr>
                <th className="p-4 text-left font-medium"><T k="comparePage.metric" /></th>
                <th className="p-4 text-center font-medium">
                  <Link href={`/areas/${a1.slug}`} className="hover:text-emerald-500">{a1.name}</Link>
                </th>
                <th className="p-4 text-center font-medium">
                  <Link href={`/areas/${a2.slug}`} className="hover:text-emerald-500">{a2.name}</Link>
                </th>
                <th className="p-4 text-center font-medium"><T k="comparePage.advantage" /></th>
              </tr>
            </thead>
            <tbody>
              {metrics.map((m, i) => {
                const winner =
                  m.raw1 > m.raw2 ? 1 : m.raw2 > m.raw1 ? 2 : 0;
                return (
                  <tr key={i} className="border-t border-[var(--color-border)]">
                    <td className="p-4 font-medium">{m.label}</td>
                    <td className={`p-4 text-center font-mono ${winner === 1 ? 'text-emerald-500 font-bold' : ''}`}>
                      {m.v1}
                    </td>
                    <td className={`p-4 text-center font-mono ${winner === 2 ? 'text-emerald-500 font-bold' : ''}`}>
                      {m.v2}
                    </td>
                    <td className="p-4 text-center text-xs">
                      {winner === 1
                        ? `✅ ${a1.name}`
                        : winner === 2
                          ? `✅ ${a2.name}`
                          : <T k="comparePage.tie" />}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>

        {/* Price History Side-by-Side */}
        {(history1.length > 0 || history2.length > 0) && (
          <section className="mb-10">
            <h2 className="text-xl font-semibold mb-4"><T k="comparePage.recentPriceHistory" /></h2>
            <div className="grid md:grid-cols-2 gap-6">
              <PriceTable name={a1.name} history={history1} />
              <PriceTable name={a2.name} history={history2} />
            </div>
          </section>
        )}

        {/* Projects Side-by-Side */}
        <h2 className="text-xl font-semibold mb-4"><T k="comparePage.availableProjects" /></h2>
        <div className="grid md:grid-cols-2 gap-6 mb-10">
          <ProjectColumn name={a1.name} projects={projects1} />
          <ProjectColumn name={a2.name} projects={projects2} />
        </div>

        {/* CTA */}
        <div className="bg-emerald-500/10 border border-emerald-500/20 rounded-2xl p-6 text-center">
          <h3 className="text-lg font-semibold mb-2"><T k="comparePage.whichArea" /></h3>
          <p className="text-sm text-[var(--color-text-muted)] mb-4">
            <T k="comparePage.areaAdvisor" />
          </p>
          <Link
            href="/chat"
            className="inline-block px-6 py-2 bg-emerald-500 text-white rounded-full font-medium hover:bg-emerald-600 transition-colors"
          >
            <T k="comparePage.chatWithAI" />
          </Link>
        </div>
      </div>
    </main>
    </AppShell>
  );
}

function PriceTable({
  name,
  history,
}: {
  name: string;
  history: Array<{ id: number; date: string; price_per_m2: number }>;
}) {
  if (history.length === 0) return <p className="text-sm text-[var(--color-text-muted)]">No price history for {name}.</p>;
  const fmt = (n: number) => new Intl.NumberFormat('en-EG').format(Math.round(n));
  return (
    <div>
      <h3 className="text-sm font-medium mb-2">{name}</h3>
      <div className="overflow-x-auto rounded-xl border border-[var(--color-border)]">
        <table className="w-full text-xs">
          <thead className="bg-[var(--color-surface)]">
            <tr>
              <th className="p-2 text-left">Date</th>
              <th className="p-2 text-right">EGP/m²</th>
            </tr>
          </thead>
          <tbody>
            {history.map((h) => (
              <tr key={h.id} className="border-t border-[var(--color-border)]">
                <td className="p-2">{h.date}</td>
                <td className="p-2 text-right font-mono">{fmt(h.price_per_m2)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}

function ProjectColumn({
  name,
  projects,
}: {
  name: string;
  projects: Array<{ slug: string; name: string; project_type?: string; min_price_per_meter?: number; max_price_per_meter?: number }>;
}) {
  if (projects.length === 0) return <p className="text-sm text-[var(--color-text-muted)]">No projects in {name}.</p>;
  const fmt = (n: number) => new Intl.NumberFormat('en-EG').format(Math.round(n));
  return (
    <div className="space-y-2">
      {projects.map((p) => (
        <Link
          key={p.slug}
          href={`/projects/${p.slug}`}
          className="block p-3 rounded-lg border border-[var(--color-border)] hover:border-emerald-500/50 transition-colors"
        >
          <p className="font-medium text-sm">{p.name}</p>
          <p className="text-xs text-[var(--color-text-muted)]">
            {p.project_type}
            {p.min_price_per_meter && p.max_price_per_meter && (
              <> · EGP {fmt(p.min_price_per_meter)} – {fmt(p.max_price_per_meter)} /m²</>
            )}
          </p>
        </Link>
      ))}
    </div>
  );
}
