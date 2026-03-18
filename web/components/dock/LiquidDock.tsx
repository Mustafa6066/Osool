'use client';

import React, { useState, useRef, useEffect } from 'react';
import { usePathname, useRouter } from 'next/navigation';
import { motion, AnimatePresence, LayoutGroup } from 'framer-motion';
import { Sparkles, Sun, Moon, Gift, LogOut, User, Shield, Search } from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';
import { useTheme } from '@/contexts/ThemeContext';
import { useLanguage } from '@/contexts/LanguageContext';
import { useGamification } from '@/contexts/GamificationContext';
import { AUTH_NAV, PUBLIC_NAV, getActiveKey, type NavItem } from '@/components/nav/nav-items';
import NotificationBell from '@/components/NotificationBell';
import DockContextPanel from './DockContextPanel';

/* ─── types ──────────────────────────────────────── */
interface LiquidDockProps {
  onInvite: () => void;
}

/* ─── component ──────────────────────────────────── */
export default function LiquidDock({ onInvite }: LiquidDockProps) {
  const pathname = usePathname();
  const router = useRouter();
  const { user, isAuthenticated, logout } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const { language, toggleLanguage } = useLanguage();
  const { xpQueue, achievementQueue } = useGamification();
  const activeKey = getActiveKey(pathname);

  const [hoveredIndex, setHoveredIndex] = useState<number | null>(null);
  const [userMenuOpen, setUserMenuOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  const items: NavItem[] = isAuthenticated ? AUTH_NAV : PUBLIC_NAV;
  const isAdmin = user?.role === 'admin';
  const hasAlerts = xpQueue.length > 0 || achievementQueue.length > 0;

  // Close user menu on route change
  useEffect(() => { setUserMenuOpen(false); }, [pathname]);

  // Outside‑click for user menu
  useEffect(() => {
    if (!userMenuOpen) return;
    const h = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node)) setUserMenuOpen(false);
    };
    document.addEventListener('mousedown', h);
    return () => document.removeEventListener('mousedown', h);
  }, [userMenuOpen]);

  return (
    <>
      {/* ── Context panel (slides UP from dock) ── */}
      <DockContextPanel />

      {/* ── Dock ── */}
      <div className="fixed bottom-4 sm:bottom-6 start-1/2 rtl:translate-x-1/2 ltr:-translate-x-1/2 z-50 max-w-[96vw] sm:max-w-fit">
        {/* Breath indicator — glow ring behind dock when alerts pending */}
        {hasAlerts && (
          <div
            className="absolute -inset-1 rounded-[28px] opacity-40 pointer-events-none animate-[breath_3s_ease-in-out_infinite]"
            style={{
              background: 'radial-gradient(ellipse at center, rgba(16,185,129,0.35) 0%, transparent 70%)',
            }}
          />
        )}

        <LayoutGroup>
          <motion.nav
            aria-label="Main navigation"
            className="relative flex items-center gap-1 sm:gap-1.5 px-2 sm:px-3 py-2 sm:py-2.5 rounded-2xl liquid-glass dock-shadow"
            initial={{ y: 80, opacity: 0 }}
            animate={{ y: 0, opacity: 1 }}
            transition={{ type: 'spring', damping: 22, stiffness: 120, delay: 0.1 }}
          >
            {/* ── Nav items ── */}
            {items.map((item, i) => {
              const Icon = item.icon;
              const isActive = item.key === activeKey;
              return (
                <motion.button
                  key={item.key}
                  onClick={() => router.push(item.href)}
                  onHoverStart={() => setHoveredIndex(i)}
                  onHoverEnd={() => setHoveredIndex(null)}
                  aria-label={language === 'ar' ? item.labelAr : item.label}
                  aria-current={isActive ? 'page' : undefined}
                  className={`relative overflow-hidden flex items-center justify-center h-[52px] sm:h-11 rounded-2xl focus:outline-none focus-visible:ring-2 focus-visible:ring-emerald-400/50 transition-all duration-300 ease-out ${isActive ? 'w-[100px] sm:w-[120px] px-3' : 'w-[52px] sm:w-11 px-0'}`}
                  animate={{
                    scale: hoveredIndex === i ? 1.18 : isActive ? 1.06 : 1,
                  }}
                  transition={{ type: 'spring', bounce: 0.35, duration: 0.35 }}
                >
                  {/* Active blob */}
                  {isActive && (
                    <motion.div
                      layoutId="dockActiveBlob"
                      className="absolute inset-0 rounded-2xl bg-emerald-500/15 -z-10"
                      transition={{ type: 'spring', bounce: 0.35, duration: 0.35 }}
                    />
                  )}

                  <div className="flex items-center gap-2">
                    <Icon
                      className={`w-[22px] h-[22px] transition-colors duration-200 ${
                        isActive
                          ? 'text-emerald-500'
                          : 'text-[var(--color-text-muted)] group-hover:text-[var(--color-text-primary)]'
                      }`}
                      strokeWidth={isActive ? 2.4 : 1.6}
                    />
                    <AnimatePresence>
                      {isActive && (
                        <motion.span
                          initial={{ width: 0, opacity: 0 }}
                          animate={{ width: 'auto', opacity: 1 }}
                          exit={{ width: 0, opacity: 0 }}
                          transition={{ duration: 0.2 }}
                          className="overflow-hidden whitespace-nowrap text-sm font-medium text-[var(--color-text-primary)]"
                        >
                          {language === 'ar' ? item.labelAr : item.label}
                        </motion.span>
                      )}
                    </AnimatePresence>
                  </div>

                  {/* Tooltip */}
                  <AnimatePresence>
                    {hoveredIndex === i && (
                      <motion.span
                        initial={{ opacity: 0, y: 8, scale: 0.85 }}
                        animate={{ opacity: 1, y: -44, scale: 1 }}
                        exit={{ opacity: 0, y: 8, scale: 0.85 }}
                        transition={{ type: 'spring', damping: 20, stiffness: 300 }}
                        className="absolute start-1/2 rtl:translate-x-1/2 ltr:-translate-x-1/2 whitespace-nowrap px-2.5 py-1 rounded-xl text-[11px] font-medium text-white bg-black/80 backdrop-blur-md border border-white/10 pointer-events-none z-10"
                      >
                        {language === 'ar' ? item.labelAr : item.label}
                      </motion.span>
                    )}
                  </AnimatePresence>
                </motion.button>
              );
            })}

            {/* Admin shortcut */}
            {isAdmin && (
              <motion.button
                onClick={() => router.push('/admin')}
                aria-label="Admin"
                className={`relative overflow-hidden flex items-center justify-center h-[52px] sm:h-11 rounded-2xl focus:outline-none focus-visible:ring-2 focus-visible:ring-emerald-400/50 transition-all duration-300 ease-out ${activeKey === 'admin' ? 'w-[100px] sm:w-[120px] px-3' : 'w-[52px] sm:w-11 px-0'}`}
                whileHover={{ scale: 1.12 }}
                whileTap={{ scale: 0.95 }}
                transition={{ type: 'spring', bounce: 0.35, duration: 0.35 }}
              >
                {activeKey === 'admin' && (
                  <motion.div
                    layoutId="dockActiveBlob"
                    className="absolute inset-0 rounded-2xl bg-emerald-500/15 -z-10"
                    transition={{ type: 'spring', bounce: 0.35, duration: 0.35 }}
                  />
                )}
                <div className="flex items-center gap-2">
                  <Shield
                    className={`w-[22px] h-[22px] transition-colors duration-200 ${
                      activeKey === 'admin' ? 'text-emerald-500' : 'text-[var(--color-text-muted)]'
                    }`}
                    strokeWidth={activeKey === 'admin' ? 2.4 : 1.6}
                  />
                  <AnimatePresence>
                    {activeKey === 'admin' && (
                      <motion.span
                        initial={{ width: 0, opacity: 0 }}
                        animate={{ width: 'auto', opacity: 1 }}
                        exit={{ width: 0, opacity: 0 }}
                        transition={{ duration: 0.2 }}
                        className="overflow-hidden whitespace-nowrap text-sm font-medium text-[var(--color-text-primary)]"
                      >
                        {language === 'ar' ? 'المدير' : 'Admin'}
                      </motion.span>
                    )}
                  </AnimatePresence>
                </div>
              </motion.button>
            )}

            {/* ── Divider ── */}
            <div className="w-[1px] h-7 bg-[var(--color-text-muted)]/15 mx-0.5 sm:mx-1 shrink-0" />

            {/* ── Ask Osool (triggers Cmd+K) ── */}
            <motion.button
              onClick={() =>
                document.dispatchEvent(
                  new KeyboardEvent('keydown', {
                    key: 'k',
                    ctrlKey: true,
                    metaKey: true,
                    bubbles: true,
                  })
                )
              }
              whileHover={{ scale: 1.06 }}
              whileTap={{ scale: 0.95 }}
              className="hidden sm:flex items-center gap-1.5 px-3 py-2 rounded-2xl bg-gradient-to-r from-emerald-500/15 to-teal-500/15 border border-emerald-500/20 text-emerald-600 dark:text-emerald-400 hover:border-emerald-500/40 transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-emerald-400/50"
            >
              <Sparkles className="w-4 h-4" />
              <span className="text-xs font-semibold">
                {language === 'ar' ? 'اسأل أصول' : 'Ask Osool'}
              </span>
              <kbd className="hidden lg:inline-block px-1 py-0.5 text-[9px] font-mono rounded bg-black/10 dark:bg-white/5 text-emerald-600/60 dark:text-emerald-400/60 border border-emerald-500/10">
                ⌘K
              </kbd>
            </motion.button>

            {/* Mobile search (triggers Cmd+K) */}
            <motion.button
              onClick={() =>
                document.dispatchEvent(
                  new KeyboardEvent('keydown', {
                    key: 'k',
                    ctrlKey: true,
                    metaKey: true,
                    bubbles: true,
                  })
                )
              }
              whileHover={{ scale: 1.1 }}
              whileTap={{ scale: 0.95 }}
              aria-label="Search"
              className="sm:hidden flex items-center justify-center w-11 h-11 rounded-2xl text-[var(--color-text-muted)] hover:text-emerald-500 transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-emerald-400/50"
            >
              <Search className="w-5 h-5" />
            </motion.button>

            {/* ── Divider ── */}
            <div className="w-[1px] h-7 bg-[var(--color-text-muted)]/15 mx-0.5 sm:mx-1 shrink-0" />

            {/* ── Utilities ── */}

            {/* Notifications */}
            <NotificationBell />

            {/* Theme */}
            <button
              onClick={toggleTheme}
              aria-label={theme === 'dark' ? 'Light mode' : 'Dark mode'}
              className="hidden sm:flex items-center justify-center w-11 h-11 rounded-2xl text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)] hover:bg-[var(--color-surface-elevated)]/50 transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-emerald-400/50"
            >
              {theme === 'dark' ? <Sun className="w-[22px] h-[22px]" /> : <Moon className="w-[22px] h-[22px]" />}
            </button>

            {/* Language */}
            <button
              onClick={toggleLanguage}
              aria-label={language === 'en' ? 'العربية' : 'English'}
              className="hidden sm:flex items-center justify-center w-11 h-11 rounded-2xl text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)] hover:bg-[var(--color-surface-elevated)]/50 transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-emerald-400/50"
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
                  className="flex items-center justify-center w-11 h-11 rounded-2xl hover:bg-[var(--color-surface-elevated)]/50 transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-emerald-400/50"
                >
                  <div className="w-8 h-8 rounded-full bg-gradient-to-br from-emerald-400 to-emerald-600 flex items-center justify-center text-white text-xs font-bold">
                    {(user?.full_name || user?.email || 'U').charAt(0).toUpperCase()}
                  </div>
                </button>

                <AnimatePresence>
                  {userMenuOpen && (
                    <motion.div
                      initial={{ opacity: 0, y: 8, filter: 'blur(4px)' }}
                      animate={{ opacity: 1, y: 0, filter: 'blur(0px)' }}
                      exit={{ opacity: 0, y: 8, filter: 'blur(4px)' }}
                      transition={{ type: 'spring', damping: 24, stiffness: 250 }}
                      className="absolute bottom-full mb-2 end-0 w-56 rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] shadow-xl shadow-black/10 py-1.5 z-50"
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
                        className="flex items-center gap-2.5 w-full px-4 py-2.5 text-sm text-emerald-600 dark:text-emerald-400 hover:bg-[var(--color-surface-elevated)] transition-colors"
                      >
                        <Gift className="w-4 h-4" />
                        {language === 'ar' ? 'دعوة أصدقاء' : 'Invite Friends'}
                      </button>
                      <button
                        onClick={() => { toggleTheme(); setUserMenuOpen(false); }}
                        className="flex items-center gap-2.5 w-full px-4 py-2.5 text-sm text-[var(--color-text-primary)] hover:bg-[var(--color-surface-elevated)] transition-colors sm:hidden"
                      >
                        {theme === 'dark' ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
                        {theme === 'dark' ? (language === 'ar' ? 'الوضع الفاتح' : 'Light mode') : (language === 'ar' ? 'الوضع الداكن' : 'Dark mode')}
                      </button>
                      <button
                        onClick={() => { toggleLanguage(); setUserMenuOpen(false); }}
                        className="flex items-center gap-2.5 w-full px-4 py-2.5 text-sm text-[var(--color-text-primary)] hover:bg-[var(--color-surface-elevated)] transition-colors sm:hidden"
                      >
                        <span className="text-xs font-bold w-4 text-center">
                          {language === 'en' ? 'ع' : 'En'}
                        </span>
                        {language === 'en' ? 'العربية' : 'English'}
                      </button>
                      <button
                        onClick={() => { setUserMenuOpen(false); logout(); }}
                        className="flex items-center gap-2.5 w-full px-4 py-2.5 text-sm text-red-500 hover:bg-[var(--color-surface-elevated)] transition-colors"
                      >
                        <LogOut className="w-4 h-4" />
                        {language === 'ar' ? 'تسجيل الخروج' : 'Sign Out'}
                      </button>
                    </motion.div>
                  )}
                </AnimatePresence>
              </div>
            ) : (
              <motion.button
                onClick={() => router.push('/login')}
                whileHover={{ scale: 1.05 }}
                whileTap={{ scale: 0.95 }}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-xl bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 text-xs font-semibold hover:bg-emerald-500/20 transition-colors"
              >
                <User className="w-3.5 h-3.5" />
                <span className="hidden sm:inline">
                  {language === 'ar' ? 'دخول' : 'Login'}
                </span>
              </motion.button>
            )}
          </motion.nav>
        </LayoutGroup>
      </div>
    </>
  );
}
