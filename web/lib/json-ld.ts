/**
 * JSON-LD structured data helpers for SEO pages.
 * Generates Schema.org markup for Google rich results.
 */

const SITE = process.env.NEXT_PUBLIC_SITE_URL || 'https://osool.eg';

export function organizationJsonLd() {
  return {
    '@context': 'https://schema.org',
    '@type': 'Organization',
    name: 'Osool',
    alternateName: 'أصول',
    url: SITE,
    description:
      'AI-powered real estate investment advisor for the Egyptian market. Powered by Claude AI.',
    areaServed: { '@type': 'Country', name: 'Egypt' },
    knowsAbout: ['Real Estate', 'Investment', 'Egypt Property Market'],
  };
}

export function developerJsonLd(dev: {
  name: string;
  name_ar?: string;
  slug: string;
  description?: string;
  founded_year?: number;
  overall_score?: number;
}) {
  return {
    '@context': 'https://schema.org',
    '@type': 'Organization',
    name: dev.name,
    alternateName: dev.name_ar,
    url: `${SITE}/developers/${dev.slug}`,
    description: dev.description,
    foundingDate: dev.founded_year ? `${dev.founded_year}` : undefined,
    aggregateRating: dev.overall_score
      ? {
          '@type': 'AggregateRating',
          ratingValue: (dev.overall_score / 10).toFixed(1),
          bestRating: '10',
          worstRating: '0',
          ratingCount: 1,
        }
      : undefined,
  };
}

export function projectJsonLd(project: {
  name: string;
  slug: string;
  min_price_per_meter?: number;
  max_price_per_meter?: number;
  min_unit_size?: number;
  max_unit_size?: number;
  amenities?: string;
}) {
  return {
    '@context': 'https://schema.org',
    '@type': 'RealEstateListing',
    name: project.name,
    url: `${SITE}/projects/${project.slug}`,
    offers: project.min_price_per_meter
      ? {
          '@type': 'AggregateOffer',
          priceCurrency: 'EGP',
          lowPrice: project.min_price_per_meter,
          highPrice: project.max_price_per_meter,
        }
      : undefined,
    floorSize: project.min_unit_size
      ? {
          '@type': 'QuantitativeValue',
          minValue: project.min_unit_size,
          maxValue: project.max_unit_size,
          unitCode: 'MTK',
        }
      : undefined,
    amenityFeature: (() => {
      try {
        const arr = typeof project.amenities === 'string' ? JSON.parse(project.amenities) : project.amenities;
        return Array.isArray(arr) ? arr.map((a: string) => ({ '@type': 'LocationFeatureSpecification', name: a })) : undefined;
      } catch { return undefined; }
    })(),
  };
}

export function areaJsonLd(area: {
  name: string;
  slug: string;
  city?: string;
  avg_price_per_meter?: number;
  lat?: number;
  lng?: number;
}) {
  return {
    '@context': 'https://schema.org',
    '@type': 'Place',
    name: area.name,
    url: `${SITE}/areas/${area.slug}`,
    containedInPlace: area.city
      ? { '@type': 'City', name: area.city }
      : undefined,
    geo:
      area.lat && area.lng
        ? {
            '@type': 'GeoCoordinates',
            latitude: area.lat,
            longitude: area.lng,
          }
        : undefined,
  };
}

export function comparisonJsonLd(
  type: 'developers' | 'areas',
  name1: string,
  name2: string,
  slug1: string,
  slug2: string
) {
  return {
    '@context': 'https://schema.org',
    '@type': 'WebPage',
    name: `${name1} vs ${name2} — ${type === 'developers' ? 'Developer' : 'Area'} Comparison`,
    url: `${SITE}/compare/${type}/${slug1}/${slug2}`,
    description: `Compare ${name1} and ${name2} for Egyptian real estate investment.`,
    isPartOf: { '@type': 'WebSite', name: 'Osool', url: SITE },
  };
}
