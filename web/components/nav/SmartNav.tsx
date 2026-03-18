'use client';

import React, { useState, useRef, useEffect, useCallback } from 'react';
import { usePathname, useRouter } from 'next/navigation';
import Link from 'next/link';
import { motion, AnimatePresence, LayoutGroup } from 'framer-motion';
import {
  Sparkles, Sun, Moon, Gift, LogOut, User, Shield,
  Search, Menu, X,
} from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';
import { useTheme } from '@/contexts/ThemeContext';
import { useLanguage } from '@/contexts/LanguageContext';
import { AUTH_NAV, PUBLIC_NAV, getActiveKey, type NavItem } from '@/components/nav/nav-items';
import NotificationBell from '@/components/NotificationBell';

/* ─── spring presets ─────────────────────────── */
const SPRING_SNAPPY = { type: 'spring' as const, damping: 26, stiffness: 300 };
const SPRING_SMOOTH = { type: 'spring' as const, damping: 24, stiffness: 200 };

/* ─── types ──────────────────────────────────── */
interface SmartNavProps {
  onInvite: () => void;
}

/* ═══════════════════════════════════════════════
   SMART NAV — Unified responsive navigation
   Desktop: Floating glass header (top)
   Mobile : Bottom tab bar + slide-up more sheet
   ═══════════════════════════════════════════════ */
export default function SmartNav({ onInvite }: SmartNavProps) {
  const pathname = usePathname();
  const router = useRouter();
  const { user, isAuthenticated, logout } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const { language, toggleLanguage } = useLanguage();
  const activeKey = getActiveKey(pathname);

  const items: NavItem[] = isAuthenticated ? AUTH_NAV : PUBLIC_NAV;
  const isAdmin = user?.role === 'admin';

  // Mobile sheet
  const [mobileOpen, setMobileOpen] = useState(false);
  // User menu (desktop)
  const [userMenuOpen, setUserMenuOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  // Close menus on route change
  useEffect(() => {
    setMobileOpen(false);
    setUserMenuOpen(false);
  }, [pathname]);

  // Outside-click for user menu
  useEffect(() => {
    if (!userMenuOpen) return;
    const handler = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) {
        setUserMenuOpen(false);
      }
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, [userMenuOpen]);

  // Escape key closes mobile sheet
  useEffect(() => {
    if (!mobileOpen) return;
    const handler = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setMobileOpen(false);
    };
    document.addEventListener('keydown', handler);
    return () => document.removeEventListener('keydown', handler);
  }, [mobileOpen]);

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

  // Mobile: first 4 items in bottom bar, rest in sheet
  const mobileBarItems = items.slice(0, 4);

  return (
    <>
      {/* ════════════════════════════════════════
         DESKTOP — Floating Glass Header
         ════════════════════════════════════════ */}
      <motion.header
        initial={{ y: -20, opacity: 0 }}
        animate={{ y: 0, opacity: 1 }}
        transition={SPRING_SMOOTH}
        className="fixed top-4 start-1/2 rtl:translate-x-1/2 ltr:-translate-x-1/2 z-50 hidden sm:flex items-center gap-1.5 px-3 py-2 rounded-2xl liquid-glass"
        role="banner"
      >
        <LayoutGroup id="desktop-nav">
          {/* Logo */}
          <Link
            href="/"
            className="flex items-center gap-2 px-3 py-1.5 rounded-xl hover:bg-[var(--color-surface-hover)] transition-colors"
            aria-label="Osool Home"
          >
            <div className="w-7 h-7 rounded-lg bg-gradient-to-br from-emerald-400 to-emerald-600 flex items-center justify-center">
              <Sparkles className="w-4 h-4 text-white" />
            </div>
            <span className="text-sm font-semibold tracking-tight text-[var(--color-text-primary)]">
              {language === 'ar' ? 'أصول' : 'Osool'}
            </span>
          </Link>

          {/* Divider */}
          <div className="w-px h-6 bg-[var(--color-border)] mx-1" />

          {/* Nav items */}
          {items.map((item) => {
            const Icon = item.icon;
            const isActive = item.key === activeKey;
            return (
              <motion.button
                key={item.key}
                onClick={() => router.push(item.href)}
                aria-label={language === 'ar' ? item.labelAr : item.label}
                aria-current={isActive ? 'page' : undefined}
                className="relative flex items-center gap-1.5 px-3 py-2 rounded-xl text-sm font-medium transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-emerald-400/50"
                whileHover={{ scale: 1.02 }}
                whileTap={{ scale: 0.97 }}
              >
                {isActive && (
                  <motion.div
                    layoutId="nav-active"
                    className="absolute inset-0 rounded-xl bg-emerald-500/10 -z-10"
                    transition={SPRING_SNAPPY}
                  />
                )}
                <Icon
                  className={`w-4 h-4 ${
                    isActive ? 'text-emerald-500' : 'text-[var(--color-text-muted)]'
                  }`}
                  strokeWidth={isActive ? 2.2 : 1.6}
                />
                <span
                  className={
                    isActive
                      ? 'text-[var(--color-text-primary)]'
                      : 'text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)]'
                  }
                >
                  {language === 'ar' ? item.labelAr : item.label}
                </span>
              </motion.button>
            );
          })}

          {/* Admin shortcut */}
          {isAdmin && (
            <motion.button
              onClick={() => router.push('/admin')}
              aria-label="Admin"
              className="relative flex items-center gap-1.5 px-3 py-2 rounded-xl text-sm font-medium transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-emerald-400/50"
              whileHover={{ scale: 1.02 }}
              whileTap={{ scale: 0.97 }}
            >
              {activeKey === 'admin' && (
                <motion.div
                  layoutId="nav-active"
                  className="absolute inset-0 rounded-xl bg-emerald-500/10 -z-10"
                  transition={SPRING_SNAPPY}
                />
              )}
              <Shield
                className={`w-4 h-4 ${
                  activeKey === 'admin' ? 'text-emerald-500' : 'text-[var(--color-text-muted)]'
                }`}
                strokeWidth={activeKey === 'admin' ? 2.2 : 1.6}
              />
              <span className={activeKey === 'admin' ? 'text-[var(--color-text-primary)]' : 'text-[var(--color-text-muted)]'}>
                {language === 'ar' ? 'المدير' : 'Admin'}
              </span>
            </motion.button>
          )}

          {/* Divider */}
          <div className="w-px h-6 bg-[var(--color-border)] mx-1" />

          {/* Ask Osool — search trigger */}
          <motion.button
            onClick={triggerSearch}
            whileHover={{ scale: 1.03 }}
            whileTap={{ scale: 0.97 }}
            className="flex items-center gap-1.5 px-3 py-2 rounded-xl bg-emerald-500/8 border border-emerald-500/15 text-emerald-600 dark:text-emerald-400 hover:border-emerald-500/30 transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-emerald-400/50"
          >
            <Sparkles className="w-3.5 h-3.5" />
            <span className="text-xs font-semibold">
              {language === 'ar' ? 'اسأل أصول' : 'Ask Osool'}
            </span>
            <kbd className="hidden lg:inline-block px-1 py-0.5 text-[9px] font-mono rounded bg-black/5 dark:bg-white/5 border border-emerald-500/10">
              ⌘K
            </kbd>
          </motion.button>

          {/* Notifications */}
          <NotificationBell />

          {/* Theme toggle */}
          <button
            onClick={toggleTheme}
            aria-label={theme === 'dark' ? 'Light mode' : 'Dark mode'}
            className="flex items-center justify-center w-9 h-9 rounded-xl text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)] hover:bg-[var(--color-surface-hover)] transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-emerald-400/50"
          >
            {theme === 'dark' ? <Sun className="w-[18px] h-[18px]" /> : <Moon className="w-[18px] h-[18px]" />}
          </button>

          {/* Language toggle */}
          <button
            onClick={toggleLanguage}
            aria-label={language === 'en' ? 'العربية' : 'English'}
            className="flex items-center justify-center w-9 h-9 rounded-xl text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)] hover:bg-[var(--color-surface-hover)] transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-emerald-400/50"
          >
            <span
              className="text-xs font-bold"
              style={{ fontFamily: language === 'en' ? 'Cairo, sans-serif' : 'Inter, sans-serif' }}
            >
              {language === 'en' ? 'ع' : 'En'}
            </span>
          </button>

          {/* User / Login */}
          {isAuthenticated ? (
            <div className="relative" ref={menuRef}>
              <button
                onClick={() => setUserMenuOpen(!userMenuOpen)}
                aria-label="User menu"
                aria-expanded={userMenuOpen}
                aria-haspopup="true"
                className="flex items-center justify-center w-9 h-9 rounded-xl hover:bg-[var(--color-surface-hover)] transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-emerald-400/50"
              >
                <div className="w-7 h-7 rounded-full bg-gradient-to-br from-emerald-400 to-emerald-600 flex items-center justify-center text-white text-[11px] font-bold">
                  {(user?.full_name || user?.email || 'U').charAt(0).toUpperCase()}
                </div>
              </button>

              {/* Dropdown */}
              <AnimatePresence>
                {userMenuOpen && (
                  <motion.div
                    initial={{ opacity: 0, y: -4, filter: 'blur(4px)' }}
                    animate={{ opacity: 1, y: 0, filter: 'blur(0px)' }}
                    exit={{ opacity: 0, y: -4, filter: 'blur(4px)' }}
                    transition={SPRING_SNAPPY}
                    className="absolute top-full mt-2 end-0 w-56 rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] shadow-xl shadow-black/10 py-1.5 z-50"
                  >
                    <div className="px-4 py-3 border-b border-[var(--color-border)]">
                      <div className="text-sm font-semibold text-[var(--color-text-primary)] truncate">
                        {user?.full_name || 'User'}
                      </div>
                      <div className="text-[11px] text-[var(--color-text-muted)] truncate mt-0.5">
                        {user?.email}
                      </div>
                    </div>
                    <button
                      onClick={() => { setUserMenuOpen(false); onInvite(); }}
                      className="flex items-center gap-2.5 w-full px-4 py-2.5 text-sm text-emerald-600 dark:text-emerald-400 hover:bg-[var(--color-surface-hover)] transition-colors"
                    >
                      <Gift className="w-4 h-4" />
                      {language === 'ar' ? 'دعوة أصدقاء' : 'Invite Friends'}
                    </button>
                    <button
                      onClick={() => { setUserMenuOpen(false); logout(); }}
                      className="flex items-center gap-2.5 w-full px-4 py-2.5 text-sm text-red-500 hover:bg-[var(--color-surface-hover)] transition-colors"
                    >
                      <LogOut className="w-4 h-4" />
                      {language === 'ar' ? 'تسجيل الخروج' : 'Sign Out'}
                    </button>
                  </motion.div>
                )}
              </AnimatePresence>
            </div>
          ) : (
            <Link
              href="/login"
              className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-[var(--color-text-primary)] text-[var(--color-background)] text-xs font-semibold hover:opacity-90 transition-opacity"
            >
              <User className="w-3.5 h-3.5" />
              {language === 'ar' ? 'دخول' : 'Login'}
            </Link>
          )}
        </LayoutGroup>
      </motion.header>

      {/* ════════════════════════════════════════
         MOBILE — Bottom Tab Bar
         ════════════════════════════════════════ */}
      <div className="fixed bottom-0 inset-x-0 z-50 sm:hidden">
        <motion.nav
          initial={{ y: 60 }}
          animate={{ y: 0 }}
          transition={SPRING_SMOOTH}
          aria-label="Mobile navigation"
          className="flex items-end justify-around px-2 pb-[env(safe-area-inset-bottom,8px)] pt-1.5 liquid-glass border-t border-[var(--glass-border)]"
        >
          <LayoutGroup id="mobile-nav">
            {mobileBarItems.map((item) => {
              const Icon = item.icon;
              const isActive = item.key === activeKey;
              return (
                <button
                  key={item.key}
                  onClick={() => router.push(item.href)}
                  aria-label={language === 'ar' ? item.labelAr : item.label}
                  aria-current={isActive ? 'page' : undefined}
                  className="relative flex flex-col items-center gap-0.5 py-2 px-3 min-w-[56px] focus:outline-none focus-visible:ring-2 focus-visible:ring-emerald-400/50 rounded-xl"
                >
                  {isActive && (
                    <motion.div
                      layoutId="mobile-active"
                      className="absolute -top-0.5 left-1/2 -translate-x-1/2 w-5 h-0.5 rounded-full bg-emerald-500"
                      transition={SPRING_SNAPPY}
                    />
                  )}
                  <Icon
                    className={`w-5 h-5 transition-colors ${
                      isActive ? 'text-emerald-500' : 'text-[var(--color-text-muted)]'
                    }`}
                    strokeWidth={isActive ? 2.4 : 1.6}
                  />
                  <span
                    className={`text-[10px] font-medium ${
                      isActive ? 'text-emerald-500' : 'text-[var(--color-text-muted)]'
                    }`}
                  >
                    {language === 'ar' ? item.labelAr : item.label}
                  </span>
                </button>
              );
            })}

            {/* More button */}
            <button
              onClick={() => setMobileOpen(true)}
              aria-label={language === 'ar' ? 'المزيد' : 'More'}
              className="flex flex-col items-center gap-0.5 py-2 px-3 min-w-[56px] focus:outline-none focus-visible:ring-2 focus-visible:ring-emerald-400/50 rounded-xl"
            >
              <Menu className="w-5 h-5 text-[var(--color-text-muted)]" strokeWidth={1.6} />
              <span className="text-[10px] font-medium text-[var(--color-text-muted)]">
                {language === 'ar' ? 'المزيد' : 'More'}
              </span>
            </button>
          </LayoutGroup>
        </motion.nav>
      </div>

      {/* ════════════════════════════════════════
         MOBILE — More Sheet (slide-up overlay)
         ════════════════════════════════════════ */}
      <AnimatePresence>
        {mobileOpen && (
          <>
            {/* Backdrop */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.2 }}
              onClick={() => setMobileOpen(false)}
              className="fixed inset-0 z-[60] bg-black/40 backdrop-blur-sm sm:hidden"
              aria-hidden
            />

            {/* Sheet */}
            <motion.div
              initial={{ y: '100%' }}
              animate={{ y: 0 }}
              exit={{ y: '100%' }}
              transition={SPRING_SMOOTH}
              className="fixed bottom-0 inset-x-0 z-[61] sm:hidden"
              role="dialog"
              aria-modal="true"
              aria-label={language === 'ar' ? 'القائمة' : 'Navigation menu'}
            >
              <div className="rounded-t-3xl liquid-glass border-t border-[var(--glass-border)] p-5 pb-[calc(env(safe-area-inset-bottom,8px)+20px)]">
                {/* Handle */}
                <div className="mx-auto w-9 h-1 rounded-full bg-[var(--color-text-muted)]/30 mb-5" />

                {/* Close */}
                <button
                  onClick={() => setMobileOpen(false)}
                  aria-label="Close"
                  className="absolute top-4 end-4 w-8 h-8 flex items-center justify-center rounded-full bg-[var(--color-surface-hover)] text-[var(--color-text-muted)]"
                >
                  <X className="w-4 h-4" />
                </button>

                {/* All nav items in a grid */}
                <div className="grid grid-cols-4 gap-3 mb-5">
                  {items.map((item) => {
                    const Icon = item.icon;
                    const isActive = item.key === activeKey;
                    return (
                      <button
                        key={item.key}
                        onClick={() => { router.push(item.href); setMobileOpen(false); }}
                        className={`flex flex-col items-center gap-1.5 p-3 rounded-2xl transition-colors ${
                          isActive
                            ? 'bg-emerald-500/10 text-emerald-500'
                            : 'text-[var(--color-text-muted)] hover:bg-[var(--color-surface-hover)]'
                        }`}
                      >
                        <Icon className="w-5 h-5" strokeWidth={isActive ? 2.2 : 1.6} />
                        <span className="text-[11px] font-medium">
                          {language === 'ar' ? item.labelAr : item.label}
                        </span>
                      </button>
                    );
                  })}

                  {isAdmin && (
                    <button
                      onClick={() => { router.push('/admin'); setMobileOpen(false); }}
                      className={`flex flex-col items-center gap-1.5 p-3 rounded-2xl transition-colors ${
                        activeKey === 'admin'
                          ? 'bg-emerald-500/10 text-emerald-500'
                          : 'text-[var(--color-text-muted)] hover:bg-[var(--color-surface-hover)]'
                      }`}
                    >
                      <Shield className="w-5 h-5" strokeWidth={activeKey === 'admin' ? 2.2 : 1.6} />
                      <span className="text-[11px] font-medium">
                        {language === 'ar' ? 'المدير' : 'Admin'}
                      </span>
                    </button>
                  )}
                </div>

                {/* Utilities */}
                <div className="flex items-center gap-2 border-t border-[var(--color-border)] pt-4">
                  {/* Search */}
                  <button
                    onClick={() => { setMobileOpen(false); triggerSearch(); }}
                    className="flex items-center gap-2 flex-1 px-3 py-2.5 rounded-xl bg-[var(--color-surface-hover)] text-[var(--color-text-muted)] text-sm"
                  >
                    <Search className="w-4 h-4" />
                    {language === 'ar' ? 'اسأل أصول...' : 'Ask Osool...'}
                  </button>

                  {/* Theme */}
                  <button
                    onClick={toggleTheme}
                    aria-label={theme === 'dark' ? 'Light mode' : 'Dark mode'}
                    className="flex items-center justify-center w-10 h-10 rounded-xl bg-[var(--color-surface-hover)] text-[var(--color-text-muted)]"
                  >
                    {theme === 'dark' ? <Sun className="w-4.5 h-4.5" /> : <Moon className="w-4.5 h-4.5" />}
                  </button>

                  {/* Language */}
                  <button
                    onClick={toggleLanguage}
                    aria-label={language === 'en' ? 'العربية' : 'English'}
                    className="flex items-center justify-center w-10 h-10 rounded-xl bg-[var(--color-surface-hover)] text-[var(--color-text-muted)] text-xs font-bold"
                  >
                    {language === 'en' ? 'ع' : 'En'}
                  </button>
                </div>

                {/* Auth actions */}
                <div className="mt-3 flex gap-2">
                  {isAuthenticated ? (
                    <>
                      <button
                        onClick={() => { setMobileOpen(false); onInvite(); }}
                        className="flex items-center gap-2 flex-1 px-3 py-2.5 rounded-xl text-sm font-medium text-emerald-600 dark:text-emerald-400 bg-emerald-500/8 border border-emerald-500/15"
                      >
                        <Gift className="w-4 h-4" />
                        {language === 'ar' ? 'دعوة أصدقاء' : 'Invite Friends'}
                      </button>
                      <button
                        onClick={() => { setMobileOpen(false); logout(); }}
                        className="flex items-center gap-2 px-3 py-2.5 rounded-xl text-sm font-medium text-red-500 bg-red-500/8 border border-red-500/15"
                      >
                        <LogOut className="w-4 h-4" />
                        {language === 'ar' ? 'خروج' : 'Sign Out'}
                      </button>
                    </>
                  ) : (
                    <Link
                      href="/login"
                      onClick={() => setMobileOpen(false)}
                      className="flex items-center justify-center gap-2 w-full px-3 py-2.5 rounded-xl text-sm font-semibold text-white bg-emerald-500 hover:bg-emerald-600 transition-colors"
                    >
                      <User className="w-4 h-4" />
                      {language === 'ar' ? 'تسجيل الدخول' : 'Login'}
                    </Link>
                  )}
                </div>
              </div>
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </>
  );
}
