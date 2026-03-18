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
const SPRING_SMOOTH = { type: 'spring' as const, damping: 26, stiffness: 220 };
const DESKTOP_COLLAPSE_KEY = 'osool:desktop-nav-collapsed';
const MOBILE_COLLAPSE_KEY = 'osool:mobile-nav-collapsed';

interface SmartNavProps {
  onInvite: () => void;
}

interface NavPanelContentProps {
  items: NavItem[];
  activeKey: string;
  isAdmin: boolean;
  isAuthenticated: boolean;
  language: string;
  theme: string;
  userInitial: string;
  onNavigate: (href: string) => void;
  onOpenAdmin: () => void;
  onSearch: () => void;
  onToggleTheme: () => void;
  onToggleLanguage: () => void;
  onInvite: () => void;
  onLogout: () => void;
}

function NavPanelContent({
  items,
  activeKey,
  isAdmin,
  isAuthenticated,
  language,
  theme,
  userInitial,
  onNavigate,
  onOpenAdmin,
  onSearch,
  onToggleTheme,
  onToggleLanguage,
  onInvite,
  onLogout,
}: NavPanelContentProps) {
  return (
    <div className="flex h-full w-full flex-col px-3 py-4">
      <Link
        href="/"
        className="mb-3 flex items-center gap-2 rounded-xl px-2 py-2 hover:bg-[var(--color-surface)] transition-colors"
        aria-label="Osool Home"
      >
        <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-emerald-400 to-emerald-600 flex items-center justify-center">
          <Sparkles className="w-4 h-4 text-white" />
        </div>
        <span className="text-sm font-semibold tracking-tight text-[var(--color-text-primary)]">
          {language === 'ar' ? 'أصول' : 'Osool'}
        </span>
      </Link>

      <div className="space-y-1">
        {items.map((item) => {
          const Icon = item.icon;
          const isActive = item.key === activeKey;
          return (
            <motion.button
              key={item.key}
              onClick={() => onNavigate(item.href)}
              whileTap={{ scale: 0.98 }}
              className={`w-full flex items-center gap-2.5 rounded-xl px-3 py-2 text-sm transition-colors ${
                isActive
                  ? 'bg-emerald-500/12 text-emerald-600 dark:text-emerald-400'
                  : 'text-[var(--color-text-secondary)] hover:bg-[var(--color-surface)] hover:text-[var(--color-text-primary)]'
              }`}
              aria-current={isActive ? 'page' : undefined}
            >
              <Icon className="w-4 h-4" strokeWidth={isActive ? 2.2 : 1.8} />
              <span className="truncate">{language === 'ar' ? item.labelAr : item.label}</span>
            </motion.button>
          );
        })}

        {isAdmin && (
          <motion.button
            onClick={onOpenAdmin}
            whileTap={{ scale: 0.98 }}
            className={`w-full flex items-center gap-2.5 rounded-xl px-3 py-2 text-sm transition-colors ${
              activeKey === 'admin'
                ? 'bg-emerald-500/12 text-emerald-600 dark:text-emerald-400'
                : 'text-[var(--color-text-secondary)] hover:bg-[var(--color-surface)] hover:text-[var(--color-text-primary)]'
            }`}
          >
            <Shield className="w-4 h-4" strokeWidth={activeKey === 'admin' ? 2.2 : 1.8} />
            <span>{language === 'ar' ? 'المدير' : 'Admin'}</span>
          </motion.button>
        )}
      </div>

      <div className="mt-4 rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)]/60 p-2">
        <button
          onClick={onSearch}
          className="w-full flex items-center gap-2 rounded-lg px-2.5 py-2 text-xs font-semibold text-emerald-600 dark:text-emerald-400 hover:bg-emerald-500/10 transition-colors"
        >
          <Search className="w-3.5 h-3.5" />
          {language === 'ar' ? 'اسأل أصول' : 'Ask Osool'}
        </button>
      </div>

      <div className="mt-auto space-y-2 border-t border-[var(--color-border)] pt-3">
        <div className="flex items-center gap-2 px-1">
          <NotificationBell />
          <button
            onClick={onToggleTheme}
            aria-label={theme === 'dark' ? 'Light mode' : 'Dark mode'}
            className="flex items-center justify-center w-9 h-9 rounded-lg text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)] hover:bg-[var(--color-surface)] transition-colors"
          >
            {theme === 'dark' ? <Sun className="w-4.5 h-4.5" /> : <Moon className="w-4.5 h-4.5" />}
          </button>
          <button
            onClick={onToggleLanguage}
            aria-label={language === 'en' ? 'العربية' : 'English'}
            className="flex items-center justify-center w-9 h-9 rounded-lg text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)] hover:bg-[var(--color-surface)] transition-colors text-xs font-bold"
          >
            {language === 'en' ? 'ع' : 'En'}
          </button>
          <div className="ms-auto w-7 h-7 rounded-full bg-gradient-to-br from-emerald-400 to-emerald-600 flex items-center justify-center text-white text-[11px] font-bold">
            {userInitial}
          </div>
        </div>

        {isAuthenticated ? (
          <>
            <button
              onClick={onInvite}
              className="w-full flex items-center gap-2 rounded-lg px-3 py-2 text-sm text-emerald-600 dark:text-emerald-400 hover:bg-emerald-500/10 transition-colors"
            >
              <Gift className="w-4 h-4" />
              {language === 'ar' ? 'دعوة أصدقاء' : 'Invite Friends'}
            </button>
            <button
              onClick={onLogout}
              className="w-full flex items-center gap-2 rounded-lg px-3 py-2 text-sm text-red-500 hover:bg-red-500/10 transition-colors"
            >
              <LogOut className="w-4 h-4" />
              {language === 'ar' ? 'تسجيل الخروج' : 'Sign Out'}
            </button>
          </>
        ) : (
          <Link
            href="/login"
            className="w-full flex items-center justify-center gap-2 rounded-lg px-3 py-2 text-sm font-semibold bg-[var(--color-text-primary)] text-[var(--color-background)] hover:opacity-90 transition-opacity"
          >
            <User className="w-4 h-4" />
            {language === 'ar' ? 'تسجيل الدخول' : 'Login'}
          </Link>
        )}
      </div>
    </div>
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

  const [desktopCollapsed, setDesktopCollapsed] = useState(false);
  const [mobileCollapsed, setMobileCollapsed] = useState(true);
  const desktopToggleControls = useAnimationControls();
  const mobileToggleControls = useAnimationControls();

  useEffect(() => {
    const desktopStored = localStorage.getItem(DESKTOP_COLLAPSE_KEY);
    const mobileStored = localStorage.getItem(MOBILE_COLLAPSE_KEY);
    if (desktopStored === '1') setDesktopCollapsed(true);
    if (mobileStored === '0') setMobileCollapsed(false);
  }, []);

  useEffect(() => {
    localStorage.setItem(DESKTOP_COLLAPSE_KEY, desktopCollapsed ? '1' : '0');
    document.documentElement.style.setProperty('--desktop-nav-offset', desktopCollapsed ? '0px' : '256px');
    return () => {
      document.documentElement.style.setProperty('--desktop-nav-offset', '0px');
    };
  }, [desktopCollapsed]);

  useEffect(() => {
    localStorage.setItem(MOBILE_COLLAPSE_KEY, mobileCollapsed ? '1' : '0');
  }, [mobileCollapsed]);

  useEffect(() => {
    setMobileCollapsed(true);
  }, [pathname]);

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setMobileCollapsed(true);
    };
    document.addEventListener('keydown', handler);
    return () => document.removeEventListener('keydown', handler);
  }, []);

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

  const closeMobileAfter = useCallback((fn: () => void) => {
    fn();
    setMobileCollapsed(true);
  }, []);

  const handleDesktopToggle = useCallback(() => {
    setDesktopCollapsed((v) => !v);
    void desktopToggleControls.start({
      scale: [1, 0.93, 1.04, 1],
      transition: { duration: 0.28, times: [0, 0.3, 0.68, 1], ease: 'easeOut' },
    });
  }, [desktopToggleControls]);

  const handleMobileToggle = useCallback(() => {
    setMobileCollapsed((v) => !v);
    void mobileToggleControls.start({
      scale: [1, 0.92, 1.05, 1],
      transition: { duration: 0.28, times: [0, 0.3, 0.68, 1], ease: 'easeOut' },
    });
  }, [mobileToggleControls]);

  return (
    <>
      <AnimatePresence>
        {!desktopCollapsed && (
          <motion.aside
            initial={{ x: -280, opacity: 0 }}
            animate={{ x: 0, opacity: 1 }}
            exit={{ x: -280, opacity: 0 }}
            transition={SPRING_SMOOTH}
            className="hidden sm:flex fixed top-0 start-0 bottom-0 z-50 w-64 border-e border-[var(--color-border)] bg-[var(--color-background)]/92 backdrop-blur-xl"
            aria-label={language === 'ar' ? 'لوحة التنقل' : 'Navigation panel'}
          >
            <NavPanelContent
              items={items}
              activeKey={activeKey}
              isAdmin={isAdmin}
              isAuthenticated={isAuthenticated}
              language={language}
              theme={theme}
              userInitial={userInitial}
              onNavigate={(href) => router.push(href)}
              onOpenAdmin={() => router.push('/admin')}
              onSearch={triggerSearch}
              onToggleTheme={toggleTheme}
              onToggleLanguage={toggleLanguage}
              onInvite={onInvite}
              onLogout={logout}
            />
          </motion.aside>
        )}
      </AnimatePresence>

      <AnimatePresence>
        {!mobileCollapsed && (
          <>
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.2 }}
              onClick={() => setMobileCollapsed(true)}
              className="fixed inset-0 z-[58] bg-black/30 backdrop-blur-[1px] sm:hidden"
              aria-hidden
            />
            <motion.aside
              initial={{ x: -280, opacity: 0 }}
              animate={{ x: 0, opacity: 1 }}
              exit={{ x: -280, opacity: 0 }}
              transition={SPRING_SMOOTH}
              className="fixed top-0 start-0 bottom-0 z-[59] w-[78vw] max-w-[280px] border-e border-[var(--color-border)] bg-[var(--color-background)]/96 backdrop-blur-xl sm:hidden"
              aria-label={language === 'ar' ? 'لوحة التنقل' : 'Navigation panel'}
            >
              <NavPanelContent
                items={items}
                activeKey={activeKey}
                isAdmin={isAdmin}
                isAuthenticated={isAuthenticated}
                language={language}
                theme={theme}
                userInitial={userInitial}
                onNavigate={(href) => closeMobileAfter(() => router.push(href))}
                onOpenAdmin={() => closeMobileAfter(() => router.push('/admin'))}
                onSearch={() => closeMobileAfter(triggerSearch)}
                onToggleTheme={toggleTheme}
                onToggleLanguage={toggleLanguage}
                onInvite={() => closeMobileAfter(onInvite)}
                onLogout={() => closeMobileAfter(logout)}
              />
            </motion.aside>
          </>
        )}
      </AnimatePresence>

      <motion.button
        onClick={handleDesktopToggle}
        initial={false}
        animate={desktopToggleControls}
        className="hidden sm:flex fixed start-4 bottom-4 z-[60] h-12 w-12 items-center justify-center rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)]/90 backdrop-blur-lg shadow-[0_8px_24px_rgba(0,0,0,0.12)]"
        whileTap={{ scale: 0.94 }}
        whileHover={{ scale: 1.03 }}
        aria-label={desktopCollapsed ? (language === 'ar' ? 'فتح لوحة التنقل' : 'Expand navigation panel') : (language === 'ar' ? 'طي لوحة التنقل' : 'Collapse navigation panel')}
        title={desktopCollapsed ? (language === 'ar' ? 'فتح' : 'Expand') : (language === 'ar' ? 'طي' : 'Collapse')}
      >
        <div className="flex flex-col items-center justify-center gap-1.5">
          {[0, 1, 2].map((dot) => (
            <motion.span
              key={dot}
              animate={{
                width: desktopCollapsed ? 22 : 16,
                opacity: desktopCollapsed ? 0.95 : 0.75,
              }}
              transition={{ duration: 0.25, ease: 'easeOut' }}
              className="block h-1 rounded-full bg-[var(--color-text-secondary)]"
            />
          ))}
        </div>
      </motion.button>

      <motion.button
        onClick={handleMobileToggle}
        initial={false}
        animate={mobileToggleControls}
        className="sm:hidden fixed start-3 bottom-[calc(env(safe-area-inset-bottom,0px)+12px)] z-[60] h-11 w-11 items-center justify-center rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)]/92 backdrop-blur-lg shadow-[0_8px_24px_rgba(0,0,0,0.14)]"
        whileTap={{ scale: 0.94 }}
        whileHover={{ scale: 1.03 }}
        aria-label={mobileCollapsed ? (language === 'ar' ? 'فتح لوحة التنقل' : 'Expand navigation panel') : (language === 'ar' ? 'طي لوحة التنقل' : 'Collapse navigation panel')}
        title={mobileCollapsed ? (language === 'ar' ? 'فتح' : 'Expand') : (language === 'ar' ? 'طي' : 'Collapse')}
      >
        <div className="relative h-5 w-6">
          <motion.span
            animate={{
              width: mobileCollapsed ? 20 : 18,
              y: mobileCollapsed ? -6 : 0,
              rotate: mobileCollapsed ? 0 : 45,
              opacity: 0.95,
            }}
            transition={SPRING_SNAPPY}
            className="absolute left-1/2 top-1/2 block h-1 -translate-x-1/2 rounded-full bg-[var(--color-text-secondary)]"
          />
          <motion.span
            animate={{
              width: mobileCollapsed ? 20 : 0,
              y: 0,
              opacity: mobileCollapsed ? 0.95 : 0,
            }}
            transition={SPRING_SNAPPY}
            className="absolute left-1/2 top-1/2 block h-1 -translate-x-1/2 rounded-full bg-[var(--color-text-secondary)]"
          />
          <motion.span
            animate={{
              width: mobileCollapsed ? 20 : 18,
              y: mobileCollapsed ? 6 : 0,
              rotate: mobileCollapsed ? 0 : -45,
              opacity: 0.95,
            }}
            transition={SPRING_SNAPPY}
            className="absolute left-1/2 top-1/2 block h-1 -translate-x-1/2 rounded-full bg-[var(--color-text-secondary)]"
          />
        </div>
      </motion.button>
    </>
  );
}
