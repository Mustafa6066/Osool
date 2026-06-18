'use client';

import { useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { ArrowLeft, ArrowRight, Loader2, ShieldCheck } from 'lucide-react';
import { useLanguage } from '@/contexts/LanguageContext';

// Renders the Paymob payment iframe stored by the pricing page.
// The webhook is the source of truth for payment success; Paymob's
// redirect lands on /billing/success which polls billing status.
export default function CheckoutPayPage() {
  const router = useRouter();
  const { direction } = useLanguage();
  const isRTL = direction === 'rtl';

  const [iframeUrl, setIframeUrl] = useState<string | null>(null);
  const [missing, setMissing] = useState(false);

  useEffect(() => {
    const url = sessionStorage.getItem('osool_checkout_iframe');
    if (url && url.startsWith('https://accept.paymob.com/')) {
      setIframeUrl(url);
    } else {
      setMissing(true);
    }
  }, []);

  const BackIcon = isRTL ? ArrowRight : ArrowLeft;

  return (
    <div className="flex h-screen flex-col bg-[var(--color-background)]" dir={direction}>
      <header className="flex items-center justify-between border-b border-[var(--color-border)] px-4 py-3 sm:px-6">
        <button
          onClick={() => router.push('/pricing')}
          className="inline-flex items-center gap-2 text-sm font-medium text-[var(--color-text-secondary)] transition hover:text-[var(--color-text-primary)]"
        >
          <BackIcon className="h-4 w-4" />
          {isRTL ? 'رجوع للباقات' : 'Back to pricing'}
        </button>
        <div className="inline-flex items-center gap-2 text-xs text-[var(--color-text-muted)]">
          <ShieldCheck className="h-4 w-4 text-[var(--osool-nile)]" />
          {isRTL ? 'دفع آمن عبر Paymob' : 'Secure payment by Paymob'}
        </div>
      </header>

      {missing ? (
        <div className="flex flex-1 flex-col items-center justify-center gap-4 px-6 text-center">
          <p className="text-[var(--color-text-secondary)]">
            {isRTL
              ? 'انتهت جلسة الدفع. ابدأ من صفحة الباقات من جديد.'
              : 'Your payment session expired. Please start again from the pricing page.'}
          </p>
          <button
            onClick={() => router.push('/pricing')}
            className="rounded-2xl bg-[var(--osool-accent)] px-6 py-3 text-sm font-semibold text-white transition hover:bg-[var(--osool-accent-dark)]"
          >
            {isRTL ? 'الذهاب للباقات' : 'Go to pricing'}
          </button>
        </div>
      ) : iframeUrl ? (
        <iframe
          src={iframeUrl}
          title="Paymob secure checkout"
          className="w-full flex-1 border-0"
          allow="payment"
        />
      ) : (
        <div className="flex flex-1 items-center justify-center">
          <Loader2 className="h-8 w-8 animate-spin text-[var(--osool-accent)]" />
        </div>
      )}
    </div>
  );
}
