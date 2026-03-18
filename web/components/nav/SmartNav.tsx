'use client';

import React, { useState, useEffect, useCallback, useRef } from 'react';
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
const SPRING_PANEL = { type: 'spring' as const, damping: 26, stiffness: 230 };
const NAV_EXPANDED_KEY = 'osool:floating-nav-expanded';

interface SmartNavProps {
  onInvite: () => void;
}

interface NavPillProps {
  item: NavItem;
  active: boolean;
  language: string;
  onClick: () => void;
}

function NavPill({ item, active, language, onClick }: NavPillProps) {
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
  const panelRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const stored = localStorage.getItem(NAV_EXPANDED_KEY);
    if (stored === '1') setExpanded(true);
  }, []);

  useEffect(() => {
    localStorage.setItem(NAV_EXPANDED_KEY, expanded ? '1' : '0');
  }, [expanded]);

  useEffect(() => {
    setExpanded(false);
  }, [pathname]);

  useEffect(() => {
    const keyHandler = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setExpanded(false);
    };
    const clickHandler = (e: MouseEvent) => {
      if (!expanded) return;
      if (panelRef.current && !panelRef.current.contains(e.target as Node)) {
        setExpanded(false);
      }
    };
    document.addEventListener('keydown', keyHandler);
    document.addEventListener('mousedown', clickHandler);
    return () => {
      document.removeEventListener('keydown', keyHandler);
      document.removeEventListener('mousedown', clickHandler);
    };
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

  const handleNavigate = useCallback((href: string) => {
    router.push(href);
    setExpanded(false);
  }, [router]);

  const handleToggle = useCallback(() => {
    setExpanded((v) => !v);
    void toggleControls.start({
      scale: [1, 0.93, 1.05, 1],
      transition: { duration: 0.28, times: [0, 0.3, 0.68, 1], ease: 'easeOut' },
    });
  }, [toggleControls]);

  return (
    <>
      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="fixed inset-0 z-[68] bg-black/18 backdrop-blur-[1px]"
            aria-hidden
          />
        )}
      </AnimatePresence>

      {/* Always visible 3-dot trigger pinned to viewport bottom-left */}
      <motion.button
        onClick={handleToggle}
        initial={false}
        animate={toggleControls}
        whileTap={{ scale: 0.94 }}
        whileHover={{ scale: 1.03 }}
        className="fixed start-4 bottom-[calc(env(safe-area-inset-bottom,0px)+14px)] z-[71] flex h-12 w-12 items-center justify-center rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)]/95 backdrop-blur-xl shadow-[0_8px_24px_rgba(0,0,0,0.16)]"
        aria-label={expanded ? (language === 'ar' ? 'طي لوحة التنقل' : 'Collapse navigation panel') : (language === 'ar' ? 'فتح لوحة التنقل' : 'Expand navigation panel')}
        title={expanded ? (language === 'ar' ? 'طي' : 'Collapse') : (language === 'ar' ? 'فتح' : 'Expand')}
      >
        <div className="relative h-5 w-6">
          {[0, 1, 2].map((dot) => (
            <motion.span
              key={dot}
              animate={{
                width: expanded ? 18 : 14,
                opacity: expanded ? 0.95 : 0.8,
                y: dot === 0 ? (expanded ? -5 : -6) : dot === 1 ? 0 : (expanded ? 5 : 6),
              }}
              transition={{ duration: 0.22, ease: 'easeOut' }}
              className="absolute left-1/2 top-1/2 block h-[3px] -translate-x-1/2 rounded-full bg-[var(--color-text-secondary)]"
            />
          ))}
        </div>
      </motion.button>

      {/* Floating bottom panel (collapses entirely into the 3 dots) */}
      <AnimatePresence>
        {expanded && (
          <motion.nav
            ref={panelRef}
            initial={{ opacity: 0, y: 30, scale: 0.97, filter: 'blur(6px)' }}
            animate={{ opacity: 1, y: 0, scale: 1, filter: 'blur(0px)' }}
            exit={{ opacity: 0, y: 20, scale: 0.98, filter: 'blur(4px)' }}
            transition={SPRING_PANEL}
            className="fixed inset-x-3 sm:inset-x-6 bottom-[calc(env(safe-area-inset-bottom,0px)+12px)] z-[70] rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)]/96 p-3 sm:p-4 backdrop-blur-xl shadow-[0_20px_50px_rgba(0,0,0,0.16)]"
            aria-label={language === 'ar' ? 'لوحة التنقل العائمة' : 'Floating navigation panel'}
          >
            <div className="flex items-center justify-between gap-2 pb-2">
              <div className="flex items-center gap-2">
                <Link
                  href="/"
                  onClick={() => setExpanded(false)}
                  className="flex items-center gap-2 rounded-lg px-2 py-1.5 hover:bg-[var(--color-background)] transition-colors"
                >
                  <div className="w-6 h-6 rounded-md bg-gradient-to-br from-emerald-400 to-emerald-600 flex items-center justify-center">
                    <Sparkles className="w-3.5 h-3.5 text-white" />
                  </div>
                  <span className="text-sm font-semibold text-[var(--color-text-primary)]">{language === 'ar' ? 'أصول' : 'Osool'}</span>
                </Link>
              </div>

              <div className="flex items-center gap-1.5">
                <button
                  onClick={triggerSearch}
                  className="flex h-9 items-center gap-1.5 rounded-lg border border-[var(--color-border)] bg-[var(--color-background)] px-2.5 text-[11px] font-semibold text-emerald-600 dark:text-emerald-400"
                >
                  <Search className="h-3.5 w-3.5" />
                  {language === 'ar' ? 'اسأل أصول' : 'Ask Osool'}
                </button>
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

            <div className="border-t border-[var(--color-border)] pt-3">
              <div className="flex flex-wrap gap-2">
                {items.map((item) => (
                  <NavPill
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
          </motion.nav>
        )}
      </AnimatePresence>
    </>
  );
}
