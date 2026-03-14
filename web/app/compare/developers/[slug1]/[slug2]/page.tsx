import { compareDevelopers, getDeveloper, getDeveloperProjects } from '@/lib/seo-api';
import { comparisonJsonLd } from '@/lib/json-ld';
import type { Metadata } from 'next';
import Link from 'next/link';
import { notFound } from 'next/navigation';
import PublicPageNav from '@/components/PublicPageNav';
import { developerBrief, pickWinnerLabel } from '@/lib/decision-support';

interface Props {
  params: Promise<{ slug1: string; slug2: string }>;
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { slug1, slug2 } = await params;
  try {
    const [d1, d2] = await Promise.all([getDeveloper(slug1), getDeveloper(slug2)]);
    return {
      title: `${d1.name} vs ${d2.name} — Egyptian Developer Comparison | Osool`,
      description: `Compare ${d1.name} and ${d2.name}: delivery scores, finish quality, resale value, payment flexibility.`,
    };
  } catch {
    return { title: 'Developer Comparison | Osool' };
  }
}

export default async function DeveloperComparisonPage({ params }: Props) {
  const { slug1, slug2 } = await params;

  let d1, d2;
  try {
    [d1, d2] = await Promise.all([getDeveloper(slug1), getDeveloper(slug2)]);
  } catch {
    return notFound();
  }

  // Fetch projects for both developers in parallel
  const [projects1, projects2] = await Promise.all([
    getDeveloperProjects(slug1).catch(() => []),
    getDeveloperProjects(slug2).catch(() => []),
  ]);

  const brief1 = developerBrief(d1);
  const brief2 = developerBrief(d2);
  const summaryCards = [
    {
      label: 'Best delivery confidence',
      winner: pickWinnerLabel(d1.avg_delivery_score ?? 0, d2.avg_delivery_score ?? 0, d1.name, d2.name),
      detail: `${d1.name}: ${(d1.avg_delivery_score ?? 0).toFixed(1)} • ${d2.name}: ${(d2.avg_delivery_score ?? 0).toFixed(1)}`,
    },
    {
      label: 'Best resale strength',
      winner: pickWinnerLabel(d1.avg_resale_retention ?? 0, d2.avg_resale_retention ?? 0, d1.name, d2.name),
      detail: `${d1.name}: ${(d1.avg_resale_retention ?? 0).toFixed(1)} • ${d2.name}: ${(d2.avg_resale_retention ?? 0).toFixed(1)}`,
    },
    {
      label: 'Best payment flexibility',
      winner: pickWinnerLabel(d1.payment_flexibility ?? 0, d2.payment_flexibility ?? 0, d1.name, d2.name),
      detail: `${d1.name}: ${(d1.payment_flexibility ?? 0).toFixed(1)} • ${d2.name}: ${(d2.payment_flexibility ?? 0).toFixed(1)}`,
    },
  ];

  const metrics = [
    { label: 'Delivery Score', key: 'avg_delivery_score' as const },
    { label: 'Finish Quality', key: 'avg_finish_quality' as const },
    { label: 'Resale Retention', key: 'avg_resale_retention' as const },
    { label: 'Payment Flexibility', key: 'payment_flexibility' as const },
    { label: 'Overall Score', key: 'overall_score' as const },
  ];

  return (
    <PublicPageNav>
    <main className="min-h-screen bg-[var(--color-background)] text-[var(--color-text-primary)]">
      <div className="mx-auto flex max-w-6xl flex-col gap-8 px-4 py-8 sm:px-6 lg:px-8">
        {/* Breadcrumb */}
        <nav className="text-sm text-[var(--color-text-muted)] mb-6 flex items-center gap-1">
          <Link href="/" className="hover:text-emerald-500">Home</Link>
          <span>/</span>
          <Link href="/developers" className="hover:text-emerald-500">Developers</Link>
          <span>/</span>
          <span className="text-[var(--color-text-primary)]">Compare</span>
        </nav>

        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: JSON.stringify(comparisonJsonLd('developers', d1.name, d2.name, d1.slug, d2.slug)) }}
        />
        <h1 className="text-3xl font-bold mb-2">
          {d1.name} vs {d2.name}
        </h1>
        <p className="text-[var(--color-text-muted)] mb-10">
          Side-by-side developer comparison based on delivery, quality, and value retention.
        </p>

        <section className="grid gap-4 md:grid-cols-3">
          {summaryCards.map((card) => (
            <div key={card.label} className="rounded-[28px] border border-[var(--color-border)] bg-[var(--color-surface)] p-5">
              <div className="text-[11px] font-semibold uppercase tracking-[0.18em] text-[var(--color-text-muted)]">{card.label}</div>
              <div className="mt-2 text-lg font-semibold">{card.winner}</div>
              <div className="mt-2 text-sm text-[var(--color-text-secondary)]">{card.detail}</div>
            </div>
          ))}
        </section>

        <section className="grid gap-4 md:grid-cols-2">
          <div className="rounded-[28px] border border-[var(--color-border)] bg-[var(--color-surface)] p-5">
            <div className="text-sm font-semibold text-[var(--color-text-primary)]">{d1.name}</div>
            <div className="mt-2 text-sm leading-6 text-[var(--color-text-secondary)]">{brief1.verdict}</div>
            <div className="mt-2 text-xs leading-5 text-[var(--color-text-muted)]">Best for: {brief1.bestFor}</div>
          </div>
          <div className="rounded-[28px] border border-[var(--color-border)] bg-[var(--color-surface)] p-5">
            <div className="text-sm font-semibold text-[var(--color-text-primary)]">{d2.name}</div>
            <div className="mt-2 text-sm leading-6 text-[var(--color-text-secondary)]">{brief2.verdict}</div>
            <div className="mt-2 text-xs leading-5 text-[var(--color-text-muted)]">Best for: {brief2.bestFor}</div>
          </div>
        </section>

        {/* Score Comparison Table */}
        <div className="rounded-2xl border border-[var(--color-border)] overflow-hidden mb-10">
          <table className="w-full text-sm">
            <thead className="bg-[var(--color-surface)]">
              <tr>
                <th className="p-4 text-left font-medium">Metric</th>
                <th className="p-4 text-center font-medium">
                  <Link href={`/developers/${d1.slug}`} className="hover:text-emerald-500">
                    {d1.name}
                  </Link>
                </th>
                <th className="p-4 text-center font-medium">
                  <Link href={`/developers/${d2.slug}`} className="hover:text-emerald-500">
                    {d2.name}
                  </Link>
                </th>
                <th className="p-4 text-center font-medium">Winner</th>
              </tr>
            </thead>
            <tbody>
              {metrics.map(({ label, key }) => {
                const v1 = d1[key] ?? 0;
                const v2 = d2[key] ?? 0;
                const winner = v1 > v2 ? 1 : v2 > v1 ? 2 : 0;
                return (
                  <tr key={key} className="border-t border-[var(--color-border)]">
                    <td className="p-4 font-medium">{label}</td>
                    <td className={`p-4 text-center font-mono ${winner === 1 ? 'text-emerald-500 font-bold' : ''}`}>
                      {v1.toFixed(1)}
                    </td>
                    <td className={`p-4 text-center font-mono ${winner === 2 ? 'text-emerald-500 font-bold' : ''}`}>
                      {v2.toFixed(1)}
                    </td>
                    <td className="p-4 text-center text-xs">
                      {winner === 1
                        ? `✅ ${d1.name}`
                        : winner === 2
                          ? `✅ ${d2.name}`
                          : 'Tie'}
                    </td>
                  </tr>
                );
              })}
            </tbody>
          </table>
        </div>

        {/* General Info */}
        <div className="grid md:grid-cols-2 gap-6 mb-10">
          <InfoCard developer={d1} projectCount={projects1.length} />
          <InfoCard developer={d2} projectCount={projects2.length} />
        </div>

        {/* Projects Side-by-Side */}
        <h2 className="text-xl font-semibold mb-4">Projects</h2>
        <div className="grid md:grid-cols-2 gap-6 mb-10">
          <ProjectList title={d1.name} projects={projects1} />
          <ProjectList title={d2.name} projects={projects2} />
        </div>

        {/* CTA */}
        <div className="bg-emerald-500/10 border border-emerald-500/20 rounded-2xl p-6 text-center">
          <h3 className="text-lg font-semibold mb-2">Need help deciding?</h3>
          <p className="text-sm text-[var(--color-text-muted)] mb-4">
            Our AI advisor can give you a personalized recommendation based on your budget and preferences.
          </p>
          <Link
            href="/chat"
            className="inline-block px-6 py-2 bg-emerald-500 text-white rounded-full font-medium hover:bg-emerald-600 transition-colors"
          >
            Get AI Recommendation
          </Link>
        </div>
      </div>
    </main>
    </PublicPageNav>
  );
}

function InfoCard({
  developer,
  projectCount,
}: {
  developer: { name: string; name_ar?: string; founded_year?: number; total_projects?: number; description?: string };
  projectCount: number;
}) {
  return (
    <div className="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)] p-5">
      <h3 className="font-semibold text-lg mb-1">{developer.name}</h3>
      {developer.name_ar && (
        <p className="text-sm text-[var(--color-text-muted)] mb-2" dir="rtl">{developer.name_ar}</p>
      )}
      <div className="text-sm text-[var(--color-text-secondary)] space-y-1">
        {developer.founded_year && <p>Founded: {developer.founded_year}</p>}
        <p>Projects on Osool: {projectCount}</p>
        {developer.total_projects && <p>Total Projects: {developer.total_projects}</p>}
      </div>
      {developer.description && (
        <p className="text-sm text-[var(--color-text-muted)] mt-3">{developer.description}</p>
      )}
    </div>
  );
}

function ProjectList({
  title,
  projects,
}: {
  title: string;
  projects: Array<{ slug: string; name: string; project_type?: string; min_price_per_meter?: number; max_price_per_meter?: number }>;
}) {
  if (projects.length === 0) return <p className="text-sm text-[var(--color-text-muted)]">No projects listed for {title}.</p>;
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
