'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Sparkles, Search, Sun, Moon, Shield, Gift, LogOut, Menu } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import { useAuth } from '@/contexts/AuthContext';
import { useTheme } from '@/contexts/ThemeContext';
import { useLanguage } from '@/contexts/LanguageContext';
import { AUTH_NAV, PUBLIC_NAV, getActiveKey } from './nav-items';
import { useState, useRef, useEffect } from 'react';
import MoreSheet from './MoreSheet';

interface FloatingHeaderProps {
  onInvite: () => void;
}

export default function FloatingHeader({ onInvite }: FloatingHeaderProps) {
  const pathname = usePathname();
  const { user, isAuthenticated, logout } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const { language, toggleLanguage } = useLanguage();
  const activeKey = getActiveKey(pathname);
  const [userMenuOpen, setUserMenuOpen] = useState(false);
  const [moreOpen, setMoreOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  const items = isAuthenticated ? AUTH_NAV : PUBLIC_NAV;
  const isAdmin = user?.role === 'admin';

  useEffect(() => setUserMenuOpen(false), [pathname]);

  useEffect(() => {
    if (!userMenuOpen) return;
    const handle = (e: MouseEvent) => {
      if (menuRef.current && !menuRef.current.contains(e.target as Node))
        setUserMenuOpen(false);
    };
    document.addEventListener('mousedown', handle);
    return () => document.removeEventListener('mousedown', handle);
  }, [userMenuOpen]);

  return (
    <>
      <header className="fixed top-0 inset-x-0 z-50 flex justify-center px-3 pt-3 pointer-events-none">
        <nav className="pointer-events-auto flex items-center gap-0.5 rounded-2xl bg-[var(--color-surface)]/80 backdrop-blur-2xl border border-[var(--color-border)] shadow-lg shadow-black/[0.04] px-2 py-1.5 w-full max-w-5xl">
          {/* Logo */}
          <Link
            href={isAuthenticated ? '/dashboard' : '/'}
            className="flex items-center justify-center w-9 h-9 rounded-xl bg-[var(--color-text-primary)] text-[var(--color-background)] shrink-0 hover:scale-105 transition-transform"
          >
            <Sparkles className="w-4 h-4" strokeWidth={2.5} />
          </Link>

          {/* Desktop nav links */}
          <div className="hidden md:flex items-center gap-0.5 flex-1 ms-2">
            {items.map((item) => {
              const Icon = item.icon;
              const isActive = item.key === activeKey;
              return (
                <Link
                  key={item.key}
                  href={item.href}
                  className={`relative flex items-center gap-1.5 px-3 py-2 rounded-xl text-sm font-medium transition-colors ${
                    isActive
                      ? 'text-emerald-600 dark:text-emerald-400 bg-emerald-500/10'
                      : 'text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)] hover:bg-[var(--color-surface-elevated)]'
                  }`}
                >
                  <Icon className="w-4 h-4" strokeWidth={isActive ? 2.5 : 1.8} />
                  <span className="hidden lg:inline">
                    {language === 'ar' ? item.labelAr : item.label}
                  </span>
                </Link>
              );
            })}
            {isAdmin && (
              <Link
                href="/admin"
                className={`flex items-center gap-1.5 px-3 py-2 rounded-xl text-sm font-medium transition-colors ${
                  activeKey === 'admin'
                    ? 'text-emerald-600 dark:text-emerald-400 bg-emerald-500/10'
                    : 'text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)] hover:bg-[var(--color-surface-elevated)]'
                }`}
              >
                <Shield className="w-4 h-4" />
              </Link>
            )}
          </div>

          {/* Mobile spacer */}
          <div className="flex-1 md:hidden" />

          {/* Utilities */}
          <div className="flex items-center gap-0.5">
            {/* Search */}
            <button
              onClick={() =>
                document.dispatchEvent(
                  new KeyboardEvent('keydown', { key: 'k', ctrlKey: true, metaKey: true, bubbles: true })
                )
              }
              className="w-9 h-9 rounded-xl flex items-center justify-center text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)] hover:bg-[var(--color-surface-elevated)] transition-colors"
              title="Search ⌘K"
            >
              <Search className="w-4 h-4" />
            </button>

            {/* Theme toggle (hidden on small mobile) */}
            <button
              onClick={toggleTheme}
              className="hidden sm:flex w-9 h-9 rounded-xl items-center justify-center text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)] hover:bg-[var(--color-surface-elevated)] transition-colors"
            >
              {theme === 'dark' ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
            </button>

            {/* Language */}
            <button
              onClick={toggleLanguage}
              className="w-9 h-9 rounded-xl flex items-center justify-center text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)] hover:bg-[var(--color-surface-elevated)] transition-colors"
            >
              <span
                className="text-xs font-bold"
                style={{ fontFamily: language === 'en' ? 'Cairo, sans-serif' : 'Inter, sans-serif' }}
              >
                {language === 'en' ? 'ع' : 'En'}
              </span>
            </button>

            {/* User menu / Login */}
            {isAuthenticated ? (
              <div className="relative" ref={menuRef}>
                <button
                  onClick={() => setUserMenuOpen(!userMenuOpen)}
                  className="w-9 h-9 rounded-xl flex items-center justify-center hover:bg-[var(--color-surface-elevated)] transition-colors"
                >
                  <div className="w-7 h-7 rounded-full bg-gradient-to-br from-emerald-400 to-emerald-600 flex items-center justify-center text-white text-[10px] font-bold">
                    {(user?.full_name || user?.email || 'U').charAt(0).toUpperCase()}
                  </div>
                </button>
                <AnimatePresence>
                  {userMenuOpen && (
                    <motion.div
                      initial={{ opacity: 0, y: -4 }}
                      animate={{ opacity: 1, y: 0 }}
                      exit={{ opacity: 0, y: -4 }}
                      transition={{ duration: 0.15 }}
                      className="absolute end-0 top-full mt-2 w-56 bg-[var(--color-surface)] border border-[var(--color-border)] rounded-2xl shadow-xl shadow-black/10 py-1.5 z-50"
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
              <Link
                href="/login"
                className="hidden sm:flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 text-sm font-semibold hover:bg-emerald-500/20 transition-colors"
              >
                {language === 'ar' ? 'دخول' : 'Login'}
              </Link>
            )}

            {/* Mobile nav button */}
            <button
              onClick={() => setMoreOpen(true)}
              className="md:hidden w-9 h-9 rounded-xl flex items-center justify-center text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)] hover:bg-[var(--color-surface-elevated)] transition-colors"
            >
              <Menu className="w-4 h-4" />
            </button>
          </div>
        </nav>
      </header>

      <MoreSheet open={moreOpen} onClose={() => setMoreOpen(false)} onInvite={onInvite} />
    </>
  );
}
