'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { Check, Crown, FileText, Loader2, Sparkles } from 'lucide-react';
import AppShell from '@/components/nav/AppShell';
import { useAuth } from '@/contexts/AuthContext';
import { useLanguage } from '@/contexts/LanguageContext';
import {
  BillingPlan,
  getBillingPlans,
  getBillingStatus,
  purchaseReport,
  subscribeToPro,
} from '@/lib/api';

const PLAN_ICONS: Record<string, React.ReactNode> = {
  free: <Sparkles className="h-6 w-6" />,
  pro_monthly: <Crown className="h-6 w-6" />,
  valuation_report: <FileText className="h-6 w-6" />,
};

export default function PricingPage() {
  const router = useRouter();
  const { isAuthenticated } = useAuth();
  const { language, direction } = useLanguage();
  const isRTL = direction === 'rtl';

  const [plans, setPlans] = useState<BillingPlan[]>([]);
  const [paymentsEnabled, setPaymentsEnabled] = useState(true);
  const [loading, setLoading] = useState(true);
  const [paying, setPaying] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [currentTier, setCurrentTier] = useState<string>('free');

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const data = await getBillingPlans();
        if (cancelled) return;
        setPlans(data.plans);
        setPaymentsEnabled(data.payments_enabled);
      } catch {
        if (!cancelled) setError(isRTL ? 'تعذر تحميل الباقات.' : 'Could not load plans.');
      } finally {
        if (!cancelled) setLoading(false);
      }
    })();
    if (isAuthenticated) {
      getBillingStatus()
        .then((s) => !cancelled && setCurrentTier(s.tier))
        .catch(() => undefined);
    }
    return () => {
      cancelled = true;
    };
  }, [isAuthenticated, isRTL]);

  const startPayment = async (planId: string) => {
    if (!isAuthenticated) {
      router.push(`/login?next=${encodeURIComponent('/pricing')}`);
      return;
    }
    setError(null);
    setPaying(planId);
    try {
      const initiation =
        planId === 'pro_monthly' ? await subscribeToPro() : await purchaseReport();
      sessionStorage.setItem('osool_checkout_iframe', initiation.iframe_url);
      sessionStorage.setItem('osool_checkout_order', initiation.order_id);
      router.push('/checkout/pay');
    } catch (err: unknown) {
      const detail =
        typeof err === 'object' && err !== null && 'response' in err
          ? // eslint-disable-next-line @typescript-eslint/no-explicit-any
            (err as any).response?.data?.detail
          : null;
      setError(
        typeof detail === 'string'
          ? detail
          : isRTL
            ? 'حدث خطأ أثناء بدء الدفع. حاول مرة أخرى.'
            : 'Something went wrong starting the payment. Please try again.',
      );
      setPaying(null);
    }
  };

  const isPro = currentTier === 'premium' || currentTier === 'admin';

  return (
    <AppShell>
      <div className="h-full overflow-y-auto bg-[var(--color-background)]" dir={direction}>
        <div className="mx-auto max-w-6xl px-4 py-10 sm:px-6 sm:py-14">
          <div className="text-center">
            <div className="inline-flex items-center gap-2 rounded-full border border-emerald-500/20 bg-emerald-500/10 px-3 py-1 text-xs font-semibold uppercase tracking-[0.18em] text-emerald-600 dark:text-emerald-400">
              <Crown className="h-3.5 w-3.5" />
              {isRTL ? 'الباقات' : 'Pricing'}
            </div>
            <h1 className="mt-5 text-3xl font-semibold tracking-tight text-[var(--color-text-primary)] sm:text-4xl">
              {isRTL ? 'اختار الباقة المناسبة ليك' : 'Choose the plan that fits you'}
            </h1>
            <p className="mx-auto mt-3 max-w-2xl text-[var(--color-text-secondary)]">
              {isRTL
                ? 'ابدأ مجانًا، وارتقِ لما تحتاج بيانات الصفقات الكاملة وتنبيهات اللقطات. كل المدفوعات بالجنيه المصري عبر بوابة Paymob الآمنة.'
                : 'Start free, upgrade when you need full deal data and La2ta alerts. All payments in EGP via the secure Paymob gateway.'}
            </p>
          </div>

          {error && (
            <div className="mx-auto mt-6 max-w-xl rounded-2xl border border-red-500/30 bg-red-500/10 px-4 py-3 text-center text-sm text-red-500">
              {error}
            </div>
          )}

          {!paymentsEnabled && !loading && (
            <div className="mx-auto mt-6 max-w-xl rounded-2xl border border-amber-500/30 bg-amber-500/10 px-4 py-3 text-center text-sm text-amber-600">
              {isRTL
                ? 'المدفوعات غير متاحة مؤقتًا — جرّب لاحقًا.'
                : 'Payments are temporarily unavailable — please check back soon.'}
            </div>
          )}

          {loading ? (
            <div className="flex justify-center py-24">
              <Loader2 className="h-8 w-8 animate-spin text-emerald-500" />
            </div>
          ) : (
            <div className="mt-12 grid gap-6 lg:grid-cols-3">
              {plans.map((plan) => {
                const highlighted = plan.id === 'pro_monthly';
                const isCurrentPro = highlighted && isPro;
                return (
                  <div
                    key={plan.id}
                    className={`relative flex flex-col rounded-[28px] border p-7 ${
                      highlighted
                        ? 'border-emerald-500/60 bg-emerald-500/[0.06] shadow-[0_30px_80px_rgba(16,185,129,0.12)]'
                        : 'border-[var(--color-border)] bg-[var(--color-surface)]'
                    }`}
                  >
                    {highlighted && (
                      <span className="absolute -top-3 start-7 rounded-full bg-emerald-500 px-3 py-1 text-xs font-bold text-white">
                        {isRTL ? 'الأكثر قيمة' : 'Best value'}
                      </span>
                    )}
                    <div
                      className={`inline-flex h-12 w-12 items-center justify-center rounded-2xl ${
                        highlighted
                          ? 'bg-emerald-500 text-white'
                          : 'bg-[var(--color-background)] text-emerald-500'
                      }`}
                    >
                      {PLAN_ICONS[plan.id] ?? <Sparkles className="h-6 w-6" />}
                    </div>
                    <h2 className="mt-4 text-xl font-semibold text-[var(--color-text-primary)]">
                      {plan.name[language]}
                    </h2>
                    <div className="mt-2 flex items-baseline gap-2">
                      <span className="text-4xl font-bold text-[var(--color-text-primary)]">
                        {plan.price_egp === 0
                          ? isRTL
                            ? 'مجاني'
                            : 'Free'
                          : plan.price_egp.toLocaleString(isRTL ? 'ar-EG' : 'en-US')}
                      </span>
                      {plan.price_egp > 0 && (
                        <span className="text-sm text-[var(--color-text-secondary)]">
                          {isRTL ? 'جنيه' : 'EGP'}
                          {plan.period === 'month' && (isRTL ? ' / شهر' : ' / month')}
                          {plan.period === 'one_time' && (isRTL ? ' / مرة واحدة' : ' one-time')}
                        </span>
                      )}
                    </div>
                    <ul className="mt-6 flex-1 space-y-3">
                      {plan.features[language].map((feature) => (
                        <li key={feature} className="flex items-start gap-2 text-sm text-[var(--color-text-secondary)]">
                          <Check className="mt-0.5 h-4 w-4 shrink-0 text-emerald-500" />
                          {feature}
                        </li>
                      ))}
                    </ul>
                    <div className="mt-8">
                      {plan.id === 'free' ? (
                        <button
                          onClick={() => router.push('/chat')}
                          className="w-full rounded-2xl border border-[var(--color-border)] py-3 text-sm font-semibold text-[var(--color-text-primary)] transition hover:bg-[var(--color-background)]"
                        >
                          {isRTL ? 'ابدأ مجانًا' : 'Start free'}
                        </button>
                      ) : isCurrentPro ? (
                        <div className="w-full rounded-2xl bg-emerald-500/15 py-3 text-center text-sm font-semibold text-emerald-600">
                          {isRTL ? '✓ باقتك الحالية' : '✓ Your current plan'}
                        </div>
                      ) : (
                        <button
                          onClick={() => startPayment(plan.id)}
                          disabled={!paymentsEnabled || paying !== null}
                          className={`flex w-full items-center justify-center gap-2 rounded-2xl py-3 text-sm font-semibold transition disabled:cursor-not-allowed disabled:opacity-50 ${
                            highlighted
                              ? 'bg-emerald-500 text-white hover:bg-emerald-600'
                              : 'border border-emerald-500/40 text-emerald-600 hover:bg-emerald-500/10'
                          }`}
                        >
                          {paying === plan.id && <Loader2 className="h-4 w-4 animate-spin" />}
                          {plan.id === 'pro_monthly'
                            ? isRTL
                              ? 'اشترك في أصول برو'
                              : 'Get Osool Pro'
                            : isRTL
                              ? 'اشترِ التقرير'
                              : 'Buy report'}
                        </button>
                      )}
                    </div>
                  </div>
                );
              })}
            </div>
          )}

          <p className="mt-10 text-center text-xs text-[var(--color-text-muted)]">
            {isRTL
              ? 'الدفع آمن عبر Paymob (فيزا، ماستركارد، محافظ إلكترونية). متوافق مع قانون البنك المركزي ١٩٤/٢٠٢٠ — كل المعاملات بالجنيه المصري.'
              : 'Secure checkout via Paymob (Visa, Mastercard, mobile wallets). CBE Law 194/2020 compliant — all transactions in EGP.'}
          </p>
        </div>
      </div>
    </AppShell>
  );
}
