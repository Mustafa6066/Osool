import type { Metadata, Viewport } from "next";
import { Suspense } from 'react';
import "./globals.css";
import { AuthProvider } from '@/contexts/AuthContext';
import { ThemeProvider } from '@/contexts/ThemeContext';
import { LanguageProvider } from '@/contexts/LanguageContext';
import { CurrencyProvider } from '@/contexts/CurrencyContext';
import { GamificationProvider } from '@/contexts/GamificationContext';
import GamificationOverlay from '@/components/GamificationOverlay';
import CommandPalette from '@/components/CommandPalette';
import { ErrorBoundaryProvider } from '@/components/ErrorBoundaryProvider';
import { organizationJsonLd } from '@/lib/json-ld';
import OrchestratorTracker from '@/components/OrchestratorTracker';
import { LeadScoreProvider } from '@/contexts/LeadScoreContext';
import PriorityHandoff from '@/components/PriorityHandoff';
import HapticFeedback from '@/components/HapticFeedback';
import { WebVitalsReporter } from '@/components/WebVitalsReporter';
import ServiceStatusBanner from '@/components/ServiceStatusBanner';
import FluentAppProvider from '@/components/FluentAppProvider';
import CookieConsent from '@/components/CookieConsent';

export const viewport: Viewport = {
  width: 'device-width',
  initialScale: 1,
  maximumScale: 5,
  viewportFit: 'cover',
  themeColor: [
    { media: '(prefers-color-scheme: light)', color: '#FAFAFA' },
    { media: '(prefers-color-scheme: dark)', color: '#09090B' },
  ],
};

export const metadata: Metadata = {
  title: "Osool — The honest way to buy property in Egypt",
  description: "An AI property advisor built for Egypt. Ask in Arabic or English and get a straight read on whether an asking price is fair against similar listed units. Private beta in New Cairo & Sheikh Zayed.",
  keywords: ["real estate", "Egypt", "AI property advisor", "price fairness", "New Cairo", "Sheikh Zayed", "عقارات", "مصر", "تطبيق عقارات"],
  authors: [{ name: "Osool" }],
  openGraph: {
    title: "Osool — The honest way to buy property in Egypt",
    description: "Ask about any Egyptian property in Arabic or English. An honest read on price — no hype, no fake numbers. Private beta.",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html
      lang="en"
      suppressHydrationWarning
    >
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link
          rel="stylesheet"
          href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Newsreader:ital,wght@0,400;0,500;1,400;1,500&family=Cairo:wght@400;500;600;700&display=swap"
        />
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: JSON.stringify(organizationJsonLd()) }}
        />

        {/* No-JS fallback: scroll-reveal sections start at opacity:0 and only
            become visible when JS adds `.in`. Without JS they would stay
            invisible, so force them visible when scripting is disabled. */}
        <noscript>
          <style>{`.osool-reveal{opacity:1 !important;transform:none !important}`}</style>
        </noscript>
      </head>
      <body className="relative min-h-dvh overflow-x-hidden antialiased">
        <ErrorBoundaryProvider>
          <ThemeProvider>
            <LanguageProvider>
              <CurrencyProvider>
              <FluentAppProvider>
                <AuthProvider>
                  <GamificationProvider>
                    <LeadScoreProvider>
                      {/* Skip to content — accessibility */}
                      <a
                        href="#main-content"
                        className="sr-only focus:not-sr-only focus:fixed focus:top-3 focus:start-3 focus:z-[200] focus:rounded-xl focus:bg-primary focus:px-4 focus:py-2 focus:text-sm focus:font-semibold focus:text-white focus:ring-2 focus:ring-[var(--color-primary)]"
                      >
                        Skip to main content
                      </a>

                      {/* App shell */}
                      <div
                        id="app-root"
                        className="relative z-10 flex min-h-dvh w-full flex-col overflow-x-hidden"
                      >
                        <ServiceStatusBanner />
                        <main id="main-content" className="flex-1">
                          {children}
                        </main>
                      </div>

                      {/* Global overlays */}
                      <GamificationOverlay />
                      <PriorityHandoff />
                      <HapticFeedback />
                      <CommandPalette />
                      <Suspense fallback={null}>
                        <OrchestratorTracker />
                      </Suspense>
                      <WebVitalsReporter />
                      <CookieConsent />
                    </LeadScoreProvider>
                  </GamificationProvider>
                </AuthProvider>
              </FluentAppProvider>
              </CurrencyProvider>
            </LanguageProvider>
          </ThemeProvider>
        </ErrorBoundaryProvider>
      </body>
    </html>
  );
}
