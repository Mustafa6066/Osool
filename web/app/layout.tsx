import type { Metadata, Viewport } from "next";
import { Suspense } from 'react';
import { Inter, Cairo } from 'next/font/google';
import "./globals.css";
import { AuthProvider } from '@/contexts/AuthContext';
import { ThemeProvider } from '@/contexts/ThemeContext';
import { LanguageProvider } from '@/contexts/LanguageContext';
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

const inter = Inter({
  subsets: ['latin'],
  weight: ['300', '400', '500', '600', '700'],
  display: 'swap',
  variable: '--font-inter',
});

const cairo = Cairo({
  subsets: ['arabic', 'latin'],
  weight: ['300', '400', '500', '600', '700'],
  display: 'swap',
  variable: '--font-cairo',
});

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
  title: "Osool | AI Real Estate Advisor for Egypt",
  description: "Chat with Osool Advisor, your AI-powered real estate guide. Get instant property matches, price analysis, and investment insights for Egyptian properties.",
  keywords: ["real estate", "Egypt", "AI", "property", "Osool Advisor", "investment", "New Cairo", "Sheikh Zayed", "عقارات", "مصر"],
  authors: [{ name: "Osool" }],
  openGraph: {
    title: "Osool | AI Real Estate Advisor for Egypt",
    description: "AI-powered property recommendations, price valuations, and investment analysis for Egypt.",
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
      className={`${inter.variable} ${cairo.variable}`}
      suppressHydrationWarning
    >
      <head>
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: JSON.stringify(organizationJsonLd()) }}
        />

      </head>
      <body className="relative min-h-dvh overflow-x-hidden antialiased">
        <ErrorBoundaryProvider>
          <ThemeProvider>
            <LanguageProvider>
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
                  </LeadScoreProvider>
                </GamificationProvider>
              </AuthProvider>
            </LanguageProvider>
          </ThemeProvider>
        </ErrorBoundaryProvider>
      </body>
    </html>
  );
}
