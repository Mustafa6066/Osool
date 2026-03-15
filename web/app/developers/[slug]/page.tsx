import { getDeveloper, getDeveloperProjects } from '@/lib/seo-api';
import { developerJsonLd } from '@/lib/json-ld';
import type { Metadata } from 'next';
import Link from 'next/link';
import { notFound } from 'next/navigation';
import AppShell from '@/components/nav/AppShell';
import { developerBrief } from '@/lib/decision-support';
import { T } from '@/components/T';

const fmt = (n: number) => n.toLocaleString('en-EG');

interface Props {
  params: Promise<{ slug: string }>;
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { slug } = await params;
  try {
    const dev = await getDeveloper(slug);
    return {
      title: `${dev.name}: Projects, Reviews & Scores | Osool`,
      description: dev.description?.slice(0, 160),
    };
  } catch {
    return { title: 'Developer Not Found | Osool' };
  }
}

function Stat({ label, value, suffix }: { label: React.ReactNode; value?: number | null; suffix?: string }) {
  if (!value) return null;
  return (
    <div className="text-center p-4 rounded-xl bg-[var(--color-surface)] border border-[var(--color-border)]">
      <div className="text-2xl font-bold text-emerald-500">
        {value}{suffix}
      </div>
      <div className="text-xs text-[var(--color-text-muted)] mt-1">{label}</div>
    </div>
  );
}

export default async function DeveloperPage({ params }: Props) {
  const { slug } = await params;
  let dev, projects;
  try {
    [dev, projects] = await Promise.all([
      getDeveloper(slug),
      getDeveloperProjects(slug),
    ]);
  } catch {
    notFound();
  }

  const brief = developerBrief(dev);

  return (
    <AppShell>
    <main className="h-full overflow-y-auto bg-[var(--color-background)] text-[var(--color-text-primary)]">
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(developerJsonLd(dev)) }}
      />
      <div className="mx-auto flex max-w-6xl flex-col gap-8 px-4 py-8 sm:px-6 lg:px-8">
        {/* Header */}
        <nav className="text-sm text-[var(--color-text-muted)] mb-6">
          <Link href="/developers" className="hover:text-emerald-500"><T k="comparePage.developers" /></Link>
          <span className="mx-2">/</span>
          <span>{dev.name}</span>
        </nav>

        <section className="grid gap-6 lg:grid-cols-[1fr_0.9fr] lg:items-start">
          <div className="rounded-[32px] border border-[var(--color-border)] bg-[var(--color-surface)] p-8">
            <div className="inline-flex items-center gap-2 rounded-full bg-emerald-500/10 px-3 py-1 text-[11px] font-semibold uppercase tracking-[0.16em] text-emerald-600 dark:text-emerald-400">
              {brief.trustLabel}
            </div>
            <h1 className="mt-4 text-4xl font-semibold tracking-tight">{dev.name}</h1>
            {dev.name_ar && (
              <p className="mt-2 text-lg text-[var(--color-text-muted)]" dir="rtl">{dev.name_ar}</p>
            )}
            <p className="mt-5 max-w-3xl text-base leading-7 text-[var(--color-text-secondary)]">
              {dev.description || brief.verdict}
            </p>
          </div>

          <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-1">
            <div className="rounded-[28px] border border-[var(--color-border)] bg-[var(--color-surface)] p-5">
              <div className="text-[11px] font-semibold uppercase tracking-[0.18em] text-[var(--color-text-muted)]"><T k="devPage.bestFor" /></div>
              <div className="mt-2 text-base font-semibold">{brief.bestFor}</div>
            </div>
            <div className="rounded-[28px] border border-[var(--color-border)] bg-[var(--color-surface)] p-5">
              <div className="text-[11px] font-semibold uppercase tracking-[0.18em] text-[var(--color-text-muted)]"><T k="devPage.mainWatchout" /></div>
              <div className="mt-2 text-base font-semibold">{brief.risk}</div>
            </div>
          </div>
        </section>

        {/* Score Cards */}
        <div className="grid grid-cols-2 md:grid-cols-5 gap-3">
          <Stat label={<T k="devPage.overallScore" />} value={dev.overall_score} suffix="/100" />
          <Stat label={<T k="devPage.delivery" />} value={dev.avg_delivery_score} suffix="/100" />
          <Stat label={<T k="devPage.finishQuality" />} value={dev.avg_finish_quality} suffix="/100" />
          <Stat label={<T k="devPage.resaleRetention" />} value={dev.avg_resale_retention} suffix="%" />
          <Stat label={<T k="devPage.paymentFlex" />} value={dev.payment_flexibility} suffix="/100" />
        </div>

        <section className="rounded-[28px] border border-[var(--color-border)] bg-[var(--color-surface)] p-6">
          <h2 className="text-sm font-semibold uppercase tracking-[0.18em] text-[var(--color-text-muted)]"><T k="devPage.whyScoreMatters" /></h2>
          <div className="mt-4 grid gap-3 md:grid-cols-3">
            <div className="rounded-2xl border border-[var(--color-border)] bg-[var(--color-background)] p-4 text-sm leading-6 text-[var(--color-text-secondary)]">
              <T k="devPage.deliveryHelps" />
            </div>
            <div className="rounded-2xl border border-[var(--color-border)] bg-[var(--color-background)] p-4 text-sm leading-6 text-[var(--color-text-secondary)]">
              <T k="devPage.resaleStrength" />
            </div>
            <div className="rounded-2xl border border-[var(--color-border)] bg-[var(--color-background)] p-4 text-sm leading-6 text-[var(--color-text-secondary)]">
              <T k="devPage.paymentFlexNote" />
            </div>
          </div>
        </section>

        {/* Projects */}
        <h2 className="text-xl font-semibold mb-4">
          <T k="devPage.projectsBy" /> {dev.name} ({(projects || []).length})
        </h2>
        <div className="grid md:grid-cols-2 gap-4">
          {(projects || []).map((p) => (
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
                <span className="px-2 py-0.5 rounded-full bg-blue-500/10 text-blue-600">
                  {p.status}
                </span>
                {p.expected_delivery && <span>Delivery {p.expected_delivery.toString().slice(0, 10)}</span>}
              </div>
              <div className="mt-2 text-sm">
                {p.min_price_per_meter && p.max_price_per_meter && (
                  <span>
                    EGP {fmt(p.min_price_per_meter)} – {fmt(p.max_price_per_meter)} /m²
                  </span>
                )}
              </div>
            </Link>
          ))}
        </div>

        {/* Compare CTA */}
        <div className="mt-12 p-6 rounded-2xl bg-emerald-500/5 border border-emerald-500/20 text-center">
          <h3 className="text-lg font-semibold mb-2"><T k="devPage.compareWith" /> {dev.name}</h3>
          <Link
            href="/developers"
            className="inline-flex items-center gap-2 px-4 py-2 bg-emerald-500 text-white rounded-lg hover:bg-emerald-600 transition-colors text-sm"
          >
            <T k="devPage.viewAllDevelopers" /> →
          </Link>
        </div>
      </div>
    </main>
    </AppShell>
  );
}
