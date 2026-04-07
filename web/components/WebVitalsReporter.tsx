'use client';

import { useReportWebVitals } from 'next/web-vitals';

/**
 * Web Vitals reporter — captures CLS, FID, FCP, LCP, TTFB metrics.
 * Mount once in the root layout to enable performance monitoring.
 */
export function WebVitalsReporter() {
  useReportWebVitals((metric) => {
    // Log to console in dev for debugging
    if (process.env.NODE_ENV === 'development') {
      console.log(`[WebVital] ${metric.name}: ${metric.value.toFixed(2)} (${metric.rating})`);
    }

    // Send to analytics endpoint
    const analyticsUrl = process.env.NEXT_PUBLIC_API_URL;
    if (analyticsUrl) {
      // Use navigator.sendBeacon for reliable delivery (non-blocking)
      const body = JSON.stringify({
        name: metric.name,        // CLS | FID | FCP | LCP | TTFB | INP
        value: metric.value,
        rating: metric.rating,    // good | needs-improvement | poor
        delta: metric.delta,
        id: metric.id,
        navigationType: metric.navigationType,
      });

      if (navigator.sendBeacon) {
        navigator.sendBeacon(`${analyticsUrl}/api/analytics/web-vitals`, body);
      }
    }
  });

  return null;
}
