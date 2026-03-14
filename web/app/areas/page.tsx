import { getAreas } from '@/lib/seo-api';
import type { Metadata } from 'next';
import Link from 'next/link';

export const metadata: Metadata = {
  title: 'Best Investment Areas in Egypt — Prices, Growth & Yield | Osool',
  description:
    'Compare Egypt\'s top investment zones: Sheikh Zayed, New Capital, Ras El Hikma, Ain Sokhna, North Coast & more. Price per sqm, appreciation rates, rental yields.',
};

export default async function AreasPage() {
  const areas = await getAreas().catch(() => []);

  return (
    <main className="min-h-screen bg-[var(--color-background)] text-[var(--color-text-primary)]">
      <div className="max-w-6xl mx-auto px-4 py-16">
        <h1 className="text-3xl font-bold mb-2">
          Best Investment Areas in Egypt
        </h1>
        <p className="text-[var(--color-text-muted)] mb-10">
          Real-time price data, year-over-year appreciation, and rental yield
          for every major investment zone.
        </p>

        <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-5">
          {areas.map((area) => (
            <Link
              key={area.id}
              href={`/areas/${area.slug}`}
              className="group block p-5 rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] hover:border-emerald-500/50 transition-all"
            >
              <h2 className="text-lg font-semibold mb-1 group-hover:text-emerald-500 transition-colors">
                {area.name}
              </h2>
              <p className="text-sm text-[var(--color-text-muted)] mb-4">
                {area.city}
              </p>

              <div className="grid grid-cols-3 gap-2 text-center">
                <div>
                  <div className="text-lg font-bold text-emerald-500">
                    {area.avg_price_per_meter ? `${(area.avg_price_per_meter / 1000).toFixed(0)}K` : '—'}
                  </div>
                  <div className="text-[10px] text-[var(--color-text-muted)]">EGP/sqm</div>
                </div>
                <div>
                  <div className="text-lg font-bold text-blue-500">
                    {area.price_growth_ytd ? `${area.price_growth_ytd}%` : '—'}
                  </div>
                  <div className="text-[10px] text-[var(--color-text-muted)]">YoY Growth</div>
                </div>
                <div>
                  <div className="text-lg font-bold text-purple-500">
                    {area.rental_yield ? `${area.rental_yield}%` : '—'}
                  </div>
                  <div className="text-[10px] text-[var(--color-text-muted)]">Rental Yield</div>
                </div>
              </div>
            </Link>
          ))}
        </div>
      </div>
    </main>
  );
}
