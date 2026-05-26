import { getProject, getProjectPriceHistory, getDeveloper, getArea } from '@/lib/seo-api';
import { projectJsonLd } from '@/lib/json-ld';
import type { Metadata } from 'next';
import Link from 'next/link';
import { notFound } from 'next/navigation';
import AppShell from '@/components/nav/AppShell';
import { areaBrief, developerBrief, formatPriceBand, formatRate, projectBrief } from '@/lib/decision-support';
import { T } from '@/components/T';

export const revalidate = 3600; // ISR: 1 hour

interface Props {
  params: Promise<{ slug: string }>;
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { slug } = await params;
  try {
    const p = await getProject(slug);
    return {
      title: `${p.name} — Prices, Payment Plans & Reviews | Osool`,
      description: `${p.name} ${p.project_type ?? 'project'} in Egypt: EGP pricing, down-payment options, delivery ${p.expected_delivery ?? 'TBA'}, amenities, and investment potential.`,
    };
  } catch {
    return { title: 'Project Not Found | Osool' };
  }
}

export default async function ProjectDetailPage({ params }: Props) {
  const { slug } = await params;

  let project;
  try {
    project = await getProject(slug);
  } catch {
    return notFound();
  }

  // Fetch supplementary data in parallel
  const [priceHistory, developer, area] = await Promise.all([
    getProjectPriceHistory(slug, 12).catch(() => []),
    project.developer_id
      ? getDeveloper(String(project.developer_id)).catch(() => null)
      : Promise.resolve(null),
    project.area_id
      ? getArea(String(project.area_id)).catch(() => null)
      : Promise.resolve(null),
  ]);

  const fmt = (n: number) =>
    new Intl.NumberFormat('en-EG').format(Math.round(n));

  const brief = projectBrief(project);
  const developerSummary = developer ? developerBrief(developer) : null;
  const areaSummary = area ? areaBrief(area) : null;

  return (
    <AppShell>
    <main className="h-full overflow-y-auto bg-[var(--color-background)] text-[var(--color-text-primary)]">
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(projectJsonLd(project)) }}
      />
      <div className="mx-auto flex max-w-6xl flex-col gap-8 px-4 py-8 sm:px-6 lg:px-8">
        {/* Breadcrumb */}
        <nav className="text-sm text-[var(--color-text-muted)] mb-6 flex items-center gap-1">
          <Link href="/" className="hover:text-emerald-500"><T k="comparePage.home" /></Link>
          <span>/</span>
          <Link href="/projects" className="hover:text-emerald-500"><T k="projPage.badge" /></Link>
          <span>/</span>
          <span className="text-[var(--color-text-primary)]">{project.name}</span>
        </nav>

        {/* Header */}
        <section className="grid gap-6 lg:grid-cols-[1fr_0.9fr] lg:items-start">
        <div className="rounded-[32px] border border-[var(--color-border)] bg-[var(--color-surface)] p-8">
          <div className="flex items-center gap-2 mb-2">
            {project.project_type && (
              <span className="px-2 py-0.5 text-xs rounded-full bg-emerald-500/10 text-emerald-600 font-medium">
                {project.project_type}
              </span>
            )}
            {project.status && (
              <span className="px-2 py-0.5 text-xs rounded-full bg-blue-500/10 text-blue-600 font-medium">
                {project.status}
              </span>
            )}
          </div>
          <h1 className="text-3xl font-bold">{project.name}</h1>
          {project.name_ar && (
            <p className="text-xl text-[var(--color-text-muted)] mt-1" dir="rtl">
              {project.name_ar}
            </p>
          )}
          <p className="mt-5 text-base leading-7 text-[var(--color-text-secondary)]">{brief.thesis}</p>

          {/* Developer & Area links */}
          <div className="flex flex-wrap gap-4 mt-3 text-sm text-[var(--color-text-secondary)]">
            {developer && (
              <Link href={`/developers/${(developer as { slug: string }).slug}`} className="hover:text-emerald-500">
                🏗️ {(developer as { name: string }).name}
              </Link>
            )}
            {area && (
              <Link href={`/areas/${(area as { slug: string }).slug}`} className="hover:text-emerald-500">
                📍 {(area as { name: string }).name}
              </Link>
            )}
          </div>
        </div>

        <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-1">
          <div className="rounded-[28px] border border-[var(--color-border)] bg-[var(--color-surface)] p-5">
            <div className="text-[11px] font-semibold uppercase tracking-[0.18em] text-[var(--color-text-muted)]"><T k="projPage.bestFor" /></div>
            <div className="mt-2 text-base font-semibold">{brief.bestFor}</div>
          </div>
          <div className="rounded-[28px] border border-[var(--color-border)] bg-[var(--color-surface)] p-5">
            <div className="text-[11px] font-semibold uppercase tracking-[0.18em] text-[var(--color-text-muted)]"><T k="projPage.mainWatchout" /></div>
            <div className="mt-2 text-base font-semibold">{brief.risk}</div>
          </div>
        </div>
        </section>

        {/* KPI Cards */}
        <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {project.min_price_per_meter && project.max_price_per_meter && (
            <StatCard
              label={<T k="projPage.pricePerSqm" />}
              value={`${fmt(project.min_price_per_meter)} – ${fmt(project.max_price_per_meter)}`}
              unit="EGP"
            />
          )}
          {project.expected_delivery && (
            <StatCard label={<T k="projPage.delivery" />} value={project.expected_delivery.slice(0, 10)} />
          )}
          {project.down_payment_min != null && (
            <StatCard label={<T k="projPage.downPayment" />} value={`${project.down_payment_min}%`} />
          )}
          {project.installment_years != null && (
            <StatCard label={<T k="projPage.installments" />} value={`${project.installment_years} years`} />
          )}
          {project.min_unit_size && project.max_unit_size && (
            <StatCard label={<T k="projPage.unitSize" />} value={`${project.min_unit_size}–${project.max_unit_size} m²`} />
          )}
          {project.construction_progress != null && (
            <StatCard label={<T k="projPage.progress" />} value={`${project.construction_progress}%`} />
          )}
        </div>

        <section className="grid gap-4 md:grid-cols-2">
          {developerSummary && (
            <div className="rounded-[28px] border border-[var(--color-border)] bg-[var(--color-surface)] p-6">
              <div className="text-[11px] font-semibold uppercase tracking-[0.18em] text-[var(--color-text-muted)]"><T k="projPage.developerContext" /></div>
              <div className="mt-2 text-lg font-semibold">{developerSummary.verdict}</div>
              <div className="mt-2 text-sm text-[var(--color-text-secondary)]">{developerSummary.bestFor}</div>
            </div>
          )}
          {areaSummary && (
            <div className="rounded-[28px] border border-[var(--color-border)] bg-[var(--color-surface)] p-6">
              <div className="text-[11px] font-semibold uppercase tracking-[0.18em] text-[var(--color-text-muted)]"><T k="projPage.areaContext" /></div>
              <div className="mt-2 text-lg font-semibold">{areaSummary.thesis}</div>
              <div className="mt-2 text-sm text-[var(--color-text-secondary)]">{areaSummary.bestFor}</div>
            </div>
          )}
        </section>

        {/* Amenities */}
        {project.amenities && (() => {
          let items: string[] = [];
          try { items = JSON.parse(project.amenities); } catch { /* ignore */ }
          return items.length > 0 ? (
          <section className="mb-10">
            <h2 className="text-xl font-semibold mb-4"><T k="projPage.amenities" /></h2>
            <div className="flex flex-wrap gap-2">
              {items.map((a: string) => (
                <span
                  key={a}
                  className="text-sm px-3 py-1 rounded-full bg-[var(--color-surface)] border border-[var(--color-border)] text-[var(--color-text-secondary)]"
                >
                  {a}
                </span>
              ))}
            </div>
          </section>
          ) : null;
        })()}

        {/* Price History Table */}
        {priceHistory.length > 0 && (
          <section className="rounded-[28px] border border-[var(--color-border)] bg-[var(--color-surface)] p-6">
            <h2 className="text-xl font-semibold mb-4"><T k="projPage.priceHistory" /></h2>
            <p className="mb-4 text-sm leading-6 text-[var(--color-text-secondary)]">
              <T k="projPage.priceHistoryNote" />
            </p>
            <div className="overflow-x-auto rounded-xl border border-[var(--color-border)]">
              <table className="w-full text-sm">
                <thead className="bg-[var(--color-surface)]">
                  <tr>
                    <th className="p-3 text-left font-medium"><T k="projPage.date" /></th>
                    <th className="p-3 text-right font-medium"><T k="projPage.priceSqm" /></th>
                    <th className="p-3 text-right font-medium"><T k="projPage.source" /></th>
                  </tr>
                </thead>
                <tbody>
                  {priceHistory.map((h) => (
                    <tr key={h.id} className="border-t border-[var(--color-border)]">
                      <td className="p-3">{h.date}</td>
                      <td className="p-3 text-right font-mono">
                        {fmt(h.price_per_m2)}
                      </td>
                      <td className="p-3 text-right">
                        —
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        )}

        {/* CTA */}
        <div className="bg-emerald-500/10 border border-emerald-500/20 rounded-2xl p-6 text-center">
          <h3 className="text-lg font-semibold mb-2">
            <T k="projPage.interested" /> {project.name}?
          </h3>
          <p className="text-sm text-[var(--color-text-muted)] mb-4">
            <T k="projPage.askAdvisor" />
          </p>
          <Link
            href="/chat"
            className="inline-block px-6 py-2 bg-emerald-500 text-white rounded-full font-medium hover:bg-emerald-600 transition-colors"
          >
            <T k="projPage.chatWithAI" />
          </Link>
        </div>
      </div>
    </main>
    </AppShell>
  );
}

function StatCard({
  label,
  value,
  unit,
}: {
  label: React.ReactNode;
  value: string;
  unit?: string;
}) {
  return (
    <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-4">
      <p className="text-xs text-[var(--color-text-muted)] mb-1">{label}</p>
      <p className="text-lg font-bold">
        {value}
        {unit && <span className="text-xs font-normal ml-1 text-[var(--color-text-muted)]">{unit}</span>}
      </p>
    </div>
  );
}
