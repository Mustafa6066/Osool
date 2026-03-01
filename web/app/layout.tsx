import type { Metadata } from "next";
import "./globals.css";
import { AuthProvider } from '@/contexts/AuthContext';
import { ThemeProvider } from '@/contexts/ThemeContext';
import { LanguageProvider } from '@/contexts/LanguageContext';
import { GamificationProvider } from '@/contexts/GamificationContext';
import NeuralBackground from '@/components/NeuralBackground';
import GamificationOverlay from '@/components/GamificationOverlay';

export const metadata: Metadata = {
  title: "Osool | Your AI Real Estate Advisor for Egypt",
  description: "Chat with AMR, your AI-powered real estate advisor. Get instant property matches, price analysis, and investment insights from 3,274 verified Egyptian properties. Powered by Claude 3.5 Sonnet.",
  keywords: ["real estate", "Egypt", "AI", "property", "AMR", "investment", "New Cairo", "Sheikh Zayed", "عقارات", "مصر"],
  authors: [{ name: "Osool" }],
  openGraph: {
    title: "Osool | Your AI Real Estate Advisor for Egypt",
    description: "Chat with AMR in Egyptian Arabic or English. Get AI-powered property recommendations, price valuations, and investment analysis.",
    type: "website",
  },
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="en" className="dark" suppressHydrationWarning>
      <head>
        <link rel="preconnect" href="https://fonts.googleapis.com" />
        <link rel="preconnect" href="https://fonts.gstatic.com" crossOrigin="anonymous" />
        <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&family=Cairo:wght@300;400;500;600;700&family=Rajdhani:wght@300;400;500;600;700&display=swap" rel="stylesheet" />
        <link href="https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:wght,FILL@100..700,0..1&display=swap" rel="stylesheet" />
      </head>
      <body className="antialiased selection:bg-[var(--color-primary)] selection:text-white">
        <ThemeProvider>
          <LanguageProvider>
            <AuthProvider>
              <GamificationProvider>
                {/* Neural Background Layer */}
                <NeuralBackground />

                {/* Content Layer */}
                <div className="relative z-10 flex flex-col overflow-auto" style={{ width: '100vw', minHeight: '100vh', flex: 1 }}>
                  {children}
                </div>

                {/* Global Gamification Notifications */}
                <GamificationOverlay />
              </GamificationProvider>
            </AuthProvider>
          </LanguageProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
