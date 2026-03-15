'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { MoreHorizontal } from 'lucide-react';
import { motion } from 'framer-motion';
import { useAuth } from '@/contexts/AuthContext';
import { useLanguage } from '@/contexts/LanguageContext';
import { AUTH_NAV, PUBLIC_NAV, getActiveKey } from './nav-items';
import { useState } from 'react';
import MoreSheet from './MoreSheet';

interface BottomBarProps {
  onInvite: () => void;
}

export default function BottomBar({ onInvite }: BottomBarProps) {
  const pathname = usePathname();
  const { isAuthenticated } = useAuth();
  const { language } = useLanguage();
  const activeKey = getActiveKey(pathname);
  const [moreOpen, setMoreOpen] = useState(false);

  const allItems = isAuthenticated ? AUTH_NAV : PUBLIC_NAV;
  const items = allItems.slice(0, 4);

  return (
    <>
      {/* Floating bottom pill */}
      <div className="fixed bottom-4 left-1/2 -translate-x-1/2 z-40 md:hidden">
        <nav className="flex items-center gap-0.5 px-1.5 py-1.5 rounded-2xl bg-[var(--color-surface)]/90 backdrop-blur-2xl border border-[var(--color-border)] shadow-lg shadow-black/8">
          {items.map((item) => {
            const Icon = item.icon;
            const isActive = item.key === activeKey;
            return (
              <Link
                key={item.key}
                href={item.href}
                className="relative flex flex-col items-center justify-center w-[52px] py-1.5 rounded-xl"
              >
                <motion.div
                  className={`flex flex-col items-center gap-0.5 ${
                    isActive ? 'text-emerald-500' : 'text-[var(--color-text-muted)]'
                  }`}
                  whileTap={{ scale: 0.9 }}
                >
                  <Icon className="w-5 h-5" strokeWidth={isActive ? 2.5 : 1.8} />
                  <span className="text-[10px] font-medium leading-none">
                    {language === 'ar' ? item.labelAr : item.label}
                  </span>
                </motion.div>
                {isActive && (
                  <motion.div
                    className="absolute -top-0.5 left-1/2 -translate-x-1/2 w-4 h-[2px] rounded-full bg-emerald-500"
                    layoutId="bottom-indicator"
                    transition={{ type: 'spring', stiffness: 400, damping: 30 }}
                  />
                )}
              </Link>
            );
          })}

          {/* More button */}
          <button
            onClick={() => setMoreOpen(true)}
            className="flex flex-col items-center justify-center w-[52px] py-1.5 rounded-xl text-[var(--color-text-muted)]"
          >
            <motion.div
              className="flex flex-col items-center gap-0.5"
              whileTap={{ scale: 0.9 }}
            >
              <MoreHorizontal className="w-5 h-5" strokeWidth={1.8} />
              <span className="text-[10px] font-medium leading-none">
                {language === 'ar' ? 'المزيد' : 'More'}
              </span>
            </motion.div>
          </button>
        </nav>
      </div>

      <MoreSheet open={moreOpen} onClose={() => setMoreOpen(false)} onInvite={onInvite} />
    </>
  );
}
