'use client';

import React, { useState, useEffect, useCallback } from 'react';
import { usePathname, useRouter } from 'next/navigation';
import Link from 'next/link';
import { motion, AnimatePresence, useAnimationControls } from 'framer-motion';
import {
  Sparkles, Sun, Moon, Gift, LogOut, User, Shield, Search,
} from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';
import { useTheme } from '@/contexts/ThemeContext';
import { useLanguage } from '@/contexts/LanguageContext';
import { AUTH_NAV, PUBLIC_NAV, getActiveKey, type NavItem } from '@/components/nav/nav-items';
import NotificationBell from '@/components/NotificationBell';

const SPRING_SNAPPY = { type: 'spring' as const, damping: 24, stiffness: 280 };
const SPRING_PANEL = { type: 'spring' as const, damping: 28, stiffness: 240 };
const NAV_EXPANDED_KEY = 'osool:bottom-nav-expanded';

interface SmartNavProps {
  onInvite: () => void;
}

interface NavButtonProps {
  item: NavItem;
  active: boolean;
  language: string;
  onClick: () => void;
}

function NavButton({ item, active, language, onClick }: NavButtonProps) {
  const Icon = item.icon;
  return (
    <motion.button
      onClick={onClick}
      whileTap={{ scale: 0.97 }}
      className={`flex items-center gap-2 rounded-xl border px-3 py-2 text-sm transition-colors ${
        active
          ? 'border-emerald-500/25 bg-emerald-500/10 text-emerald-600 dark:text-emerald-400'
          : 'border-[var(--color-border)] bg-[var(--color-background)] text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)]'
      }`}
      aria-current={active ? 'page' : undefined}
      aria-label={language === 'ar' ? item.labelAr : item.label}
    >
      <Icon className="h-4 w-4" strokeWidth={active ? 2.2 : 1.8} />
      <span className="truncate">{language === 'ar' ? item.labelAr : item.label}</span>
    </motion.button>
  );
}

export default function SmartNav({ onInvite }: SmartNavProps) {
  const pathname = usePathname();
  const router = useRouter();
  const { user, isAuthenticated, logout } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const { language, toggleLanguage } = useLanguage();

  const activeKey = getActiveKey(pathname);
  const items: NavItem[] = isAuthenticated ? AUTH_NAV : PUBLIC_NAV;
  const isAdmin = user?.role === 'admin';
  const userInitial = (user?.full_name || user?.email || 'U').charAt(0).toUpperCase();

  const [expanded, setExpanded] = useState(false);
  const toggleControls = useAnimationControls();

  useEffect(() => {
    const stored = localStorage.getItem(NAV_EXPANDED_KEY);
    if (stored === '1') setExpanded(true);
  }, []);

  useEffect(() => {
    localStorage.setItem(NAV_EXPANDED_KEY, expanded ? '1' : '0');
  }, [expanded]);

  const triggerSearch = useCallback(() => {
    document.dispatchEvent(
      new KeyboardEvent('keydown', {
        key: 'k',
        ctrlKey: true,
        metaKey: true,
        bubbles: true,
      })
    );
  }, []);

  const togglePanel = useCallback(() => {
    setExpanded((v) => !v);
    void toggleControls.start({
      scale: [1, 0.93, 1.05, 1],
      transition: { duration: 0.28, times: [0, 0.3, 0.68, 1], ease: 'easeOut' },
    });
  }, [toggleControls]);

  const handleNavigate = useCallback((href: string) => {
    router.push(href);
    setExpanded(false);
  }, [router]);

  return (
    <div className="fixed inset-x-0 bottom-0 z-[70] pointer-events-none">
      <motion.nav
        initial={{ y: 100, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={SPRING_PANEL}
        aria-label={language === 'ar' ? 'التنقل الرئيسي' : 'Main navigation'}
        className="pointer-events-auto mx-auto mb-[calc(env(safe-area-inset-bottom,0px)+10px)] w-[calc(100%-14px)] max-w-6xl rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)]/92 p-2 backdrop-blur-xl shadow-[0_14px_36px_rgba(0,0,0,0.14)]"
      >
        <div className="flex items-center gap-2">
          <motion.button
            onClick={togglePanel}
            initial={false}
            animate={toggleControls}
            whileTap={{ scale: 0.94 }}
            className="flex h-10 w-10 items-center justify-center rounded-xl border border-[var(--color-border)] bg-[var(--color-background)]"
            aria-label={expanded ? (language === 'ar' ? 'طي التنقل' : 'Collapse navigation') : (language === 'ar' ? 'فتح التنقل' : 'Expand navigation')}
            title={expanded ? (language === 'ar' ? 'طي' : 'Collapse') : (language === 'ar' ? 'فتح' : 'Expand')}
          >
            {/* Always-visible 3-dot control */}
            <div className="flex flex-col items-center justify-center gap-1">
              {[0, 1, 2].map((dot) => (
                <motion.span
                  key={dot}
                  animate={{ width: expanded ? 18 : 14, opacity: expanded ? 0.95 : 0.8 }}
                  transition={{ duration: 0.2, ease: 'easeOut' }}
                  className="block h-[3px] rounded-full bg-[var(--color-text-secondary)]"
                />
              ))}
            </div>
          </motion.button>

          <button
            onClick={triggerSearch}
            className="flex h-10 items-center gap-2 rounded-xl border border-[var(--color-border)] bg-[var(--color-background)] px-3 text-xs font-semibold text-emerald-600 dark:text-emerald-400"
          >
            <Search className="h-3.5 w-3.5" />
            {language === 'ar' ? 'اسأل أصول' : 'Ask Osool'}
          </button>

          <div className="ms-auto flex items-center gap-1.5">
            <NotificationBell />
            <button
              onClick={toggleTheme}
              aria-label={theme === 'dark' ? 'Light mode' : 'Dark mode'}
              className="flex h-9 w-9 items-center justify-center rounded-lg border border-[var(--color-border)] bg-[var(--color-background)] text-[var(--color-text-muted)]"
            >
              {theme === 'dark' ? <Sun className="h-4 w-4" /> : <Moon className="h-4 w-4" />}
            </button>
            <button
              onClick={toggleLanguage}
              aria-label={language === 'en' ? 'العربية' : 'English'}
              className="flex h-9 w-9 items-center justify-center rounded-lg border border-[var(--color-border)] bg-[var(--color-background)] text-[11px] font-bold text-[var(--color-text-muted)]"
            >
              {language === 'en' ? 'ع' : 'En'}
            </button>
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-gradient-to-br from-emerald-400 to-emerald-600 text-[11px] font-bold text-white">
              {userInitial}
            </div>
          </div>
        </div>

        <AnimatePresence initial={false}>
          {expanded && (
            <motion.div
              initial={{ opacity: 0, height: 0, y: 10 }}
              animate={{ opacity: 1, height: 'auto', y: 0 }}
              exit={{ opacity: 0, height: 0, y: 8 }}
              transition={{ duration: 0.26, ease: 'easeOut' }}
              className="overflow-hidden"
            >
              <div className="mt-2 border-t border-[var(--color-border)] pt-2">
                <div className="flex flex-wrap gap-2">
                  {items.map((item) => (
                    <NavButton
                      key={item.key}
                      item={item}
                      active={item.key === activeKey}
                      language={language}
                      onClick={() => handleNavigate(item.href)}
                    />
                  ))}

                  {isAdmin && (
                    <motion.button
                      onClick={() => handleNavigate('/admin')}
                      whileTap={{ scale: 0.97 }}
                      className={`flex items-center gap-2 rounded-xl border px-3 py-2 text-sm transition-colors ${
                        activeKey === 'admin'
                          ? 'border-emerald-500/25 bg-emerald-500/10 text-emerald-600 dark:text-emerald-400'
                          : 'border-[var(--color-border)] bg-[var(--color-background)] text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)]'
                      }`}
                    >
                      <Shield className="h-4 w-4" strokeWidth={activeKey === 'admin' ? 2.2 : 1.8} />
                      <span>{language === 'ar' ? 'المدير' : 'Admin'}</span>
                    </motion.button>
                  )}
                </div>

                <div className="mt-2 flex flex-wrap gap-2">
                  {isAuthenticated ? (
                    <>
                      <motion.button
                        onClick={() => {
                          onInvite();
                          setExpanded(false);
                        }}
                        whileTap={{ scale: 0.97 }}
                        className="flex items-center gap-2 rounded-xl border border-emerald-500/20 bg-emerald-500/10 px-3 py-2 text-sm text-emerald-600 dark:text-emerald-400"
                      >
                        <Gift className="h-4 w-4" />
                        {language === 'ar' ? 'دعوة أصدقاء' : 'Invite Friends'}
                      </motion.button>

                      <motion.button
                        onClick={() => {
                          logout();
                          setExpanded(false);
                        }}
                        whileTap={{ scale: 0.97 }}
                        className="flex items-center gap-2 rounded-xl border border-red-500/20 bg-red-500/10 px-3 py-2 text-sm text-red-500"
                      >
                        <LogOut className="h-4 w-4" />
                        {language === 'ar' ? 'تسجيل الخروج' : 'Sign Out'}
                      </motion.button>
                    </>
                  ) : (
                    <Link
                      href="/login"
                      onClick={() => setExpanded(false)}
                      className="inline-flex items-center gap-2 rounded-xl bg-[var(--color-text-primary)] px-3 py-2 text-sm font-semibold text-[var(--color-background)]"
                    >
                      <User className="h-4 w-4" />
                      {language === 'ar' ? 'تسجيل الدخول' : 'Login'}
                    </Link>
                  )}
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </motion.nav>
    </div>
  );
}
