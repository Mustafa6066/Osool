import { getProject, getProjectPriceHistory, getDeveloper, getArea } from '@/lib/seo-api';
import { projectJsonLd } from '@/lib/json-ld';
import type { Metadata } from 'next';
import Link from 'next/link';
import { notFound } from 'next/navigation';

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

  return (
    <main className="min-h-screen bg-[var(--color-background)] text-[var(--color-text-primary)]">
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(projectJsonLd(project)) }}
      />
      <div className="max-w-4xl mx-auto px-4 py-16">
        {/* Breadcrumb */}
        <nav className="text-sm text-[var(--color-text-muted)] mb-6 flex items-center gap-1">
          <Link href="/" className="hover:text-emerald-500">Home</Link>
          <span>/</span>
          <Link href="/projects" className="hover:text-emerald-500">Projects</Link>
          <span>/</span>
          <span className="text-[var(--color-text-primary)]">{project.name}</span>
        </nav>

        {/* Header */}
        <div className="mb-8">
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

        {/* KPI Cards */}
        <div className="grid sm:grid-cols-2 lg:grid-cols-4 gap-4 mb-10">
          {project.min_price_per_meter && project.max_price_per_meter && (
            <StatCard
              label="Price/m²"
              value={`${fmt(project.min_price_per_meter)} – ${fmt(project.max_price_per_meter)}`}
              unit="EGP"
            />
          )}
          {project.expected_delivery && (
            <StatCard label="Delivery" value={project.expected_delivery.slice(0, 10)} />
          )}
          {project.down_payment_min != null && (
            <StatCard label="Down Payment" value={`${project.down_payment_min}%`} />
          )}
          {project.installment_years != null && (
            <StatCard label="Installments" value={`${project.installment_years} years`} />
          )}
          {project.min_unit_size && project.max_unit_size && (
            <StatCard label="Unit Size" value={`${project.min_unit_size}–${project.max_unit_size} m²`} />
          )}
          {project.construction_progress != null && (
            <StatCard label="Progress" value={`${project.construction_progress}%`} />
          )}
        </div>

        {/* Amenities */}
        {project.amenities && (() => {
          let items: string[] = [];
          try { items = JSON.parse(project.amenities); } catch { /* ignore */ }
          return items.length > 0 ? (
          <section className="mb-10">
            <h2 className="text-xl font-semibold mb-4">Amenities</h2>
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
          <section className="mb-10">
            <h2 className="text-xl font-semibold mb-4">Price History (EGP/m²)</h2>
            <div className="overflow-x-auto rounded-xl border border-[var(--color-border)]">
              <table className="w-full text-sm">
                <thead className="bg-[var(--color-surface)]">
                  <tr>
                    <th className="p-3 text-left font-medium">Date</th>
                    <th className="p-3 text-right font-medium">Price/m²</th>
                    <th className="p-3 text-right font-medium">Source</th>
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
            Interested in {project.name}?
          </h3>
          <p className="text-sm text-[var(--color-text-muted)] mb-4">
            Ask our AI assistant for personalized pricing, availability, and investment analysis.
          </p>
          <Link
            href="/#chat"
            className="inline-block px-6 py-2 bg-emerald-500 text-white rounded-full font-medium hover:bg-emerald-600 transition-colors"
          >
            Chat with Osool AI
          </Link>
        </div>
      </div>
    </main>
  );
}

function StatCard({
  label,
  value,
  unit,
}: {
  label: string;
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
