import { getEnrichedSEO } from '@/lib/seo-content';
import { EnrichedBody, LivePropertyCards } from '@/components/seo/EnrichedContent';
import type { Metadata } from 'next';
import Link from 'next/link';
import { notFound } from 'next/navigation';
import AppShell from '@/components/nav/AppShell';

export const revalidate = 21600; // ISR: 6 hours

interface Props {
  params: Promise<{ slug: string }>;
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { slug } = await params;
  const content = await getEnrichedSEO('roi_analysis', slug).catch(() => null);
  if (!content) return { title: 'ROI Analysis | Osool' };

  return {
    title: content.seo.title || `${slug.replace(/-/g, ' ')} ROI Analysis | Osool`,
    description: content.seo.description,
  };
}

export default async function ROIPage({ params }: Props) {
  const { slug } = await params;
  const content = await getEnrichedSEO('roi_analysis', slug);

  if (!content) notFound();

  return (
    <AppShell>
      <main className="h-full overflow-y-auto bg-[var(--color-background)] text-[var(--color-text-primary)]">
        {content.seo.schemaMarkup && (
          <script
            type="application/ld+json"
            dangerouslySetInnerHTML={{ __html: JSON.stringify(content.seo.schemaMarkup) }}
          />
        )}
        <div className="mx-auto flex max-w-4xl flex-col gap-8 px-4 py-8 sm:px-6 lg:px-8">
          <nav className="text-sm text-[var(--color-text-muted)]">
            <Link href="/areas" className="hover:text-emerald-500">Areas</Link>
            <span className="mx-2">/</span>
            <span>ROI Analysis</span>
          </nav>

          <h1 className="text-3xl font-semibold tracking-tight">{content.seo.title}</h1>

          {content.liveData.areaMetrics && (
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
              <div className="p-4 rounded-xl bg-[var(--color-surface)] border border-[var(--color-border)] text-center">
                <div className="text-2xl font-bold text-emerald-500">
                  {content.liveData.areaMetrics.price_growth_ytd?.toFixed(1)}%
                </div>
                <div className="text-xs text-[var(--color-text-muted)]">YoY Growth</div>
              </div>
              <div className="p-4 rounded-xl bg-[var(--color-surface)] border border-[var(--color-border)] text-center">
                <div className="text-2xl font-bold text-purple-500">
                  {content.liveData.areaMetrics.rental_yield?.toFixed(1)}%
                </div>
                <div className="text-xs text-[var(--color-text-muted)]">Rental Yield</div>
              </div>
              <div className="p-4 rounded-xl bg-[var(--color-surface)] border border-[var(--color-border)] text-center">
                <div className="text-2xl font-bold text-blue-500">
                  {(content.liveData.areaMetrics.avg_price_per_meter / 1000).toFixed(0)}K
                </div>
                <div className="text-xs text-[var(--color-text-muted)]">EGP/m²</div>
              </div>
              <div className="p-4 rounded-xl bg-[var(--color-surface)] border border-[var(--color-border)] text-center">
                <div className="text-2xl font-bold">
                  {content.liveData.areaMetrics.demand_score}/100
                </div>
                <div className="text-xs text-[var(--color-text-muted)]">Demand Score</div>
              </div>
            </div>
          )}

          <EnrichedBody content={content} />

          {content.liveData.topROIProperties && (
            <LivePropertyCards properties={content.liveData.topROIProperties} />
          )}

          <div className="rounded-[28px] border border-emerald-500/20 bg-emerald-500/10 p-6 text-center">
            <h3 className="text-lg font-semibold">Want a personalized ROI analysis?</h3>
            <p className="mt-2 text-sm text-[var(--color-text-secondary)]">
              Our AI advisor can calculate your specific investment returns.
            </p>
            <Link
              href="/chat"
              className="mt-4 inline-flex rounded-full bg-[var(--color-text-primary)] px-5 py-3 text-sm font-semibold text-[var(--color-background)]"
            >
              Ask the AI Advisor
            </Link>
          </div>
        </div>
      </main>
    </AppShell>
  );
}
