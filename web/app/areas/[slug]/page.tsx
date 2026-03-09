import { getArea, getAreaProjects, getAreaPriceHistory } from '@/lib/seo-api';
import type { Metadata } from 'next';
import Link from 'next/link';
import { notFound } from 'next/navigation';

interface Props {
  params: Promise<{ slug: string }>;
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { slug } = await params;
  try {
    const area = await getArea(slug);
    return {
      title: `Invest in ${area.name}: Prices, Projects & Guide | Osool`,
      description: area.description?.slice(0, 160),
    };
  } catch {
    return { title: 'Area Not Found | Osool' };
  }
}

export default async function AreaPage({ params }: Props) {
  const { slug } = await params;
  let area, projects, priceHistory;
  try {
    [area, projects, priceHistory] = await Promise.all([
      getArea(slug),
      getAreaProjects(slug),
      getAreaPriceHistory(slug),
    ]);
  } catch {
    notFound();
  }

  return (
    <main className="min-h-screen bg-[var(--color-background)] text-[var(--color-text-primary)]">
      <div className="max-w-5xl mx-auto px-4 py-16">
        <nav className="text-sm text-[var(--color-text-muted)] mb-6">
          <Link href="/areas" className="hover:text-emerald-500">Areas</Link>
          <span className="mx-2">/</span>
          <span>{area.name}</span>
        </nav>

        <h1 className="text-3xl font-bold mb-2">{area.name}</h1>
        {area.name_ar && (
          <p className="text-lg text-[var(--color-text-muted)] mb-4" dir="rtl">{area.name_ar}</p>
        )}
        <p className="text-[var(--color-text-secondary)] max-w-3xl mb-8">
          {area.description}
        </p>

        {/* KPI Cards */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-12">
          <div className="p-4 rounded-xl bg-[var(--color-surface)] border border-[var(--color-border)] text-center">
            <div className="text-2xl font-bold text-emerald-500">
              {area.avg_price_per_meter ? `${(area.avg_price_per_meter / 1000).toFixed(0)}K` : '—'}
            </div>
            <div className="text-xs text-[var(--color-text-muted)]">EGP/sqm</div>
          </div>
          <div className="p-4 rounded-xl bg-[var(--color-surface)] border border-[var(--color-border)] text-center">
            <div className="text-2xl font-bold text-blue-500">{area.price_growth_ytd}%</div>
            <div className="text-xs text-[var(--color-text-muted)]">YoY Growth</div>
          </div>
          <div className="p-4 rounded-xl bg-[var(--color-surface)] border border-[var(--color-border)] text-center">
            <div className="text-2xl font-bold text-purple-500">{area.rental_yield}%</div>
            <div className="text-xs text-[var(--color-text-muted)]">Rental Yield</div>
          </div>
          <div className="p-4 rounded-xl bg-[var(--color-surface)] border border-[var(--color-border)] text-center">
            <div className="text-2xl font-bold">{projects.length}</div>
            <div className="text-xs text-[var(--color-text-muted)]">Projects</div>
          </div>
        </div>

        {/* Price History Table */}
        {priceHistory.length > 0 && (
          <section className="mb-12">
            <h2 className="text-xl font-semibold mb-4">Price History (Last 12 Months)</h2>
            <div className="overflow-x-auto">
              <table className="w-full text-sm border-collapse">
                <thead>
                  <tr className="border-b border-[var(--color-border)]">
                    <th className="text-left py-2 px-3">Date</th>
                    <th className="text-right py-2 px-3">Avg EGP/sqm</th>
                    <th className="text-right py-2 px-3">Transactions</th>
                  </tr>
                </thead>
                <tbody>
                  {priceHistory.map((ph) => (
                    <tr key={ph.id} className="border-b border-[var(--color-border)]/50">
                      <td className="py-2 px-3">{ph.date}</td>
                      <td className="text-right py-2 px-3 font-medium">
                        {ph.price_per_m2.toLocaleString()}
                      </td>
                      <td className="text-right py-2 px-3 text-[var(--color-text-muted)]">
                        {ph.transaction_count ?? '—'}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        )}

        {/* Projects in Area */}
        <h2 className="text-xl font-semibold mb-4">
          Projects in {area.name} ({projects.length})
        </h2>
        <div className="grid md:grid-cols-2 gap-4">
          {projects.map((p) => (
            <Link
              key={p.id}
              href={`/projects/${p.slug}`}
              className="block p-5 rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] hover:border-emerald-500/50 transition-all"
            >
              <h3 className="font-semibold mb-1">{p.name}</h3>
              <div className="flex flex-wrap gap-2 text-xs text-[var(--color-text-muted)]">
                <span className="px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-600">
                  {p.project_type}
                </span>
                {p.expected_delivery && <span>Delivery {new Date(p.expected_delivery).getFullYear()}</span>}
              </div>
              {p.min_price_per_meter && p.max_price_per_meter && (
                <div className="mt-2 text-sm">
                  EGP {(p.min_price_per_meter).toLocaleString()} – {(p.max_price_per_meter).toLocaleString()} /m²
                </div>
              )}
            </Link>
          ))}
        </div>
      </div>
    </main>
  );
}
