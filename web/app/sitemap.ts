import type { MetadataRoute } from 'next';
import { getDevelopers, getAreas, getProjects } from '@/lib/seo-api';

const SITE = process.env.NEXT_PUBLIC_SITE_URL || 'https://osool.eg';

export default async function sitemap(): Promise<MetadataRoute.Sitemap> {
  const now = new Date().toISOString();

  // Static pages
  const staticPages: MetadataRoute.Sitemap = [
    { url: `${SITE}/`, lastModified: now, changeFrequency: 'daily', priority: 1.0 },
    { url: `${SITE}/developers`, lastModified: now, changeFrequency: 'weekly', priority: 0.9 },
    { url: `${SITE}/areas`, lastModified: now, changeFrequency: 'weekly', priority: 0.9 },
    { url: `${SITE}/projects`, lastModified: now, changeFrequency: 'weekly', priority: 0.9 },
  ];

  // Dynamic pages
  const [developers, areas, projects] = await Promise.all([
    getDevelopers().catch(() => []),
    getAreas().catch(() => []),
    getProjects().catch(() => []),
  ]);

  const developerPages: MetadataRoute.Sitemap = developers.map((d) => ({
    url: `${SITE}/developers/${d.slug}`,
    lastModified: now,
    changeFrequency: 'weekly' as const,
    priority: 0.8,
  }));

  const areaPages: MetadataRoute.Sitemap = areas.map((a) => ({
    url: `${SITE}/areas/${a.slug}`,
    lastModified: now,
    changeFrequency: 'weekly' as const,
    priority: 0.8,
  }));

  const projectPages: MetadataRoute.Sitemap = projects.map((p) => ({
    url: `${SITE}/projects/${p.slug}`,
    lastModified: now,
    changeFrequency: 'weekly' as const,
    priority: 0.7,
  }));

  // Comparison pages — developer pairs
  const devComparisons: MetadataRoute.Sitemap = [];
  for (let i = 0; i < developers.length; i++) {
    for (let j = i + 1; j < developers.length; j++) {
      devComparisons.push({
        url: `${SITE}/compare/developers/${developers[i].slug}/${developers[j].slug}`,
        lastModified: now,
        changeFrequency: 'monthly' as const,
        priority: 0.6,
      });
    }
  }

  // Comparison pages — area pairs
  const areaComparisons: MetadataRoute.Sitemap = [];
  for (let i = 0; i < areas.length; i++) {
    for (let j = i + 1; j < areas.length; j++) {
      areaComparisons.push({
        url: `${SITE}/compare/areas/${areas[i].slug}/${areas[j].slug}`,
        lastModified: now,
        changeFrequency: 'monthly' as const,
        priority: 0.6,
      });
    }
  }

  return [
    ...staticPages,
    ...developerPages,
    ...areaPages,
    ...projectPages,
    ...devComparisons,
    ...areaComparisons,
  ];
}
