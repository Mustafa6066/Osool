'use client';

import { useState } from 'react';
import { Calculator, Crown, Landmark, Loader2 } from 'lucide-react';
import AppShell from '@/components/nav/AppShell';
import UpgradeModal from '@/components/billing/UpgradeModal';
import { useLanguage } from '@/contexts/LanguageContext';
import { calculateMortgage, MortgageResult } from '@/lib/api';

const fmt = (n: number, ar: boolean) =>
  n.toLocaleString(ar ? 'ar-EG' : 'en-US', { maximumFractionDigits: 0 });

export default function MortgageCalculatorPage() {
  const { language, direction } = useLanguage();
  const isRTL = direction === 'rtl';

  const [price, setPrice] = useState(3_000_000);
  const [downPayment, setDownPayment] = useState(600_000);
  const [years, setYears] = useState(15);
  const [income, setIncome] = useState<number | ''>('');

  const [result, setResult] = useState<MortgageResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [upgradeOpen, setUpgradeOpen] = useState(false);

  const calculate = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await calculateMortgage({
        unit_price_egp: price,
        down_payment_egp: downPayment,
        years,
        monthly_income_egp: income === '' ? undefined : income,
      });
      setResult(data);
    } catch {
      setError(isRTL ? 'حدث خطأ في الحساب. حاول مرة أخرى.' : 'Calculation failed. Please try again.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <AppShell>
      <div className="h-full overflow-y-auto bg-[var(--color-background)]" dir={direction}>
        <div className="mx-auto max-w-4xl px-4 py-10 sm:px-6">
          <div className="inline-flex items-center gap-2 rounded-full border px-3 py-1 text-xs font-semibold uppercase tracking-[0.18em]" style={{ borderColor: 'var(--osool-accent-mid)', backgroundColor: 'var(--osool-accent-soft)', color: 'var(--osool-accent)' }}>
            <Landmark className="h-3.5 w-3.5" />
            {isRTL ? 'التمويل العقاري' : 'Mortgage'}
          </div>
          <h1 className="mt-5 text-3xl font-semibold tracking-tight text-[var(--color-text-primary)]">
            {isRTL ? 'حاسبة التمويل العقاري' : 'Mortgage Calculator'}
          </h1>
          <p className="mt-2 max-w-2xl text-[var(--color-text-secondary)]">
            {isRTL
              ? 'احسب قسطك الشهري بأسعار مبادرة البنك المركزي المدعومة (٣٪ و٨٪) والسعر البنكي القياسي — واعرف أنت مؤهل لأنهي مبادرة.'
              : "Calculate your monthly payment at the CBE subsidized initiative rates (3% & 8%) and the standard bank rate — and see which tier you qualify for."}
          </p>

          {/* Inputs */}
          <div className="mt-8 grid gap-4 rounded-[28px] border border-[var(--color-border)] bg-[var(--color-surface)] p-6 sm:grid-cols-2">
            <label className="block">
              <span className="text-sm font-medium text-[var(--color-text-primary)]">
                {isRTL ? 'سعر الوحدة (جنيه)' : 'Unit price (EGP)'}
              </span>
              <input
                type="number"
                min={100_000}
                value={price}
                onChange={(e) => setPrice(Number(e.target.value))}
                className="mt-2 w-full rounded-2xl border border-[var(--color-border)] bg-[var(--color-background)] px-4 py-3 text-[var(--color-text-primary)] outline-none focus:border-[var(--osool-accent)]"
              />
            </label>
            <label className="block">
              <span className="text-sm font-medium text-[var(--color-text-primary)]">
                {isRTL ? 'المقدم (جنيه)' : 'Down payment (EGP)'}
              </span>
              <input
                type="number"
                min={0}
                value={downPayment}
                onChange={(e) => setDownPayment(Number(e.target.value))}
                className="mt-2 w-full rounded-2xl border border-[var(--color-border)] bg-[var(--color-background)] px-4 py-3 text-[var(--color-text-primary)] outline-none focus:border-[var(--osool-accent)]"
              />
            </label>
            <label className="block">
              <span className="text-sm font-medium text-[var(--color-text-primary)]">
                {isRTL ? `مدة التمويل: ${years} سنة` : `Term: ${years} years`}
              </span>
              <input
                type="range"
                min={5}
                max={30}
                step={1}
                value={years}
                onChange={(e) => setYears(Number(e.target.value))}
                className="mt-3 w-full"
                style={{ accentColor: 'var(--osool-accent)' }}
              />
            </label>
            <label className="block">
              <span className="text-sm font-medium text-[var(--color-text-primary)]">
                {isRTL ? 'دخلك الشهري (اختياري)' : 'Monthly income (optional)'}
              </span>
              <input
                type="number"
                min={0}
                value={income}
                placeholder={isRTL ? 'لتحديد أهلية المبادرة' : 'For initiative eligibility'}
                onChange={(e) => setIncome(e.target.value === '' ? '' : Number(e.target.value))}
                className="mt-2 w-full rounded-2xl border border-[var(--color-border)] bg-[var(--color-background)] px-4 py-3 text-[var(--color-text-primary)] outline-none focus:border-[var(--osool-accent)]"
              />
            </label>
            <button
              onClick={calculate}
              disabled={loading || price <= 0 || downPayment >= price}
              className="sm:col-span-2 flex items-center justify-center gap-2 rounded-2xl py-3.5 text-sm font-semibold text-white transition hover:bg-[var(--osool-accent-dark)] disabled:cursor-not-allowed disabled:opacity-50"
              style={{ backgroundColor: 'var(--osool-accent)' }}
            >
              {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Calculator className="h-4 w-4" />}
              {isRTL ? 'احسب القسط' : 'Calculate'}
            </button>
          </div>

          {error && (
            <div className="mt-4 rounded-2xl border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-500">
              {error}
            </div>
          )}

          {/* Results */}
          {result && (
            <div className="mt-8 space-y-4">
              <div className="grid gap-4 sm:grid-cols-3">
                {result.tiers.map((tier) => {
                  const isBest = tier.id === result.best_eligible_tier;
                  return (
                    <div
                      key={tier.id}
                      className={`rounded-[24px] border p-5 ${
                        isBest
                          ? 'bg-[var(--osool-accent-soft)]'
                          : tier.eligible
                            ? 'border-[var(--color-border)] bg-[var(--color-surface)]'
                            : 'border-[var(--color-border)] bg-[var(--color-surface)] opacity-50'
                      }`}
                      style={isBest ? { borderColor: 'var(--osool-accent-mid)' } : undefined}
                    >
                      {isBest && (
                        <span className="rounded-full px-2.5 py-0.5 text-[10px] font-bold text-white" style={{ backgroundColor: 'var(--osool-accent)' }}>
                          {isRTL ? 'أفضل خيار ليك' : 'Best for you'}
                        </span>
                      )}
                      <h3 className="mt-2 text-sm font-semibold text-[var(--color-text-primary)]">
                        {tier.name[language]}
                      </h3>
                      <p className="text-xs text-[var(--color-text-muted)]">
                        {tier.annual_rate_pct}% {isRTL ? 'سنويًا' : 'annual'}
                        {!tier.eligible && ` — ${isRTL ? 'غير مؤهل' : 'not eligible'}`}
                      </p>
                      <p className="mt-3 text-2xl font-bold text-[var(--color-text-primary)]">
                        {fmt(tier.monthly_payment_egp, isRTL)}
                        <span className="text-sm font-normal text-[var(--color-text-secondary)]">
                          {' '}{isRTL ? 'ج/شهر' : 'EGP/mo'}
                        </span>
                      </p>
                      <p className="mt-1 text-xs text-[var(--color-text-secondary)]">
                        {isRTL ? 'إجمالي الفوائد' : 'Total interest'}: {fmt(tier.total_interest_egp, isRTL)}
                      </p>
                    </div>
                  );
                })}
              </div>

              {result.affordability && (
                <div
                  className={`rounded-[24px] border p-5 ${
                    result.affordability.affordable
                      ? ''
                      : 'border-amber-500/40 bg-amber-500/[0.06]'
                  }`}
                  style={
                    result.affordability.affordable
                      ? { borderColor: 'var(--osool-accent-mid)', backgroundColor: 'var(--osool-accent-soft)' }
                      : undefined
                  }
                >
                  <h3 className="flex items-center gap-2 text-sm font-semibold text-[var(--color-text-primary)]">
                    <Crown className="h-4 w-4" style={{ color: 'var(--osool-accent)' }} />
                    {isRTL ? 'تحليل القدرة الشرائية (برو)' : 'Affordability analysis (Pro)'}
                  </h3>
                  <p className="mt-2 text-sm text-[var(--color-text-secondary)]">
                    {result.affordability.affordable
                      ? isRTL
                        ? `القسط في حدود قدرتك — بيستهلك ${result.affordability.utilization_pct}٪ من سقف الـ٤٠٪ المسموح من دخلك.`
                        : `The payment fits — it uses ${result.affordability.utilization_pct}% of the 40%-of-income ceiling banks apply.`
                      : isRTL
                        ? `القسط أعلى من سقف الـ٤٠٪ من دخلك. أقصى سعر وحدة مناسب ليك تقريبًا ${fmt(result.affordability.max_affordable_unit_price_egp, isRTL)} جنيه.`
                        : `The payment exceeds the 40%-of-income ceiling. Your max affordable unit price is about ${fmt(result.affordability.max_affordable_unit_price_egp, isRTL)} EGP.`}
                  </p>
                </div>
              )}

              {result.affordability_gated && (
                <button
                  onClick={() => setUpgradeOpen(true)}
                  className="w-full rounded-[24px] border border-dashed p-5 text-start transition hover:bg-[var(--osool-accent-mid)]"
                  style={{ borderColor: 'var(--osool-accent-mid)', backgroundColor: 'var(--osool-accent-soft)' }}
                >
                  <h3 className="flex items-center gap-2 text-sm font-semibold text-[var(--color-text-primary)]">
                    <Crown className="h-4 w-4" style={{ color: 'var(--osool-accent)' }} />
                    {isRTL ? 'هل تقدر على القسط ده فعلاً؟' : 'Can you actually afford this payment?'}
                  </h3>
                  <p className="mt-1 text-sm text-[var(--color-text-secondary)]">
                    {isRTL
                      ? 'مع أصول برو: تحليل قدرتك الشرائية مقابل دخلك وأقصى سعر وحدة مناسب ليك.'
                      : 'With Osool Pro: affordability verdict vs your income and your max affordable unit price.'}
                  </p>
                </button>
              )}

              <p className="text-xs text-[var(--color-text-muted)]">
                {isRTL
                  ? `الأسعار استرشادية (آخر تحديث ${result.rates_last_updated}). شروط مبادرة البنك المركزي تتغير بقرارات رسمية — راجع البنك قبل التعاقد.`
                  : `Rates are indicative (last updated ${result.rates_last_updated}). CBE initiative terms change by decree — confirm with your bank before contracting.`}
              </p>
            </div>
          )}
        </div>
      </div>
      <UpgradeModal open={upgradeOpen} onClose={() => setUpgradeOpen(false)} source="mortgage-tool" />
    </AppShell>
  );
}
