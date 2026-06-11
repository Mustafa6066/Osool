'use client';

import { Suspense, useEffect } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { Loader2 } from 'lucide-react';

// Existing upgrade CTAs across the app link to /upgrade?source=… —
// this route preserves that contract and lands users on /pricing.
function UpgradeRedirect() {
  const router = useRouter();
  const searchParams = useSearchParams();

  useEffect(() => {
    const source = searchParams.get('source');
    router.replace(source ? `/pricing?source=${encodeURIComponent(source)}` : '/pricing');
  }, [router, searchParams]);

  return (
    <div className="flex h-screen items-center justify-center bg-[var(--color-background)]">
      <Loader2 className="h-8 w-8 animate-spin text-emerald-500" />
    </div>
  );
}

export default function UpgradePage() {
  return (
    <Suspense
      fallback={
        <div className="flex h-screen items-center justify-center bg-[var(--color-background)]">
          <Loader2 className="h-8 w-8 animate-spin text-emerald-500" />
        </div>
      }
    >
      <UpgradeRedirect />
    </Suspense>
  );
}
