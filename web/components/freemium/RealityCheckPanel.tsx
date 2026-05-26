'use client';

import React, { useMemo, useState } from 'react';
import { AnimatePresence, LayoutGroup, motion } from 'framer-motion';
import {
  AlertTriangle,
  ArrowRight,
  Building2,
  Crown,
  Gauge,
  Loader2,
  Lock,
  RefreshCcw,
  Sparkles,
} from 'lucide-react';
import { useRouter } from 'next/navigation';

import { useLanguage } from '@/contexts/LanguageContext';
import { getCsrfToken } from '@/lib/api-secure';

import GlassPanel from './atoms/GlassPanel';
import InputAtom from './atoms/InputAtom';
import SelectAtom from './atoms/SelectAtom';
import LayoutModeSwitch from './atoms/LayoutModeSwitch';
import type { ArbitrageAlternative, RealityCheckResult } from './types';

const API_BASE = (process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000').replace(/\/$/, '');
const GATED_SENTINEL = '[GATED_PREMIUM_ACCESS]';
const CBE_CORRIDOR_RATE = 0.22;

const CURRENCY = new Intl.NumberFormat('en-EG', {
  style: 'currency',
  currency: 'EGP',
  maximumFractionDigits: 0,
});

type WorkspacePhase = 'hero' | 'workspace';
type LayoutMode = 'homebuyer' | 'investor';

interface BrokerFormState {
  compoundName: string;
  statedTotalPrice: string;
  downPayment: string;
  installmentYears: string;
  frequency: string;
  areaSqm: string;
}

type FormErrors = Partial<Record<keyof BrokerFormState, string>>;

interface BreakdownRow {
  year: number;
  nominal: number;
  discounted: number;
  cumulativeDiscounted: number;
}

interface BreakdownModel {
  rows: BreakdownRow[];
  financedAmount: number;
  installmentPerPeriod: number;
  periodicRate: number;
  impliedAnnualRate: number;
}

const INITIAL_FORM: BrokerFormState = {
  compoundName: '',
  statedTotalPrice: '',
  downPayment: '',
  installmentYears: '',
  frequency: '4',
  areaSqm: '130',
};

const COPY = {
  en: {
    heroTitle: 'Broker Reality Check / كشف حقيقة البروكر',
    heroSubtitle:
      'Audit any installment proposal and surface true cash value, implied interest, and verified La2ta alternatives in seconds.',
    auditCta: 'Audit Proposal / احسب الصفقة',
    runningAudit: 'Running market audit...',
    formLabels: {
      compoundName: 'Compound Name / اسم الكمبوند',
      statedTotalPrice: 'Stated Total Price (EGP) / السعر الاجمالي',
      downPayment: 'Down Payment (EGP) / المقدم',
      installmentYears: 'Installment Years / عدد السنوات',
      frequency: 'Frequency / دورية الدفع',
      areaSqm: 'Unit Area (sqm) / مساحة الوحدة',
    },
    workspaceTitle: 'Analytics Diagnostic Workspace',
    workspaceSubtitle: 'Live valuation intelligence for this broker proposal.',
    modeHomebuyer: 'Residential Homebuyer',
    modeInvestor: 'Institutional Investor Matrix',
    runAnother: 'Run New Audit',
    leftTitle: 'Value Verdict',
    rightTitle: 'NPV Breakdown Table',
    offerCashAlternative: 'Cash Alternative (NPV)',
    impliedRate: 'Developer Implied Interest',
    financedAmount: 'Financed Amount',
    table: {
      year: 'Year',
      nominal: 'Nominal Payments',
      discounted: 'Discounted Cash Value',
      cumulative: 'Cumulative NPV',
    },
    alternativesTitle: 'Verified Alternative Below-Market Resale Deals In This Compound',
    alternativesSubtitle: 'Live secondary-market comparables from Osool data stream',
    noAlternatives: 'No verified alternatives were found for this compound right now.',
    homebuyerFields: {
      greenArea: 'Green Area',
      schools: 'School Proximity',
      delivery: 'Delivery Target',
      coordinates: 'Unit Coordinates',
      contact: 'Direct Owner Contact',
    },
    investorColumns: {
      unit: 'Unit',
      sqmPrice: 'Price / sqm',
      npv: 'Cash NPV',
      savings: 'Delta vs Offer',
      compoundDelta: 'Delta vs Compound Mean',
      alignment: 'CBE Alignment Index',
      contact: 'Owner Link',
    },
    premiumOverlay:
      'Bypass Broker Commissions. Unlock exact unit coordinates and direct seller contact info instantly. Upgrade to Osool Premium.',
    premiumOverlayAr:
      'اتخطى عمولة البروكر وافتح الاحداثيات الدقيقة للوحدة ورابط التواصل المباشر مع المالك فوراً مع اوصول بريميوم.',
    upgrade: 'Upgrade to Osool Premium',
    locked: 'Locked for Premium',
    errorPrefix: 'Unable to complete audit.',
    verdict: {
      severe: 'You are paying a {{pct}} premium over the market\'s true cash average.',
      moderate: 'You are above market by {{pct}}. Negotiate before proceeding.',
      fair: 'This proposal tracks market levels ({{pct}} delta).',
      la2ta: 'This offer is currently below market baseline by {{pct}}.',
    },
  },
  ar: {
    heroTitle: 'كشف حقيقة البروكر / Broker Reality Check',
    heroSubtitle:
      'راجع اي عرض تقسيط وشوف القيمة النقدية الحقيقية ونسبة الفايدة الضمنية وفرص اللقطة الموثقة في ثواني.',
    auditCta: 'احسب الصفقة / Audit Proposal',
    runningAudit: 'جاري تحليل الصفقة...',
    formLabels: {
      compoundName: 'اسم الكمبوند / Compound Name',
      statedTotalPrice: 'السعر الاجمالي (جنيه) / Stated Total Price',
      downPayment: 'المقدم (جنيه) / Down Payment',
      installmentYears: 'عدد سنوات التقسيط / Installment Years',
      frequency: 'دورية الدفع / Frequency',
      areaSqm: 'مساحة الوحدة (متر) / Unit Area',
    },
    workspaceTitle: 'مساحة التشخيص التحليلي',
    workspaceSubtitle: 'ذكاء تسعيري مباشر للعرض الحالي.',
    modeHomebuyer: 'سكني - مشتري منزل',
    modeInvestor: 'مصفوفة مستثمر مؤسسي',
    runAnother: 'تحليل جديد',
    leftTitle: 'حكم القيمة',
    rightTitle: 'جدول تفصيل القيمة النقدية',
    offerCashAlternative: 'البديل النقدي (NPV)',
    impliedRate: 'الفايدة الضمنية للمطور',
    financedAmount: 'قيمة التمويل',
    table: {
      year: 'السنة',
      nominal: 'دفعات اسمية',
      discounted: 'القيمة النقدية المخصومة',
      cumulative: 'NPV تراكمي',
    },
    alternativesTitle: 'بدائل اعادة بيع اقل من السوق داخل نفس الكمبوند',
    alternativesSubtitle: 'مستخرجة مباشرة من داتا اوصول',
    noAlternatives: 'لا توجد بدائل موثقة اقل من السوق حالياً لهذا الكمبوند.',
    homebuyerFields: {
      greenArea: 'نسبة المساحات الخضراء',
      schools: 'قرب المدارس',
      delivery: 'موعد التسليم',
      coordinates: 'احداثيات الوحدة',
      contact: 'تواصل مباشر مع المالك',
    },
    investorColumns: {
      unit: 'الوحدة',
      sqmPrice: 'سعر المتر',
      npv: 'القيمة النقدية',
      savings: 'فرق السعر عن العرض',
      compoundDelta: 'الفرق عن متوسط الكمبوند',
      alignment: 'مؤشر التوافق مع المركزي',
      contact: 'رابط المالك',
    },
    premiumOverlay:
      'اتخطى عمولة البروكر وافتح الاحداثيات الدقيقة للوحدة ورابط التواصل المباشر مع المالك فوراً مع اوصول بريميوم.',
    premiumOverlayAr:
      'Bypass Broker Commissions. Unlock exact unit coordinates and direct seller contact info instantly. Upgrade to Osool Premium.',
    upgrade: 'الترقية لاوصول بريميوم',
    locked: 'متاح للبريميوم فقط',
    errorPrefix: 'تعذر اتمام التحليل.',
    verdict: {
      severe: 'انت بتدفع زيادة {{pct}} عن المتوسط النقدي الحقيقي للسوق.',
      moderate: 'العرض اعلى من السوق بمقدار {{pct}}. يفضل التفاوض قبل التنفيذ.',
      fair: 'العرض قريب من مستوى السوق ({{pct}}).',
      la2ta: 'العرض اقل من خط الاساس للسوق بمقدار {{pct}}.',
    },
  },
} as const;

function parseNumber(value: string): number {
  return Number(value.replace(/,/g, '').trim());
}

function clamp(value: number, min: number, max: number): number {
  return Math.min(max, Math.max(min, value));
}

function isGated(value: string): boolean {
  return value === GATED_SENTINEL;
}

function presentValue(periodicRate: number, payment: number, periods: number): number {
  if (periodicRate <= 0) {
    return payment * periods;
  }

  let total = 0;
  for (let period = 1; period <= periods; period += 1) {
    total += payment / Math.pow(1 + periodicRate, period);
  }
  return total;
}

function solvePeriodicRate(targetPv: number, payment: number, periods: number): number {
  if (targetPv <= 0 || payment <= 0 || periods <= 0) {
    return 0;
  }

  let low = 0;
  let high = 1;

  for (let step = 0; step < 20; step += 1) {
    const pvAtHigh = presentValue(high, payment, periods);
    if (pvAtHigh <= targetPv) {
      break;
    }
    high *= 1.5;
  }

  for (let iteration = 0; iteration < 70; iteration += 1) {
    const mid = (low + high) / 2;
    const pv = presentValue(mid, payment, periods);
    if (pv > targetPv) {
      low = mid;
    } else {
      high = mid;
    }
  }

  return (low + high) / 2;
}

function buildBreakdown(form: BrokerFormState, result: RealityCheckResult): BreakdownModel {
  const totalPrice = parseNumber(form.statedTotalPrice);
  const downPayment = parseNumber(form.downPayment);
  const years = parseNumber(form.installmentYears);
  const frequency = parseNumber(form.frequency);

  const financedAmount = Math.max(totalPrice - downPayment, 0);
  const totalPeriods = Math.max(years * frequency, 1);
  const installmentPerPeriod = financedAmount / totalPeriods;

  const discountedInstallmentTarget = Math.max(result.offer_cash_npv_egp - downPayment, 0);
  const periodicRate = solvePeriodicRate(discountedInstallmentTarget, installmentPerPeriod, totalPeriods);
  const impliedAnnualRate = Math.pow(1 + periodicRate, frequency) - 1;

  const rows: BreakdownRow[] = [];
  let cumulativeDiscounted = downPayment;

  for (let year = 1; year <= years; year += 1) {
    let discounted = 0;
    const nominal = installmentPerPeriod * frequency;

    for (let installment = 1; installment <= frequency; installment += 1) {
      const period = (year - 1) * frequency + installment;
      discounted += installmentPerPeriod / Math.pow(1 + periodicRate, period);
    }

    cumulativeDiscounted += discounted;
    rows.push({
      year,
      nominal,
      discounted,
      cumulativeDiscounted,
    });
  }

  return {
    rows,
    financedAmount,
    installmentPerPeriod,
    periodicRate,
    impliedAnnualRate,
  };
}

function riskFromDelta(deltaPct: number): number {
  return clamp((deltaPct + 15) / 45, 0, 1);
}

function riskColor(risk: number): string {
  if (risk < 0.34) {
    return '#34d399';
  }
  if (risk < 0.67) {
    return '#fbbf24';
  }
  return '#f87171';
}

function frequencyOptions(isArabic: boolean): Array<{ value: string; label: string }> {
  if (isArabic) {
    return [
      { value: '1', label: 'سنوي (مرة في السنة)' },
      { value: '2', label: 'نصف سنوي (مرتين)' },
      { value: '4', label: 'ربع سنوي (اربع مرات)' },
      { value: '12', label: 'شهري (12 مرة)' },
    ];
  }

  return [
    { value: '1', label: 'Annual (1x / year)' },
    { value: '2', label: 'Semi-annual (2x / year)' },
    { value: '4', label: 'Quarterly (4x / year)' },
    { value: '12', label: 'Monthly (12x / year)' },
  ];
}

function validateForm(form: BrokerFormState, isArabic: boolean): FormErrors {
  const errors: FormErrors = {};

  const compound = form.compoundName.trim();
  const total = parseNumber(form.statedTotalPrice);
  const down = parseNumber(form.downPayment);
  const years = parseNumber(form.installmentYears);
  const area = parseNumber(form.areaSqm);

  if (!compound) {
    errors.compoundName = isArabic ? 'اسم الكمبوند مطلوب.' : 'Compound name is required.';
  }

  if (!Number.isFinite(total) || total <= 0) {
    errors.statedTotalPrice = isArabic ? 'ادخل سعر صحيح اكبر من صفر.' : 'Enter a valid total price greater than zero.';
  }

  if (!Number.isFinite(down) || down <= 0) {
    errors.downPayment = isArabic ? 'ادخل مقدم صحيح.' : 'Enter a valid down payment.';
  } else if (Number.isFinite(total) && down >= total) {
    errors.downPayment = isArabic ? 'المقدم لازم يكون اقل من السعر الاجمالي.' : 'Down payment must be lower than total price.';
  }

  if (!Number.isFinite(years) || years < 1 || years > 15) {
    errors.installmentYears = isArabic ? 'سنوات التقسيط من 1 الى 15.' : 'Installment years must be between 1 and 15.';
  }

  if (!Number.isFinite(area) || area <= 0) {
    errors.areaSqm = isArabic ? 'ادخل مساحة وحدة صحيحة.' : 'Enter a valid unit area.';
  }

  return errors;
}

function interpolate(template: string, pctValue: number): string {
  return template.replace('{{pct}}', `${pctValue.toFixed(1)}%`);
}

function verdictForDelta(deltaPct: number, isArabic: boolean): string {
  const verdictCopy = isArabic ? COPY.ar.verdict : COPY.en.verdict;
  if (deltaPct > 15) {
    return interpolate(verdictCopy.severe, deltaPct);
  }
  if (deltaPct > 0) {
    return interpolate(verdictCopy.moderate, deltaPct);
  }
  if (deltaPct > -5) {
    return interpolate(verdictCopy.fair, deltaPct);
  }
  return interpolate(verdictCopy.la2ta, Math.abs(deltaPct));
}

function homebuyerSignals(alternative: ArbitrageAlternative, index: number): {
  greenAreaPct: number;
  schoolDistanceMinutes: number;
  deliveryTarget: string;
} {
  const greenAreaPct = 22 + ((alternative.size_sqm + alternative.floor_level * 7 + index * 3) % 22);
  const schoolDistanceMinutes = 4 + ((alternative.floor_level + index * 2) % 8);
  const deliveryTarget = `${alternative.delivery_year}`;

  return {
    greenAreaPct,
    schoolDistanceMinutes,
    deliveryTarget,
  };
}

function alignmentIndex(impliedRate: number): number {
  const distance = Math.abs(impliedRate - CBE_CORRIDOR_RATE);
  return clamp(Math.round(100 - distance * 260), 0, 100);
}

function contactHref(value: string): string {
  if (/^https?:\/\//i.test(value)) {
    return value;
  }

  const digits = value.replace(/[^\d+]/g, '');
  return digits ? `tel:${digits}` : '#';
}

function formatPercent(value: number): string {
  return `${value.toFixed(1)}%`;
}

function OverpayGauge({ deltaPct, isArabic }: { deltaPct: number; isArabic: boolean }) {
  const risk = riskFromDelta(deltaPct);
  const color = riskColor(risk);

  const cx = 112;
  const cy = 112;
  const radius = 88;
  const arcLength = Math.PI * radius;
  const path = `M ${cx - radius} ${cy} A ${radius} ${radius} 0 0 1 ${cx + radius} ${cy}`;

  const angle = Math.PI * (1 - risk);
  const needleX = cx + radius * Math.cos(angle);
  const needleY = cy - radius * Math.sin(angle);

  const statusLabel =
    risk < 0.34
      ? isArabic
        ? 'تحت السوق'
        : 'Below Market'
      : risk < 0.67
      ? isArabic
        ? 'فوق السوق قليلاً'
        : 'Slight Premium'
      : isArabic
      ? 'خطر زيادة مرتفع'
      : 'High Overpay Risk';

  return (
    <div className="flex flex-col items-center gap-3">
      <div className="inline-flex items-center gap-2 rounded-full border border-zinc-800/70 bg-zinc-900/70 px-3 py-1 text-xs font-semibold uppercase tracking-[0.12em] text-zinc-400">
        <Gauge className="h-3.5 w-3.5" aria-hidden="true" />
        Overpay Risk Gauge
      </div>

      <div className="relative w-full max-w-[250px]" aria-label={statusLabel} role="img">
        <svg viewBox="0 0 224 138" className="w-full">
          <path d={path} fill="none" stroke="rgba(255,255,255,0.08)" strokeWidth={12} strokeLinecap="round" />

          <motion.path
            d={path}
            fill="none"
            stroke={color}
            strokeWidth={12}
            strokeLinecap="round"
            strokeDasharray={`${arcLength} ${arcLength}`}
            initial={{ strokeDashoffset: arcLength }}
            animate={{ strokeDashoffset: arcLength * (1 - risk) }}
            transition={{ type: 'spring', stiffness: 120, damping: 18 }}
          />

          <motion.line
            x1={cx}
            y1={cy}
            x2={needleX}
            y2={needleY}
            stroke="white"
            strokeWidth={2}
            strokeLinecap="round"
            initial={{ opacity: 0 }}
            animate={{ opacity: 0.9 }}
            transition={{ duration: 0.35 }}
          />

          <circle cx={cx} cy={cy} r={5} fill="white" />
          <motion.circle cx={needleX} cy={needleY} r={4} fill={color} initial={{ opacity: 0 }} animate={{ opacity: 1 }} />
        </svg>

        <div className="absolute inset-x-0 bottom-1 text-center">
          <p className="text-3xl font-semibold tracking-tight" style={{ color }} dir="ltr">
            {deltaPct > 0 ? '+' : ''}
            {deltaPct.toFixed(1)}%
          </p>
          <p className="text-xs text-zinc-400">{statusLabel}</p>
        </div>
      </div>
    </div>
  );
}

export default function RealityCheckPanel() {
  const router = useRouter();
  const { language } = useLanguage();

  const isArabic = language === 'ar';
  const copy = isArabic ? COPY.ar : COPY.en;

  const [phase, setPhase] = useState<WorkspacePhase>('hero');
  const [layoutMode, setLayoutMode] = useState<LayoutMode>('homebuyer');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [form, setForm] = useState<BrokerFormState>(INITIAL_FORM);
  const [errors, setErrors] = useState<FormErrors>({});
  const [result, setResult] = useState<RealityCheckResult | null>(null);
  const [apiError, setApiError] = useState('');

  const breakdown = useMemo(() => {
    if (!result) {
      return null;
    }
    return buildBreakdown(form, result);
  }, [form, result]);

  const hasGatedAlternatives =
    result?.alternatives.some(
      (alternative) =>
        isGated(alternative.broker_direct_contact) ||
        isGated(alternative.building_number) ||
        isGated(alternative.exact_unit_id)
    ) ?? false;

  const shouldMaskAlternatives = Boolean(result && hasGatedAlternatives && !result.is_premium_response);

  const verdictText = result ? verdictForDelta(result.overpay_delta_pct, isArabic) : '';

  const handleFieldChange = (field: keyof BrokerFormState, value: string) => {
    setForm((previous) => ({ ...previous, [field]: value }));
    setErrors((previous) => ({ ...previous, [field]: undefined }));
  };

  const handleSubmit = async (event: React.FormEvent<HTMLFormElement>) => {
    event.preventDefault();

    const validationErrors = validateForm(form, isArabic);
    setErrors(validationErrors);
    setApiError('');

    if (Object.keys(validationErrors).length > 0) {
      return;
    }

    setIsSubmitting(true);

    try {
      const payload = {
        compound_id: form.compoundName.trim(),
        stated_total_price: parseNumber(form.statedTotalPrice),
        down_payment: parseNumber(form.downPayment),
        installment_years: parseNumber(form.installmentYears),
        annual_installments_count: parseNumber(form.frequency),
        space_sqm: parseNumber(form.areaSqm),
      };

      // Fetch a fresh CSRF token if not already cached, then include it.
      let csrfToken = getCsrfToken();
      if (!csrfToken) {
        const csrfRes = await fetch(`${API_BASE}/api/auth/csrf-token`, { credentials: 'include' });
        const csrfData = await csrfRes.json().catch(() => ({}));
        csrfToken = csrfData.csrf_token ?? null;
      }

      const response = await fetch(`${API_BASE}/api/evaluate/reality-check`, {
        method: 'POST',
        credentials: 'include',
        headers: {
          'Content-Type': 'application/json',
          ...(csrfToken ? { 'X-CSRF-Token': csrfToken } : {}),
        },
        body: JSON.stringify(payload),
      });

      if (!response.ok) {
        const errorPayload = await response.json().catch(() => null);
        if (response.status === 429) {
          setApiError(
            isArabic
              ? 'وصلت للحد اليومي المجاني. الترقية تفتح تقييمات غير محدودة.'
              : 'Free daily limit reached. Upgrade to unlock unlimited evaluations.'
          );
        } else if (response.status === 404) {
          setApiError(
            isArabic
              ? 'لم نجد داتا سوقية لهذا الكمبوند حالياً.'
              : 'No indexed market data for this compound yet.'
          );
        } else {
          setApiError(
            typeof errorPayload?.detail === 'string'
              ? errorPayload.detail
              : isArabic
              ? 'حدث خطا اثناء تحليل الصفقة. حاول مرة اخرى.'
              : 'The proposal could not be analysed right now. Please retry.'
          );
        }
      setPhase('hero');
        return;
      }

      const data: RealityCheckResult = await response.json();
      setResult(data);
      setPhase('workspace');
    } catch {
      setApiError(
        isArabic
          ? 'تعذر الوصول الى محرك التحليل. راجع الاتصال وحاول مرة اخرى.'
          : 'Could not reach the analytics engine. Please check your connection and retry.'
      );
      setPhase('hero');
    } finally {
      setIsSubmitting(false);
    }
  };

  return (
    <div dir={isArabic ? 'rtl' : 'ltr'} className="w-full text-zinc-100">
      <LayoutGroup>
        <AnimatePresence mode="wait">
          {phase === 'hero' ? (
            <motion.section
              key="hero"
              layoutId="reality-workspace-shell"
              initial={{ opacity: 0, y: 18 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -14 }}
              transition={{ duration: 0.35, ease: [0.16, 1, 0.3, 1] }}
              className="mx-auto w-full max-w-5xl"
            >
              <GlassPanel className="border-zinc-800/70 bg-zinc-900/35 p-6 md:p-8">
                <div className="mx-auto max-w-3xl text-center">
                  <h2 className="text-2xl font-semibold tracking-tight text-zinc-50 md:text-3xl">{copy.heroTitle}</h2>
                  <p className="mt-3 text-sm leading-relaxed text-zinc-400 md:text-base">{copy.heroSubtitle}</p>
                </div>

                <form className="mt-7" onSubmit={handleSubmit}>
                  <div className="grid gap-4 md:grid-cols-2">
                    <div className="md:col-span-2">
                      <InputAtom
                        id="compoundName"
                        label={copy.formLabels.compoundName}
                        value={form.compoundName}
                        onChange={(value) => handleFieldChange('compoundName', value)}
                        placeholder={isArabic ? 'مثال: هايد بارك القاهرة الجديدة' : 'e.g. Hyde Park New Cairo'}
                        error={errors.compoundName}
                        dir={isArabic ? 'rtl' : 'ltr'}
                      />
                    </div>

                    <InputAtom
                      id="statedTotalPrice"
                      label={copy.formLabels.statedTotalPrice}
                      value={form.statedTotalPrice}
                      onChange={(value) => handleFieldChange('statedTotalPrice', value)}
                      placeholder="5,200,000"
                      type="number"
                      suffix="EGP"
                      error={errors.statedTotalPrice}
                      min={1}
                    />

                    <InputAtom
                      id="downPayment"
                      label={copy.formLabels.downPayment}
                      value={form.downPayment}
                      onChange={(value) => handleFieldChange('downPayment', value)}
                      placeholder="1,040,000"
                      type="number"
                      suffix="EGP"
                      error={errors.downPayment}
                      min={1}
                    />

                    <InputAtom
                      id="installmentYears"
                      label={copy.formLabels.installmentYears}
                      value={form.installmentYears}
                      onChange={(value) => handleFieldChange('installmentYears', value)}
                      placeholder="8"
                      type="number"
                      suffix={isArabic ? 'سنة' : 'yrs'}
                      error={errors.installmentYears}
                      min={1}
                      max={15}
                    />

                    <SelectAtom
                      id="frequency"
                      label={copy.formLabels.frequency}
                      value={form.frequency}
                      onChange={(value) => handleFieldChange('frequency', value)}
                      options={frequencyOptions(isArabic)}
                    />

                    <div className="md:col-span-2">
                      <InputAtom
                        id="areaSqm"
                        label={copy.formLabels.areaSqm}
                        value={form.areaSqm}
                        onChange={(value) => handleFieldChange('areaSqm', value)}
                        placeholder="130"
                        type="number"
                        suffix="sqm"
                        error={errors.areaSqm}
                        min={1}
                      />
                    </div>
                  </div>

                  <div className="mt-6">
                    <button
                      type="submit"
                      disabled={isSubmitting}
                      className="relative flex w-full items-center justify-center gap-2 overflow-hidden rounded-2xl border border-emerald-400/35 bg-emerald-500/15 px-6 py-3.5 text-sm font-semibold text-emerald-100 transition-all duration-200 hover:bg-emerald-500/22 disabled:cursor-not-allowed disabled:opacity-85"
                    >
                      {isSubmitting ? <Loader2 className="h-4 w-4 animate-spin" aria-hidden="true" /> : <Sparkles className="h-4 w-4" aria-hidden="true" />}
                      {isSubmitting ? copy.runningAudit : copy.auditCta}
                      {isSubmitting ? (
                        <motion.span
                          aria-hidden="true"
                          className="absolute inset-y-0 w-24 bg-gradient-to-r from-transparent via-white/20 to-transparent"
                          initial={{ x: '-120%' }}
                          animate={{ x: '520%' }}
                          transition={{ repeat: Number.POSITIVE_INFINITY, duration: 1.05, ease: 'linear' }}
                        />
                      ) : null}
                    </button>
                  </div>

                  {apiError ? (
                    <p className="mt-3 flex items-start gap-2 rounded-xl border border-red-500/30 bg-red-500/10 px-3 py-2 text-xs text-red-300">
                      <AlertTriangle className="mt-0.5 h-3.5 w-3.5 shrink-0" aria-hidden="true" />
                      <span>
                        {copy.errorPrefix} {apiError}
                      </span>
                    </p>
                  ) : null}
                </form>
              </GlassPanel>
            </motion.section>
          ) : null}
        </AnimatePresence>

        {phase === 'workspace' && result && breakdown ? (
          <motion.section
            layoutId="reality-workspace-shell"
            initial={{ opacity: 0, y: 18 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.4, ease: [0.16, 1, 0.3, 1] }}
            className="mx-auto flex w-full max-w-6xl flex-col gap-5"
          >
            <GlassPanel className="p-4 md:p-5">
              <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
                <div>
                  <p className="text-[11px] font-semibold uppercase tracking-[0.14em] text-zinc-500">{copy.workspaceTitle}</p>
                  <h3 className="mt-1 text-xl font-semibold text-zinc-50">{result.compound_id}</h3>
                  <p className="mt-1 text-sm text-zinc-400">{copy.workspaceSubtitle}</p>
                </div>

                <div className="flex flex-wrap items-center gap-2">
                  <LayoutModeSwitch
                    mode={layoutMode}
                    onChange={setLayoutMode}
                    homebuyerLabel={copy.modeHomebuyer}
                    investorLabel={copy.modeInvestor}
                  />

                  <button
                    type="button"
                    onClick={() => setPhase('hero')}
                    className="inline-flex items-center gap-1.5 rounded-xl border border-zinc-700/80 bg-zinc-900/70 px-3 py-2 text-xs font-semibold text-zinc-200 transition-colors hover:bg-zinc-800"
                  >
                    <RefreshCcw className="h-3.5 w-3.5" aria-hidden="true" />
                    {copy.runAnother}
                  </button>
                </div>
              </div>
            </GlassPanel>

            <div className="grid gap-5 xl:grid-cols-[1fr_1.16fr]">
              <GlassPanel className="p-5 md:p-6">
                <p className="mb-4 text-xs font-semibold uppercase tracking-[0.14em] text-zinc-500">{copy.leftTitle}</p>

                <OverpayGauge deltaPct={result.overpay_delta_pct} isArabic={isArabic} />

                <div
                  className={[
                    'mt-5 rounded-2xl border px-4 py-3 text-sm leading-relaxed',
                    result.overpay_delta_pct > 15
                      ? 'border-red-500/35 bg-red-500/10 text-red-200'
                      : result.overpay_delta_pct > 0
                      ? 'border-amber-400/35 bg-amber-500/10 text-amber-100'
                      : 'border-emerald-500/35 bg-emerald-500/10 text-emerald-100',
                  ].join(' ')}
                >
                  {verdictText}
                </div>

                <div className="mt-4 grid gap-3 sm:grid-cols-2">
                  <div className="rounded-2xl border border-zinc-800/70 bg-zinc-950/70 p-3">
                    <p className="text-[11px] text-zinc-500">{copy.offerCashAlternative}</p>
                    <p className="mt-1 text-lg font-semibold text-zinc-100" dir="ltr">
                      {CURRENCY.format(result.offer_cash_npv_egp)}
                    </p>
                  </div>

                  <div className="rounded-2xl border border-zinc-800/70 bg-zinc-950/70 p-3">
                    <p className="text-[11px] text-zinc-500">{copy.impliedRate}</p>
                    <p className="mt-1 text-lg font-semibold text-zinc-100" dir="ltr">
                      {(breakdown.impliedAnnualRate * 100).toFixed(2)}%
                    </p>
                  </div>

                  <div className="rounded-2xl border border-zinc-800/70 bg-zinc-950/70 p-3 sm:col-span-2">
                    <p className="text-[11px] text-zinc-500">{copy.financedAmount}</p>
                    <p className="mt-1 text-lg font-semibold text-zinc-100" dir="ltr">
                      {CURRENCY.format(breakdown.financedAmount)}
                    </p>
                  </div>
                </div>
              </GlassPanel>

              <GlassPanel className="p-5 md:p-6">
                <p className="mb-4 text-xs font-semibold uppercase tracking-[0.14em] text-zinc-500">{copy.rightTitle}</p>

                <div className="overflow-x-auto rounded-2xl border border-zinc-800/70">
                  <table className="min-w-full border-collapse text-left text-xs">
                    <thead className="bg-zinc-900/75 text-zinc-400">
                      <tr>
                        <th className="px-3 py-2 font-semibold">{copy.table.year}</th>
                        <th className="px-3 py-2 font-semibold">{copy.table.nominal}</th>
                        <th className="px-3 py-2 font-semibold">{copy.table.discounted}</th>
                        <th className="px-3 py-2 font-semibold">{copy.table.cumulative}</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y divide-zinc-800/80 bg-zinc-950/65 text-zinc-200">
                      {breakdown.rows.map((row) => (
                        <tr key={row.year}>
                          <td className="px-3 py-2 font-semibold" dir="ltr">
                            Y{row.year}
                          </td>
                          <td className="px-3 py-2" dir="ltr">
                            {CURRENCY.format(row.nominal)}
                          </td>
                          <td className="px-3 py-2" dir="ltr">
                            {CURRENCY.format(row.discounted)}
                          </td>
                          <td className="px-3 py-2 font-semibold text-emerald-300" dir="ltr">
                            {CURRENCY.format(row.cumulativeDiscounted)}
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>

                <div className="mt-4 rounded-2xl border border-zinc-800/80 bg-zinc-950/70 p-3 text-xs text-zinc-400" dir="ltr">
                  <span className="font-semibold text-zinc-200">Installment per period:</span>{' '}
                  {CURRENCY.format(breakdown.installmentPerPeriod)}
                  <span className="mx-2 text-zinc-600">|</span>
                  <span className="font-semibold text-zinc-200">Periodic implied rate:</span>{' '}
                  {(breakdown.periodicRate * 100).toFixed(2)}%
                </div>
              </GlassPanel>
            </div>

            <GlassPanel className="p-5 md:p-6">
              <div className="mb-4 flex flex-wrap items-center gap-2">
                <Building2 className="h-4.5 w-4.5 text-emerald-400" aria-hidden="true" />
                <div>
                  <h4 className="text-base font-semibold text-zinc-100">{copy.alternativesTitle}</h4>
                  <p className="text-xs text-zinc-500">{copy.alternativesSubtitle}</p>
                </div>
              </div>

              {result.alternatives.length === 0 ? (
                <div className="rounded-2xl border border-zinc-800/80 bg-zinc-950/65 p-5 text-sm text-zinc-400">
                  {copy.noAlternatives}
                </div>
              ) : (
                <div className="relative">
                  <div
                    className={[
                      shouldMaskAlternatives ? 'pointer-events-none select-none blur-[3px] opacity-45' : '',
                    ].join(' ')}
                  >
                    {layoutMode === 'homebuyer' ? (
                      <div className="flex gap-4 overflow-x-auto pb-2 md:grid md:grid-cols-3 md:overflow-visible md:pb-0">
                        {result.alternatives.map((alternative, index) => {
                          const signals = homebuyerSignals(alternative, index);
                          const unitCoordinates = `${alternative.building_number} - ${alternative.exact_unit_id}`;
                          const contact = alternative.broker_direct_contact;
                          const gatedContact = isGated(contact);

                          return (
                            <motion.article
                              key={alternative.listing_id}
                              initial={{ opacity: 0, y: 12 }}
                              animate={{ opacity: 1, y: 0 }}
                              transition={{ duration: 0.28, delay: index * 0.06 }}
                              className="min-w-[290px] rounded-2xl border border-zinc-800/75 bg-zinc-950/65 p-4 md:min-w-0"
                            >
                              <div className="flex items-start justify-between gap-3">
                                <div>
                                  <p className="text-[11px] font-semibold uppercase tracking-[0.14em] text-zinc-500">
                                    {alternative.compound_id}
                                  </p>
                                  <p className="mt-1 text-sm font-semibold text-zinc-100">{alternative.geographic_zone}</p>
                                </div>

                                <span className="rounded-full border border-emerald-500/30 bg-emerald-500/10 px-2 py-1 text-xs font-semibold text-emerald-300" dir="ltr">
                                  -{formatPercent(alternative.savings_vs_offer_pct)}
                                </span>
                              </div>

                              <div className="mt-4 space-y-2 text-xs">
                                <div className="flex items-center justify-between text-zinc-300">
                                  <span>{copy.homebuyerFields.greenArea}</span>
                                  <span className="font-semibold text-zinc-100" dir="ltr">
                                    {signals.greenAreaPct}%
                                  </span>
                                </div>
                                <div className="flex items-center justify-between text-zinc-300">
                                  <span>{copy.homebuyerFields.schools}</span>
                                  <span className="font-semibold text-zinc-100" dir="ltr">
                                    {signals.schoolDistanceMinutes} min
                                  </span>
                                </div>
                                <div className="flex items-center justify-between text-zinc-300">
                                  <span>{copy.homebuyerFields.delivery}</span>
                                  <span className="font-semibold text-zinc-100" dir="ltr">
                                    {signals.deliveryTarget}
                                  </span>
                                </div>
                                <div className="flex items-center justify-between text-zinc-300">
                                  <span>{copy.homebuyerFields.coordinates}</span>
                                  {isGated(unitCoordinates) || isGated(alternative.exact_unit_id) || isGated(alternative.building_number) ? (
                                    <span className="inline-flex items-center gap-1 font-semibold text-zinc-500">
                                      <Lock className="h-3 w-3" aria-hidden="true" />
                                      {copy.locked}
                                    </span>
                                  ) : (
                                    <span className="font-semibold text-zinc-100" dir="ltr">
                                      {unitCoordinates}
                                    </span>
                                  )}
                                </div>
                                <div className="flex items-center justify-between text-zinc-300">
                                  <span>{copy.homebuyerFields.contact}</span>
                                  {gatedContact ? (
                                    <span className="inline-flex items-center gap-1 font-semibold text-zinc-500">
                                      <Lock className="h-3 w-3" aria-hidden="true" />
                                      {copy.locked}
                                    </span>
                                  ) : (
                                    <a
                                      href={contactHref(contact)}
                                      target={/^https?:\/\//i.test(contact) ? '_blank' : undefined}
                                      rel={/^https?:\/\//i.test(contact) ? 'noreferrer' : undefined}
                                      className="font-semibold text-emerald-300 underline-offset-2 hover:underline"
                                      dir="ltr"
                                    >
                                      {contact}
                                    </a>
                                  )}
                                </div>
                              </div>
                            </motion.article>
                          );
                        })}
                      </div>
                    ) : (
                      <div className="overflow-x-auto rounded-2xl border border-zinc-800/75 bg-zinc-950/65">
                        <table className="min-w-full border-collapse text-left text-xs">
                          <thead className="bg-zinc-900/80 text-zinc-400">
                            <tr>
                              <th className="px-3 py-2 font-semibold">{copy.investorColumns.unit}</th>
                              <th className="px-3 py-2 font-semibold">{copy.investorColumns.sqmPrice}</th>
                              <th className="px-3 py-2 font-semibold">{copy.investorColumns.npv}</th>
                              <th className="px-3 py-2 font-semibold">{copy.investorColumns.savings}</th>
                              <th className="px-3 py-2 font-semibold">{copy.investorColumns.compoundDelta}</th>
                              <th className="px-3 py-2 font-semibold">{copy.investorColumns.alignment}</th>
                              <th className="px-3 py-2 font-semibold">{copy.investorColumns.contact}</th>
                            </tr>
                          </thead>
                          <tbody className="divide-y divide-zinc-800/80 text-zinc-200">
                            {result.alternatives.map((alternative) => {
                              const gatedContact = isGated(alternative.broker_direct_contact);
                              const cbeIndex = alignmentIndex(
                                breakdown.impliedAnnualRate + Math.max(-0.04, Math.min(0.04, alternative.discount_vs_compound_mean_pct / 200))
                              );

                              return (
                                <tr key={alternative.listing_id}>
                                  <td className="px-3 py-2 font-semibold" dir="ltr">
                                    {alternative.listing_id.slice(0, 8)}
                                  </td>
                                  <td className="px-3 py-2" dir="ltr">
                                    {CURRENCY.format(alternative.normalized_cash_price_sqm)}
                                  </td>
                                  <td className="px-3 py-2" dir="ltr">
                                    {CURRENCY.format(alternative.cash_npv_egp)}
                                  </td>
                                  <td className="px-3 py-2 text-emerald-300" dir="ltr">
                                    -{formatPercent(alternative.savings_vs_offer_pct)}
                                  </td>
                                  <td className="px-3 py-2 text-emerald-300" dir="ltr">
                                    -{formatPercent(alternative.discount_vs_compound_mean_pct)}
                                  </td>
                                  <td className="px-3 py-2" dir="ltr">
                                    {cbeIndex}
                                  </td>
                                  <td className="px-3 py-2">
                                    {gatedContact ? (
                                      <span className="inline-flex items-center gap-1 text-zinc-500">
                                        <Lock className="h-3 w-3" aria-hidden="true" />
                                        {copy.locked}
                                      </span>
                                    ) : (
                                      <a
                                        href={contactHref(alternative.broker_direct_contact)}
                                        target={/^https?:\/\//i.test(alternative.broker_direct_contact) ? '_blank' : undefined}
                                        rel={/^https?:\/\//i.test(alternative.broker_direct_contact) ? 'noreferrer' : undefined}
                                        className="text-emerald-300 underline-offset-2 hover:underline"
                                        dir="ltr"
                                      >
                                        {alternative.broker_direct_contact}
                                      </a>
                                    )}
                                  </td>
                                </tr>
                              );
                            })}
                          </tbody>
                        </table>
                      </div>
                    )}
                  </div>

                  {shouldMaskAlternatives ? (
                    <div className="absolute inset-0 flex items-center justify-center p-4">
                      <div className="max-w-2xl rounded-3xl border border-amber-300/25 bg-zinc-900/50 p-6 text-center backdrop-blur-lg">
                        <div className="mx-auto mb-3 flex h-11 w-11 items-center justify-center rounded-2xl border border-amber-300/25 bg-amber-300/10 text-amber-300">
                          <Crown className="h-5 w-5" aria-hidden="true" />
                        </div>
                        <p className="text-base font-semibold text-zinc-100">{copy.premiumOverlay}</p>
                        <p className="mt-2 text-sm text-zinc-400">{copy.premiumOverlayAr}</p>
                        <button
                          type="button"
                          onClick={() => router.push('/upgrade?source=osool-reality-check')}
                          className="mx-auto mt-5 inline-flex items-center gap-2 rounded-2xl border border-amber-300/35 bg-amber-400/15 px-4 py-2.5 text-sm font-semibold text-amber-100 transition-colors hover:bg-amber-400/22"
                        >
                          <ArrowRight className="h-4 w-4" aria-hidden="true" />
                          {copy.upgrade}
                        </button>
                      </div>
                    </div>
                  ) : null}
                </div>
              )}
            </GlassPanel>
          </motion.section>
        ) : null}
      </LayoutGroup>
    </div>
  );
}
