'use client';

import Link from 'next/link';
import { motion } from 'framer-motion';
import { ArrowRight, Sparkles } from 'lucide-react';

import { useAuth } from '@/contexts/AuthContext';
import { useLanguage } from '@/contexts/LanguageContext';

import LanguageToggle from '@/components/LanguageToggle';
import RealityCheckPanel from '@/components/freemium/RealityCheckPanel';

const COPY = {
  en: {
    product: 'Osool',
    strapline: 'AI-native real estate intelligence for Egypt',
    heroTitle: 'Buy right. With numbers, not promises.',
    heroSubtitle:
      'Osool audits broker proposals, exposes hidden financing premiums, and pivots you into verified alternatives at fairer prices — in one conversation.',
    openChat: 'Open Intelligence Chat',
    signIn: 'Sign In',
    primaryKicker: 'Your AI property advisor',
    workspaceHint: 'Live diagnostic workspace with NPV and La2ta intelligence',
    ctaChat: 'Ask the advisor — free',
    ctaCheck: 'Check your offer — free',
    ctaPricing: 'See Osool Pro',
  },
  ar: {
    product: 'أصول',
    strapline: 'ذكاء عقاري مصري مدعوم بالذكاء الاصطناعي',
    heroTitle: 'اشتري صح. بالأرقام، مش بالكلام.',
    heroSubtitle:
      'أصول بيراجع عروض السماسرة، يكشف تكلفة التمويل المخفية، ويوريك بدائل موثقة بأسعار أعدل — في محادثة واحدة.',
    openChat: 'افتح محادثة الذكاء',
    signIn: 'تسجيل الدخول',
    primaryKicker: 'مستشارك العقاري الذكي',
    workspaceHint: 'مساحة تشخيص حية تتضمن صافي القيمة الحالية وذكاء اللقطة',
    ctaChat: 'اسأل المستشار مجانًا',
    ctaCheck: 'افحص عرضك مجانًا',
    ctaPricing: 'شوف باقة أصول برو',
  },
} as const;

export default function HomePage() {
  const { isAuthenticated, loading } = useAuth();
  const { language } = useLanguage();

  const isArabic = language === 'ar';
  const copy = isArabic ? COPY.ar : COPY.en;

  return (
    <main dir={isArabic ? 'rtl' : 'ltr'} className="relative min-h-screen overflow-hidden bg-[#0D0E12] text-zinc-100">
      <div
        aria-hidden="true"
        className="pointer-events-none absolute inset-0 opacity-90"
        style={{
          background:
            'radial-gradient(1200px 440px at 12% -10%, rgba(16,185,129,0.16), transparent 68%), radial-gradient(780px 380px at 88% 8%, rgba(251,191,36,0.08), transparent 72%), linear-gradient(180deg, rgba(13,14,18,1) 0%, rgba(11,12,16,1) 100%)',
        }}
      />

      <div className="relative mx-auto flex w-full max-w-7xl flex-col px-4 pb-14 pt-6 sm:px-6 lg:px-8">
        <header className="mb-10 flex items-center justify-between rounded-2xl border border-zinc-800/70 bg-zinc-900/45 px-4 py-3 backdrop-blur-md">
          <div className="flex items-center gap-3">
            <div className="grid h-9 w-9 place-items-center rounded-xl border border-emerald-400/35 bg-emerald-500/12 text-xs font-semibold uppercase tracking-[0.16em] text-emerald-300">
              OA
            </div>
            <div>
              <p className="text-sm font-semibold text-zinc-100">{copy.product}</p>
              <p className="text-[11px] text-zinc-500">{copy.strapline}</p>
            </div>
          </div>

          <div className="flex items-center gap-2">
            <LanguageToggle />
            {!loading ? (
              <Link
                href={isAuthenticated ? '/chat' : '/login'}
                className="inline-flex items-center gap-1.5 rounded-xl border border-zinc-700/80 bg-zinc-900/70 px-3 py-2 text-xs font-semibold text-zinc-100 transition-colors hover:bg-zinc-800"
              >
                {isAuthenticated ? copy.openChat : copy.signIn}
                <ArrowRight className="h-3.5 w-3.5" aria-hidden="true" />
              </Link>
            ) : null}
          </div>
        </header>

        <section className="mb-8 grid gap-6 lg:grid-cols-[1.05fr_0.95fr] lg:items-end">
          <motion.div
            initial={{ opacity: 0, y: 14 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, ease: [0.16, 1, 0.3, 1] }}
            className="max-w-3xl"
          >
            <div className="inline-flex items-center gap-2 rounded-full border border-emerald-500/25 bg-emerald-500/12 px-3 py-1 text-xs font-semibold uppercase tracking-[0.14em] text-emerald-300">
              <Sparkles className="h-3.5 w-3.5" aria-hidden="true" />
              {copy.primaryKicker}
            </div>

            <h1 className="mt-4 text-3xl font-semibold tracking-tight text-zinc-50 sm:text-4xl lg:text-5xl">
              {copy.heroTitle}
            </h1>

            <p className="mt-4 max-w-2xl text-sm leading-relaxed text-zinc-400 sm:text-base">
              {copy.heroSubtitle}
            </p>

            <div className="mt-6 flex flex-wrap items-center gap-3">
              <Link
                href="/chat"
                className="inline-flex items-center gap-2 rounded-2xl bg-emerald-500 px-5 py-3 text-sm font-semibold text-white transition-colors hover:bg-emerald-600"
              >
                {copy.ctaChat}
                <ArrowRight className={`h-4 w-4 ${isArabic ? 'rotate-180' : ''}`} aria-hidden="true" />
              </Link>
              <Link
                href="/pricing"
                className="inline-flex items-center gap-2 rounded-2xl border border-zinc-700/80 bg-zinc-900/70 px-5 py-3 text-sm font-semibold text-zinc-100 transition-colors hover:bg-zinc-800"
              >
                {copy.ctaPricing}
              </Link>
            </div>
          </motion.div>

          <motion.div
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.45, ease: [0.16, 1, 0.3, 1], delay: 0.05 }}
            className="rounded-2xl border border-zinc-800/65 bg-zinc-900/40 p-4 backdrop-blur-md"
          >
            <p className="text-xs font-semibold uppercase tracking-[0.13em] text-zinc-500">{copy.workspaceHint}</p>
            <div className="mt-3 grid grid-cols-3 gap-2 text-xs">
              <div className="rounded-xl border border-zinc-800/70 bg-zinc-950/65 px-3 py-2 text-zinc-400">NPV Engine</div>
              <div className="rounded-xl border border-zinc-800/70 bg-zinc-950/65 px-3 py-2 text-zinc-400">Risk Gauge</div>
              <div className="rounded-xl border border-zinc-800/70 bg-zinc-950/65 px-3 py-2 text-zinc-400">La2ta Feed</div>
            </div>
          </motion.div>
        </section>

        <section>
          <RealityCheckPanel />
        </section>
      </div>
    </main>
  );
}
