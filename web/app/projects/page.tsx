import { getProjects } from '@/lib/seo-api';
import type { Metadata } from 'next';
import Link from 'next/link';

export const metadata: Metadata = {
  title: 'Egyptian Real Estate Projects — Prices & Payment Plans | Osool',
  description:
    'Browse 30+ verified Egyptian real estate projects: compounds, resorts, towers. Filter by area, developer, price, and bedrooms. Updated weekly.',
};

export default async function ProjectsPage() {
  const projects = await getProjects();

  return (
    <main className="min-h-screen bg-[var(--color-background)] text-[var(--color-text-primary)]">
      <div className="max-w-6xl mx-auto px-4 py-16">
        <h1 className="text-3xl font-bold mb-2">
          Egyptian Real Estate Projects
        </h1>
        <p className="text-[var(--color-text-muted)] mb-10">
          Browse verified projects from Egypt&apos;s top developers. Compounds, resorts, and towers
          with pricing, payment plans, and delivery dates.
        </p>

        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-5">
          {projects.map((p) => (
            <Link
              key={p.id}
              href={`/projects/${p.slug}`}
              className="group block p-5 rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] hover:border-emerald-500/50 transition-all"
            >
              <div className="flex items-center gap-2 mb-2">
                <span className="px-2 py-0.5 text-[10px] rounded-full bg-emerald-500/10 text-emerald-600 font-medium">
                  {p.project_type}
                </span>
                <span className="px-2 py-0.5 text-[10px] rounded-full bg-blue-500/10 text-blue-600 font-medium">
                  {p.status}
                </span>
              </div>

              <h2 className="text-lg font-semibold group-hover:text-emerald-500 transition-colors">
                {p.name}
              </h2>
              {p.name_ar && (
                <p className="text-sm text-[var(--color-text-muted)]" dir="rtl">{p.name_ar}</p>
              )}

              <div className="mt-3 space-y-1 text-sm text-[var(--color-text-secondary)]">
                {p.min_price_per_meter && p.max_price_per_meter && (
                  <div>
                    💰 EGP {p.min_price_per_meter.toLocaleString()} – {p.max_price_per_meter.toLocaleString()} /m²
                  </div>
                )}
                {p.expected_delivery && <div>📅 Delivery {new Date(p.expected_delivery).getFullYear()}</div>}
                {p.min_unit_size && p.max_unit_size && (
                  <div>📐 {p.min_unit_size}–{p.max_unit_size} m²</div>
                )}
                {p.down_payment_min != null && p.installment_years != null && (
                  <div>💳 {p.down_payment_min}% down, {p.installment_years} years</div>
                )}
              </div>

              {(() => {
                try {
                  const arr = typeof p.amenities === 'string' ? JSON.parse(p.amenities) : p.amenities;
                  if (!Array.isArray(arr) || arr.length === 0) return null;
                  return (
                    <div className="mt-3 flex flex-wrap gap-1">
                      {arr.slice(0, 3).map((a: string) => (
                        <span
                          key={a}
                          className="text-[10px] px-2 py-0.5 rounded-full bg-[var(--color-border)]/50 text-[var(--color-text-muted)]"
                        >
                          {a}
                        </span>
                      ))}
                      {arr.length > 3 && (
                        <span className="text-[10px] px-2 py-0.5 text-[var(--color-text-muted)]">
                          +{arr.length - 3} more
                    </span>
                  )}
                    </div>
                  );
                } catch { return null; }
              })()}
            </Link>
          ))}
        </div>
      </div>
    </main>
  );
}
