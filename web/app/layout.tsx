import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { AuthProvider } from '@/contexts/AuthContext';
import { ThemeProvider } from '@/contexts/ThemeContext';
import { LanguageProvider } from '@/contexts/LanguageContext';

const inter = Inter({
  variable: "--font-inter",
  subsets: ["latin"],
});

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
        <link href="https://fonts.googleapis.com/css2?family=Cairo:wght@400;500;600;700&display=swap" rel="stylesheet" />
      </head>
      <body className={`${inter.variable} antialiased`}>
        <ThemeProvider>
          <LanguageProvider>
            <AuthProvider>
              {children}
            </AuthProvider>
          </LanguageProvider>
        </ThemeProvider>
      </body>
    </html>
  );
}
