'use client';

import { useState } from 'react';
import { Loader2, Scale } from 'lucide-react';
import AppShell from '@/components/nav/AppShell';
import { useLanguage } from '@/contexts/LanguageContext';
import { compareInstallmentVsCash, InstallmentVsCashResult } from '@/lib/api';

const fmt = (n: number, ar: boolean) =>
  n.toLocaleString(ar ? 'ar-EG' : 'en-US', { maximumFractionDigits: 0 });

export default function InstallmentsVsCashPage() {
  const { direction } = useLanguage();
  const isRTL = direction === 'rtl';

  const [totalPrice, setTotalPrice] = useState(5_000_000);
  const [downPayment, setDownPayment] = useState(500_000);
  const [years, setYears] = useState(8);
  const [perYear, setPerYear] = useState(4);
  const [cashPrice, setCashPrice] = useState<number | ''>('');

  const [result, setResult] = useState<InstallmentVsCashResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const calculate = async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await compareInstallmentVsCash({
        total_price_egp: totalPrice,
        down_payment_egp: downPayment,
        installment_years: years,
        installments_per_year: perYear,
        cash_price_egp: cashPrice === '' ? undefined : cashPrice,
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
          <div className="inline-flex items-center gap-2 rounded-full border border-[var(--osool-accent-mid)] bg-[var(--osool-accent-soft)] px-3 py-1 text-xs font-semibold uppercase tracking-[0.18em] text-[var(--osool-accent)]">
            <Scale className="h-3.5 w-3.5" />
            {isRTL ? 'تقسيط ولا كاش؟' : 'Installments vs Cash'}
          </div>
          <h1 className="mt-5 text-3xl font-semibold tracking-tight text-[var(--color-text-primary)]">
            {isRTL ? 'هل التقسيط أحسن من الكاش؟' : 'Are installments better than cash?'}
          </h1>
          <p className="mt-2 max-w-2xl text-[var(--color-text-secondary)]">
            {isRTL
              ? 'بنحسب القيمة الحالية الحقيقية لخطة الأقساط بسعر فائدة البنك المركزي — عشان تعرف خطة المطور «الرخيصة» بتساوي كام كاش فعليًا.'
              : "We discount the developer's payment plan at the CBE corridor rate — so you know what that 'cheap' plan is actually worth in cash."}
          </p>

          <div className="mt-8 grid gap-4 rounded-[28px] border border-[var(--color-border)] bg-[var(--color-surface)] p-6 sm:grid-cols-2">
            <label className="block">
              <span className="text-sm font-medium text-[var(--color-text-primary)]">
                {isRTL ? 'السعر الإجمالي بالتقسيط (جنيه)' : 'Total installment price (EGP)'}
              </span>
              <input
                type="number"
                min={100_000}
                value={totalPrice}
                onChange={(e) => setTotalPrice(Number(e.target.value))}
                className="mt-2 w-full rounded-2xl border border-[var(--color-border)] bg-[var(--color-background)] px-4 py-3 text-[var(--color-text-primary)] outline-none focus:border-[var(--osool-accent)]"
              />
            </label>
            <label className="block">
              <span className="text-sm font-medium text-[var(--color-text-primary)]">
                {isRTL ? 'المقدم (جنيه)' : 'Down payment (EGP)'}
              </span>
              <input
                type="number"
                min={1}
                value={downPayment}
                onChange={(e) => setDownPayment(Number(e.target.value))}
                className="mt-2 w-full rounded-2xl border border-[var(--color-border)] bg-[var(--color-background)] px-4 py-3 text-[var(--color-text-primary)] outline-none focus:border-[var(--osool-accent)]"
              />
            </label>
            <label className="block">
              <span className="text-sm font-medium text-[var(--color-text-primary)]">
                {isRTL ? `سنوات التقسيط: ${years}` : `Installment years: ${years}`}
              </span>
              <input
                type="range"
                min={1}
                max={15}
                value={years}
                onChange={(e) => setYears(Number(e.target.value))}
                className="mt-3 w-full accent-[var(--osool-accent)]"
              />
            </label>
            <label className="block">
              <span className="text-sm font-medium text-[var(--color-text-primary)]">
                {isRTL ? 'عدد الأقساط في السنة' : 'Installments per year'}
              </span>
              <select
                value={perYear}
                onChange={(e) => setPerYear(Number(e.target.value))}
                className="mt-2 w-full rounded-2xl border border-[var(--color-border)] bg-[var(--color-background)] px-4 py-3 text-[var(--color-text-primary)] outline-none focus:border-[var(--osool-accent)]"
              >
                <option value={1}>{isRTL ? 'سنوي (١)' : 'Yearly (1)'}</option>
                <option value={2}>{isRTL ? 'نصف سنوي (٢)' : 'Semi-annual (2)'}</option>
                <option value={4}>{isRTL ? 'ربع سنوي (٤)' : 'Quarterly (4)'}</option>
                <option value={12}>{isRTL ? 'شهري (١٢)' : 'Monthly (12)'}</option>
              </select>
            </label>
            <label className="block sm:col-span-2">
              <span className="text-sm font-medium text-[var(--color-text-primary)]">
                {isRTL ? 'سعر الكاش المعروض (اختياري)' : 'Quoted cash price (optional)'}
              </span>
              <input
                type="number"
                min={0}
                value={cashPrice}
                placeholder={isRTL ? 'لو المطور عرض سعر كاش مختلف' : "If the developer quoted a separate cash price"}
                onChange={(e) => setCashPrice(e.target.value === '' ? '' : Number(e.target.value))}
                className="mt-2 w-full rounded-2xl border border-[var(--color-border)] bg-[var(--color-background)] px-4 py-3 text-[var(--color-text-primary)] outline-none focus:border-[var(--osool-accent)]"
              />
            </label>
            <button
              onClick={calculate}
              disabled={loading || totalPrice <= 0 || downPayment <= 0 || downPayment >= totalPrice}
              className="sm:col-span-2 flex items-center justify-center gap-2 rounded-2xl bg-[var(--osool-accent)] py-3.5 text-sm font-semibold text-white transition hover:bg-[var(--osool-accent-dark)] disabled:cursor-not-allowed disabled:opacity-50"
            >
              {loading ? <Loader2 className="h-4 w-4 animate-spin" /> : <Scale className="h-4 w-4" />}
              {isRTL ? 'قارن' : 'Compare'}
            </button>
          </div>

          {error && (
            <div className="mt-4 rounded-2xl border border-red-500/30 bg-red-500/10 px-4 py-3 text-sm text-red-500">
              {error}
            </div>
          )}

          {result && (
            <div className="mt-8 space-y-4">
              <div className="grid gap-4 sm:grid-cols-2">
                <div className="rounded-[24px] border border-[var(--color-border)] bg-[var(--color-surface)] p-5">
                  <p className="text-xs uppercase tracking-wider text-[var(--color-text-muted)]">
                    {isRTL ? 'السعر الاسمي بالتقسيط' : 'Nominal installment price'}
                  </p>
                  <p className="mt-2 text-2xl font-bold text-[var(--color-text-primary)]">
                    {fmt(result.nominal_price_egp, isRTL)} <span className="text-sm font-normal">{isRTL ? 'جنيه' : 'EGP'}</span>
                  </p>
                  <p className="mt-1 text-xs text-[var(--color-text-secondary)]">
                    {result.installments_count} {isRTL ? 'قسط' : 'installments'} × {fmt(result.per_installment_egp, isRTL)}
                  </p>
                </div>
                <div className="rounded-[24px] border border-[var(--osool-accent-mid)] bg-[var(--osool-accent-soft)] p-5">
                  <p className="text-xs uppercase tracking-wider text-[var(--osool-accent)]">
                    {isRTL ? 'القيمة الحقيقية كاش (NPV)' : 'True cash value (NPV)'}
                  </p>
                  <p className="mt-2 text-2xl font-bold text-[var(--color-text-primary)]">
                    {fmt(result.cash_equivalent_npv_egp, isRTL)} <span className="text-sm font-normal">{isRTL ? 'جنيه' : 'EGP'}</span>
                  </p>
                  <p className="mt-1 text-xs text-[var(--color-text-secondary)]">
                    {isRTL
                      ? `أقل ${result.time_value_discount_pct}٪ من السعر الاسمي (بسعر فائدة ${result.cbe_rate_pct}٪)`
                      : `${result.time_value_discount_pct}% below nominal (at ${result.cbe_rate_pct}% CBE rate)`}
                  </p>
                </div>
              </div>

              {result.verdict && (
                <div className="rounded-[24px] border border-[var(--color-border)] bg-[var(--color-surface)] p-5">
                  <h3 className="text-sm font-semibold text-[var(--color-text-primary)]">
                    {isRTL ? 'الحكم' : 'Verdict'}
                  </h3>
                  <p className="mt-2 text-sm text-[var(--color-text-secondary)]">
                    {result.verdict === 'cash'
                      ? isRTL
                        ? `سعر الكاش المعروض (${fmt(result.cash_price_egp!, isRTL)} جنيه) أرخص من القيمة الحقيقية لخطة التقسيط — الكاش هنا صفقة أحسن بفارق ${fmt(Math.abs(result.savings_if_cash_egp!), isRTL)} جنيه.`
                        : `The quoted cash price (${fmt(result.cash_price_egp!, isRTL)} EGP) is below the plan's true value — cash wins by ${fmt(Math.abs(result.savings_if_cash_egp!), isRTL)} EGP.`
                      : isRTL
                        ? `خطة التقسيط قيمتها الحقيقية أقل من سعر الكاش المعروض — كمّل بالتقسيط واستثمر فلوسك في مكان تاني.`
                        : `The installment plan's true value is below the quoted cash price — take the installments and keep your cash working elsewhere.`}
                  </p>
                </div>
              )}

              <p className="text-xs text-[var(--color-text-muted)]">
                {isRTL
                  ? 'الحساب استرشادي بسعر الكوريدور الحالي للبنك المركزي ولا يشمل مصاريف الصيانة أو وديعة الجراج.'
                  : 'Indicative calculation at the current CBE corridor rate; excludes maintenance fees and garage deposits.'}
              </p>
            </div>
          )}
        </div>
      </div>
    </AppShell>
  );
}
