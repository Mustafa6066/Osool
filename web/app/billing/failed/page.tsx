'use client';

import { useRouter } from 'next/navigation';
import { XCircle } from 'lucide-react';
import { useLanguage } from '@/contexts/LanguageContext';

// Paymob redirects here when a payment is declined or cancelled.
export default function BillingFailedPage() {
  const router = useRouter();
  const { direction } = useLanguage();
  const isRTL = direction === 'rtl';

  return (
    <div
      className="flex h-screen items-center justify-center bg-[var(--color-background)] px-6"
      dir={direction}
    >
      <div className="w-full max-w-md rounded-[28px] border border-[var(--color-border)] bg-[var(--color-surface)] p-8 text-center">
        <div className="mx-auto inline-flex h-16 w-16 items-center justify-center rounded-full bg-red-500/15">
          <XCircle className="h-8 w-8 text-red-500" />
        </div>
        <h1 className="mt-6 text-xl font-semibold text-[var(--color-text-primary)]">
          {isRTL ? 'لم تكتمل عملية الدفع' : 'Payment was not completed'}
        </h1>
        <p className="mt-2 text-sm text-[var(--color-text-secondary)]">
          {isRTL
            ? 'لم يتم خصم أي مبلغ. تقدر تحاول مرة أخرى أو تستخدم وسيلة دفع مختلفة.'
            : 'You were not charged. You can try again or use a different payment method.'}
        </p>
        <div className="mt-8 flex gap-3">
          <button
            onClick={() => router.push('/pricing')}
            className="flex-1 rounded-2xl bg-[var(--osool-accent)] py-3 text-sm font-semibold text-white transition hover:bg-[var(--osool-accent-dark)]"
          >
            {isRTL ? 'حاول مرة أخرى' : 'Try again'}
          </button>
          <button
            onClick={() => router.push('/contact')}
            className="flex-1 rounded-2xl border border-[var(--color-border)] py-3 text-sm font-semibold text-[var(--color-text-primary)]"
          >
            {isRTL ? 'الدعم' : 'Support'}
          </button>
        </div>
      </div>
    </div>
  );
}
