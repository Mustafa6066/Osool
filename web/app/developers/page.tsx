import { getDevelopers } from '@/lib/seo-api';
import type { Developer } from '@/lib/seo-api';
import type { Metadata } from 'next';
import Link from 'next/link';
import PublicPageNav from '@/components/PublicPageNav';

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
    <PublicPageNav>
    <main className="h-full overflow-y-auto bg-[var(--color-background)] text-[var(--color-text-primary)]">
      <div className="max-w-6xl mx-auto px-4 py-8">
        <h1 className="text-3xl font-bold mb-2">
          Top Egyptian Real Estate Developers
        </h1>
        <p className="text-[var(--color-text-muted)] mb-10">
          Ranked by delivery track record, finish quality, and resale value retention.
          Data updated monthly by Osool&apos;s AI analytics engine.
        </p>

        {developers.length > 0 ? (
          <div className="grid md:grid-cols-2 gap-6">
            {developers.map((dev, i) => (
              <Link
                key={dev.id}
                href={`/developers/${dev.slug}`}
                className="group block p-6 rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] hover:border-emerald-500/50 transition-all"
              >
                <div className="flex items-start justify-between mb-4">
                  <div>
                    <div className="flex items-center gap-2 mb-1">
                      <span className="text-xs font-bold text-emerald-500">#{i + 1}</span>
                      <h2 className="text-lg font-semibold group-hover:text-emerald-500 transition-colors">
                        {dev.name}
                      </h2>
                    </div>
                    <p className="text-sm text-[var(--color-text-muted)]">
                      Est. {dev.founded_year} · {dev.total_projects} projects
                    </p>
                  </div>
                  <div className="flex items-center justify-center w-12 h-12 rounded-xl bg-emerald-500/10 text-emerald-500 font-bold text-lg">
                    {dev.overall_score}
                  </div>
                </div>

                <div className="space-y-2">
                  <ScoreBar value={dev.avg_delivery_score ?? 0} label="Delivery" />
                  <ScoreBar value={dev.avg_finish_quality ?? 0} label="Quality" />
                  <ScoreBar value={dev.avg_resale_retention ?? 0} label="Resale" />
                  <ScoreBar value={dev.payment_flexibility ?? 0} label="Payments" />
                </div>
              </Link>
            ))}
          </div>
        ) : (
          <div className="rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] p-8 text-center">
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
    </PublicPageNav>
  );
}
