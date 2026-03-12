import { getDeveloper, getDeveloperProjects } from '@/lib/seo-api';
import { developerJsonLd } from '@/lib/json-ld';
import type { Metadata } from 'next';
import Link from 'next/link';
import { notFound } from 'next/navigation';
import SmartNav from '@/components/SmartNav';

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

function Stat({ label, value, suffix }: { label: string; value?: number | null; suffix?: string }) {
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

  return (
    <SmartNav>
    <main className="h-full overflow-y-auto bg-[var(--color-background)] text-[var(--color-text-primary)] pb-20 md:pb-0">
      <script
        type="application/ld+json"
        dangerouslySetInnerHTML={{ __html: JSON.stringify(developerJsonLd(dev)) }}
      />
      <div className="max-w-5xl mx-auto px-4 py-16">
        {/* Header */}
        <nav className="text-sm text-[var(--color-text-muted)] mb-6">
          <Link href="/developers" className="hover:text-emerald-500">Developers</Link>
          <span className="mx-2">/</span>
          <span>{dev.name}</span>
        </nav>

        <h1 className="text-3xl font-bold mb-2">{dev.name}</h1>
        {dev.name_ar && (
          <p className="text-lg text-[var(--color-text-muted)] mb-4" dir="rtl">{dev.name_ar}</p>
        )}
        <p className="text-[var(--color-text-secondary)] max-w-3xl mb-8">
          {dev.description}
        </p>

        {/* Score Cards */}
        <div className="grid grid-cols-2 md:grid-cols-5 gap-3 mb-12">
          <Stat label="Overall Score" value={dev.overall_score} suffix="/100" />
          <Stat label="Delivery" value={dev.avg_delivery_score} suffix="/100" />
          <Stat label="Finish Quality" value={dev.avg_finish_quality} suffix="/100" />
          <Stat label="Resale Retention" value={dev.avg_resale_retention} suffix="%" />
          <Stat label="Payment Flex" value={dev.payment_flexibility} suffix="/100" />
        </div>

        {/* Projects */}
        <h2 className="text-xl font-semibold mb-4">
          Projects by {dev.name} ({projects.length})
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
          <h3 className="text-lg font-semibold mb-2">Compare {dev.name} with other developers</h3>
          <Link
            href="/developers"
            className="inline-flex items-center gap-2 px-4 py-2 bg-emerald-500 text-white rounded-lg hover:bg-emerald-600 transition-colors text-sm"
          >
            View All Developers →
          </Link>
        </div>
      </div>
    </main>
    </SmartNav>
  );
}
