import { getEnrichedSEO } from '@/lib/seo-content';
import { EnrichedBody } from '@/components/seo/EnrichedContent';
import type { Metadata } from 'next';
import Link from 'next/link';
import { notFound } from 'next/navigation';
import AppShell from '@/components/nav/AppShell';

export const revalidate = 86400; // ISR: 24 hours (buying guides change infrequently)

interface Props {
  params: Promise<{ slug: string }>;
}

export async function generateMetadata({ params }: Props): Promise<Metadata> {
  const { slug } = await params;
  const content = await getEnrichedSEO('buying_guide', slug).catch(() => null);
  if (!content) return { title: 'Buying Guide | Osool' };

  return {
    title: content.seo.title || `${slug.replace(/-/g, ' ')} — Buying Guide | Osool`,
    description: content.seo.description,
  };
}

export default async function BuyingGuidePage({ params }: Props) {
  const { slug } = await params;
  const content = await getEnrichedSEO('buying_guide', slug);

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
            <Link href="/" className="hover:text-emerald-500">Home</Link>
            <span className="mx-2">/</span>
            <span>Buying Guide</span>
          </nav>

          <h1 className="text-3xl font-semibold tracking-tight">{content.seo.title}</h1>

          <EnrichedBody content={content} />

          <div className="rounded-[28px] border border-emerald-500/20 bg-emerald-500/10 p-6 text-center">
            <h3 className="text-lg font-semibold">Have questions about buying in Egypt?</h3>
            <p className="mt-2 text-sm text-[var(--color-text-secondary)]">
              Our AI advisor understands Egyptian property law and can guide you step by step.
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
