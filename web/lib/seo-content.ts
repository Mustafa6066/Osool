/**
 * SEO Content Bridge — Orchestrator Enriched Content
 * ---------------------------------------------------
 * Server-side fetch for AI-generated SEO content from the Orchestrator,
 * enriched with live property data. Used in Next.js server components.
 */

const ORCHESTRATOR_URL = (
  process.env.NEXT_PUBLIC_ORCHESTRATOR_URL || ''
).replace(/\/$/, '');

const API_KEY = process.env.ORCHESTRATOR_API_KEY || '';

export interface EnrichedSEOContent {
  seo: {
    pageType: string;
    slug: string;
    locale: string;
    title: string;
    description: string;
    body: string;
    schemaMarkup?: Record<string, unknown>;
    version: number;
    generatedAt: string;
  };
  liveData: {
    topROIProperties?: Array<{
      id: string;
      title: string;
      location: string;
      developer: string;
      price: number;
      price_per_sqm: number;
      bedrooms: number;
      size_sqm: number;
      roi_estimate?: number;
    }>;
    areaMetrics?: {
      avg_price_per_meter: number;
      rental_yield: number;
      price_growth_ytd: number;
      demand_score: number;
    };
    developerProfile?: Record<string, unknown>;
    developerA?: Record<string, unknown>;
    developerB?: Record<string, unknown>;
  };
  lastUpdated: string;
}

/**
 * Fetch enriched SEO content from the Orchestrator.
 * Returns null if the Orchestrator is unreachable or content doesn't exist.
 */
export async function getEnrichedSEO(
  pageType: string,
  slug: string,
  locale: string = 'en',
): Promise<EnrichedSEOContent | null> {
  if (!ORCHESTRATOR_URL) return null;

  try {
    const url = `${ORCHESTRATOR_URL}/data/enriched-seo/${encodeURIComponent(pageType)}/${encodeURIComponent(slug)}?locale=${locale}`;
    const res = await fetch(url, {
      headers: {
        'Content-Type': 'application/json',
        ...(API_KEY ? { 'x-api-key': API_KEY } : {}),
      },
      next: { revalidate: 21600 }, // 6 hours ISR
    });

    if (!res.ok) return null;
    return res.json();
  } catch {
    return null;
  }
}

/**
 * Fetch all published SEO content slugs for sitemap generation.
 */
export async function getPublishedSEOSlugs(): Promise<
  Array<{ pageType: string; slug: string; locale: string; updatedAt: string }>
> {
  if (!ORCHESTRATOR_URL) return [];

  try {
    const res = await fetch(`${ORCHESTRATOR_URL}/data/seo-pages?status=published`, {
      headers: {
        'Content-Type': 'application/json',
        ...(API_KEY ? { 'x-api-key': API_KEY } : {}),
      },
      next: { revalidate: 3600 },
    });

    if (!res.ok) return [];
    const data = await res.json();
    return Array.isArray(data) ? data : data.pages ?? [];
  } catch {
    return [];
  }
}
