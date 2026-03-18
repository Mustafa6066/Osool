'use client';

import Link from 'next/link';
import { useEffect } from 'react';
import { usePathname } from 'next/navigation';
import { AnimatePresence, motion } from 'framer-motion';
import { Gift, LogIn, LogOut, Shield, X } from 'lucide-react';

import { useAuth } from '@/contexts/AuthContext';
import { useLanguage } from '@/contexts/LanguageContext';
import { AUTH_NAV, PUBLIC_NAV, getActiveKey } from './nav-items';

interface MoreSheetProps {
  open: boolean;
  onClose: () => void;
  onInvite: () => void;
}

export default function MoreSheet({ open, onClose, onInvite }: MoreSheetProps) {
  const pathname = usePathname();
  const { user, isAuthenticated, logout } = useAuth();
  const { language } = useLanguage();

  const activeKey = getActiveKey(pathname);
  const items = isAuthenticated ? AUTH_NAV : PUBLIC_NAV;
  const isAdmin = user?.role === 'admin';

  useEffect(() => {
    if (!open) {
      return;
    }

    const previousOverflow = document.body.style.overflow;
    const handleKeyDown = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        onClose();
      }
    };

    document.body.style.overflow = 'hidden';
    window.addEventListener('keydown', handleKeyDown);

    return () => {
      document.body.style.overflow = previousOverflow;
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, [open, onClose]);

  useEffect(() => {
    if (open) {
      onClose();
    }
  }, [pathname]);

  const closeThen = (action: () => void) => {
    onClose();
    action();
  };

  return (
    <AnimatePresence>
      {open && (
        <>
          <motion.button
            type="button"
            aria-label="Close navigation menu"
            className="fixed inset-0 z-[90] bg-slate-950/45 backdrop-blur-sm"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.16 }}
            onClick={onClose}
          />

          <motion.aside
            role="dialog"
            aria-modal="true"
            aria-label="Navigation menu"
            className="fixed inset-x-0 bottom-0 z-[95] mx-auto w-full max-w-md rounded-t-[28px] border border-[var(--color-border)] bg-[var(--color-surface)]/96 px-4 pb-8 pt-4 shadow-2xl shadow-black/20 backdrop-blur-2xl"
            initial={{ opacity: 0, y: 36 }}
            animate={{ opacity: 1, y: 0 }}
            exit={{ opacity: 0, y: 24 }}
            transition={{ type: 'spring', damping: 24, stiffness: 220 }}
          >
            <div className="mb-4 flex items-center justify-between">
              <div>
                <div className="text-sm font-semibold text-[var(--color-text-primary)]">
                  {language === 'ar' ? 'التنقل' : 'Navigation'}
                </div>
                <div className="text-xs text-[var(--color-text-muted)]">
                  {isAuthenticated
                    ? user?.full_name || user?.email || (language === 'ar' ? 'حسابك' : 'Your account')
                    : language === 'ar'
                      ? 'استكشف أصول'
                      : 'Explore Osool'}
                </div>
              </div>

              <button
                type="button"
                onClick={onClose}
                className="flex h-10 w-10 items-center justify-center rounded-2xl text-[var(--color-text-muted)] transition-colors hover:bg-[var(--color-surface-elevated)] hover:text-[var(--color-text-primary)]"
              >
                <X className="h-4 w-4" />
              </button>
            </div>

            <div className="grid gap-2">
              {items.map((item) => {
                const Icon = item.icon;
                const isActive = item.key === activeKey;

                return (
                  <Link
                    key={item.key}
                    href={item.href}
                    onClick={onClose}
                    className={[
                      'flex items-center gap-3 rounded-2xl px-4 py-3 text-sm font-medium transition-colors',
                      isActive
                        ? 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400'
                        : 'text-[var(--color-text-primary)] hover:bg-[var(--color-surface-elevated)]',
                    ].join(' ')}
                  >
                    <Icon className="h-4 w-4" strokeWidth={isActive ? 2.4 : 2} />
                    <span>{language === 'ar' ? item.labelAr : item.label}</span>
                  </Link>
                );
              })}

              {isAdmin && (
                <Link
                  href="/admin"
                  onClick={onClose}
                  className={[
                    'flex items-center gap-3 rounded-2xl px-4 py-3 text-sm font-medium transition-colors',
                    activeKey === 'admin'
                      ? 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400'
                      : 'text-[var(--color-text-primary)] hover:bg-[var(--color-surface-elevated)]',
                  ].join(' ')}
                >
                  <Shield className="h-4 w-4" strokeWidth={2} />
                  <span>{language === 'ar' ? 'الإدارة' : 'Admin'}</span>
                </Link>
              )}
            </div>

            <div className="mt-4 border-t border-[var(--color-border)] pt-4">
              {isAuthenticated ? (
                <div className="grid gap-2">
                  <button
                    type="button"
                    onClick={() => closeThen(onInvite)}
                    className="flex items-center gap-3 rounded-2xl px-4 py-3 text-sm font-medium text-emerald-600 transition-colors hover:bg-emerald-500/10 dark:text-emerald-400"
                  >
                    <Gift className="h-4 w-4" strokeWidth={2} />
                    <span>{language === 'ar' ? 'دعوة أصدقاء' : 'Invite Friends'}</span>
                  </button>

                  <button
                    type="button"
                    onClick={() => closeThen(logout)}
                    className="flex items-center gap-3 rounded-2xl px-4 py-3 text-sm font-medium text-red-500 transition-colors hover:bg-red-500/10"
                  >
                    <LogOut className="h-4 w-4" strokeWidth={2} />
                    <span>{language === 'ar' ? 'تسجيل الخروج' : 'Sign Out'}</span>
                  </button>
                </div>
              ) : (
                <Link
                  href="/login"
                  onClick={onClose}
                  className="flex items-center justify-center gap-2 rounded-2xl bg-emerald-500 px-4 py-3 text-sm font-semibold text-white transition-colors hover:bg-emerald-600"
                >
                  <LogIn className="h-4 w-4" strokeWidth={2} />
                  <span>{language === 'ar' ? 'تسجيل الدخول' : 'Login'}</span>
                </Link>
              )}
            </div>
          </motion.aside>
        </>
      )}
    </AnimatePresence>
  );
}