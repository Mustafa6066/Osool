/**
 * SEO API — Dual-Engine Frontend Helpers
 * ----------------------------------------
 * Typed API functions for the SEO/marketing platform.
 * These use direct fetch (no auth) for public SEO content,
 * or the authenticated api client for user-specific data.
 */

const BASE = (process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000').replace(/\/$/, '');

// ═══════════════════════════════════════════════════════════════
// TYPES
// ═══════════════════════════════════════════════════════════════

export interface Developer {
  id: number;
  name: string;
  name_ar?: string;
  slug: string;
  founded_year?: number;
  total_projects?: number;
  description?: string;
  description_ar?: string;
  avg_delivery_score?: number;
  avg_finish_quality?: number;
  avg_resale_retention?: number;
  payment_flexibility?: number;
  overall_score?: number;
}

export interface Area {
  id: number;
  name: string;
  name_ar?: string;
  slug: string;
  city?: string;
  avg_price_per_meter?: number;
  price_growth_ytd?: number;
  rental_yield?: number;
  liquidity_score?: number;
  demand_score?: number;
  description?: string;
  description_ar?: string;
}

export interface Project {
  id: number;
  slug: string;
  name: string;
  name_ar?: string;
  developer_id?: number;
  area_id?: number;
  project_type?: string;
  status?: string;
  min_price_per_meter?: number;
  max_price_per_meter?: number;
  avg_price_per_meter?: number;
  down_payment_min?: number;
  installment_years?: number;
  expected_delivery?: string;
  min_unit_size?: number;
  max_unit_size?: number;
  amenities?: string;
  unit_types?: string;
  construction_progress?: number;
  predicted_roi_1y?: number;
  predicted_roi_3y?: number;
  predicted_roi_5y?: number;
}

export interface PriceHistory {
  id: number;
  area_id?: number;
  project_id?: number;
  date: string;
  price_per_m2: number;
  transaction_count?: number;
}

export interface SEOPage {
  id: number;
  slug: string;
  page_type: string;
  status: string;
  title?: string;
  title_ar?: string;
  meta_desc?: string;
  content_json?: string;
  view_count?: number;
  chat_conv_rate?: number;
}

// ═══════════════════════════════════════════════════════════════
// FETCH HELPERS (server-side / ISR compatible)
// ═══════════════════════════════════════════════════════════════

async function seoFetch<T>(path: string, revalidate: number = 3600): Promise<T> {
  const res = await fetch(`${BASE}${path}`, {
    next: { revalidate },
  });
  if (!res.ok) throw new Error(`SEO API ${res.status}: ${path}`);
  return res.json();
}

// ═══════════════════════════════════════════════════════════════
// DEVELOPERS
// ═══════════════════════════════════════════════════════════════

export const getDevelopers = (sort = 'overall_score', order = 'desc') =>
  seoFetch<Developer[]>(`/api/seo/developers?sort=${sort}&order=${order}`, 60);

export const getDeveloper = (slug: string) =>
  seoFetch<Developer>(`/api/seo/developers/${slug}`);

export const getDeveloperProjects = (slug: string) =>
  seoFetch<Project[]>(`/api/seo/developers/${slug}/projects`);

// ═══════════════════════════════════════════════════════════════
// AREAS
// ═══════════════════════════════════════════════════════════════

export const getAreas = (sort = 'avg_price_per_meter', order = 'desc') =>
  seoFetch<Area[]>(`/api/seo/areas?sort=${sort}&order=${order}`, 60);

export const getArea = (slug: string) =>
  seoFetch<Area>(`/api/seo/areas/${slug}`);

export const getAreaProjects = (slug: string) =>
  seoFetch<Project[]>(`/api/seo/areas/${slug}/projects`);

// ═══════════════════════════════════════════════════════════════
// PROJECTS
// ═══════════════════════════════════════════════════════════════

export const getProjects = (params?: Record<string, string>) => {
  const qs = params ? '?' + new URLSearchParams(params).toString() : '';
  return seoFetch<Project[]>(`/api/seo/projects${qs}`);
};

export const getProject = (slug: string) =>
  seoFetch<Project>(`/api/seo/projects/${slug}`);

// ═══════════════════════════════════════════════════════════════
// PRICE HISTORY
// ═══════════════════════════════════════════════════════════════

export const getAreaPriceHistory = (slug: string, months = 12) =>
  seoFetch<PriceHistory[]>(`/api/seo/price-history/area/${slug}?months=${months}`);

export const getProjectPriceHistory = (slug: string, months = 12) =>
  seoFetch<PriceHistory[]>(`/api/seo/price-history/project/${slug}?months=${months}`);

// ═══════════════════════════════════════════════════════════════
// COMPARISONS
// ═══════════════════════════════════════════════════════════════

export const compareDevelopers = (slug1: string, slug2: string) =>
  seoFetch<{ developer_1: Record<string, unknown>; developer_2: Record<string, unknown> }>(
    `/api/seo/compare/developers/${slug1}/${slug2}`
  );

export const compareAreas = (slug1: string, slug2: string) =>
  seoFetch<{ area_1: Record<string, unknown>; area_2: Record<string, unknown> }>(
    `/api/seo/compare/areas/${slug1}/${slug2}`
  );

// ═══════════════════════════════════════════════════════════════
// SEO PAGES
// ═══════════════════════════════════════════════════════════════

export const getSEOPage = (slug: string) =>
  seoFetch<SEOPage>(`/api/seo/pages/${slug}`);

// ═══════════════════════════════════════════════════════════════
// WAITLIST (public)
// ═══════════════════════════════════════════════════════════════

export async function joinWaitlist(data: {
  name: string;
  email: string;
  phone?: string;
  interest?: string;
  source?: string;
}) {
  const res = await fetch(`${BASE}/api/campaigns/waitlist`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(data),
  });
  return res.json();
}
