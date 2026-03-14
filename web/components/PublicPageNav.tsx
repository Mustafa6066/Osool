'use client';

import SmartNav from '@/components/SmartNav';

export default function PublicPageNav({ children }: { children: React.ReactNode }) {
  return <SmartNav>{children}</SmartNav>;
}
