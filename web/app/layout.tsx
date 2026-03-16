import type { Metadata, Viewport } from "next";
import { Suspense } from 'react';
import { Inter, Cairo, Rajdhani } from 'next/font/google';
import "./globals.css";
import { AuthProvider } from '@/contexts/AuthContext';
import { ThemeProvider } from '@/contexts/ThemeContext';
import { LanguageProvider } from '@/contexts/LanguageContext';
import { GamificationProvider } from '@/contexts/GamificationContext';
import NeuralBackground from '@/components/NeuralBackground';
import GamificationOverlay from '@/components/GamificationOverlay';
import CommandPalette from '@/components/CommandPalette';
import { ErrorBoundaryProvider } from '@/components/ErrorBoundaryProvider';
import { organizationJsonLd } from '@/lib/json-ld';
import OrchestratorTracker from '@/components/OrchestratorTracker';
import { LeadScoreProvider } from '@/contexts/LeadScoreContext';
import PriorityHandoff from '@/components/PriorityHandoff';

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

const rajdhani = Rajdhani({
  subsets: ['latin'],
  weight: ['300', '400', '500', '600', '700'],
  display: 'swap',
  variable: '--font-rajdhani',
});

export const viewport: Viewport = {
  width: 'device-width',
  initialScale: 1,
  maximumScale: 1,
  viewportFit: 'cover',
};

export const metadata: Metadata = {
  title: "Osool | Your AI Real Estate Advisor for Egypt",
  description: "Chat with CoInvestor, your AI-powered real estate advisor. Get instant property matches, price analysis, and investment insights from 3,274 verified Egyptian properties. Powered by Claude 3.5 Sonnet.",
  keywords: ["real estate", "Egypt", "AI", "property", "CoInvestor", "investment", "New Cairo", "Sheikh Zayed", "عقارات", "مصر"],
  authors: [{ name: "Osool" }],
  openGraph: {
    title: "Osool | Your AI Real Estate Advisor for Egypt",
    description: "Chat with CoInvestor in Egyptian Arabic or English. Get AI-powered property recommendations, price valuations, and investment analysis.",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className={`dark ${inter.variable} ${cairo.variable} ${rajdhani.variable}`} suppressHydrationWarning>
      <head>
        <script
          type="application/ld+json"
          dangerouslySetInnerHTML={{ __html: JSON.stringify(organizationJsonLd()) }}
        />
        <link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap" rel="stylesheet" />
      </head>
      <body>
        <ErrorBoundaryProvider>
          <ThemeProvider>
            <LanguageProvider>
              <AuthProvider>
                <GamificationProvider>
                  <LeadScoreProvider>
                  {/* Skip to content — accessibility */}
                  <a
                    href="#main-content"
                    className="sr-only focus:not-sr-only focus:fixed focus:top-2 focus:left-2 focus:z-[200] focus:rounded-lg focus:bg-emerald-600 focus:px-4 focus:py-2 focus:text-sm focus:font-semibold focus:text-white focus:outline-none"
                  >
                    Skip to main content
                  </a>

                  {/* Neural Background Layer */}
                  <NeuralBackground />

                  {/* Content Layer — inline styles guarantee these can never be overridden */}
                  <div
                    id="app-root"
                    role="application"
                    style={{
                      display: 'flex',
                      flexDirection: 'column',
                      width: '100%',
                      maxWidth: '100vw',
                      minHeight: '100vh',
                      flex: '1 1 0%',
                      position: 'relative',
                      zIndex: 10,
                      overflow: 'auto',
                      overflowX: 'hidden',
                    }}
                  >
                    <main id="main-content">
                      {children}
                    </main>
                  </div>

                  {/* Global Gamification Notifications */}
                  <GamificationOverlay />

                  {/* Lead-to-Advisor Handoff (appears when lead score is high) */}
                  <PriorityHandoff />

                  {/* Global Command Palette (Ctrl+K / ⌘K) */}
                  <CommandPalette />

                  {/* Orchestrator tracking — page views, UTM attribution */}
                  <Suspense fallback={null}>
                    <OrchestratorTracker />
                  </Suspense>
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
