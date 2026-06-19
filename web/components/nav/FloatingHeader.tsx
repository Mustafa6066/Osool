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
import NotificationBell from '@/components/NotificationBell';

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

  const items = (isAuthenticated ? AUTH_NAV : PUBLIC_NAV).slice(0, 4);
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
        <nav
          aria-label="Main navigation"
          className="pointer-events-auto flex items-center gap-0.5 rounded-2xl bg-[var(--osool-surface)]/80 backdrop-blur-xl border border-[var(--osool-border)] shadow-lg shadow-black/[0.04] px-2 py-1.5 w-full max-w-5xl"
        >
          {/* Logo */}
          <Link
            href={isAuthenticated ? '/dashboard' : '/'}
            aria-label="Osool home"
            className="flex h-11 w-11 items-center justify-center rounded-xl bg-[var(--osool-text)] text-[var(--osool-bg)] shrink-0 transition-transform hover:scale-105 focus:outline-none focus-visible:ring-2 focus-visible:ring-[var(--osool-accent)] md:h-9 md:w-9"
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
                  className={`relative flex items-center gap-1.5 px-3 py-2 rounded-xl text-sm font-medium transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-[var(--osool-accent)] ${
                    isActive
                      ? 'text-[var(--osool-accent)] bg-[var(--osool-accent-soft)]'
                      : 'text-[var(--osool-muted)] hover:text-[var(--osool-text)] hover:bg-[var(--osool-surface-2)]'
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
                className={`flex items-center gap-1.5 px-3 py-2 rounded-xl text-sm font-medium transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-[var(--osool-accent)] ${
                  activeKey === 'admin'
                    ? 'text-[var(--osool-accent)] bg-[var(--osool-accent-soft)]'
                    : 'text-[var(--osool-muted)] hover:text-[var(--osool-text)] hover:bg-[var(--osool-surface-2)]'
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
            {/* Notifications */}
            <NotificationBell />

            {/* Search */}
            <button
              onClick={() =>
                document.dispatchEvent(
                  new KeyboardEvent('keydown', { key: 'k', ctrlKey: true, metaKey: true, bubbles: true })
                )
              }
              className="flex h-11 w-11 items-center justify-center rounded-xl text-[var(--osool-muted)] transition-colors hover:bg-[var(--osool-surface-2)] hover:text-[var(--osool-text)] focus:outline-none focus-visible:ring-2 focus-visible:ring-[var(--osool-accent)] md:h-9 md:w-9"
              aria-label="Search (Ctrl+K)"
            >
              <Search className="w-4 h-4" />
            </button>

            {/* Theme toggle (hidden on small mobile) */}
            <button
              onClick={toggleTheme}
              aria-label={theme === 'dark' ? 'Switch to light mode' : 'Switch to dark mode'}
              className="hidden sm:flex h-11 w-11 items-center justify-center rounded-xl text-[var(--osool-muted)] transition-colors hover:bg-[var(--osool-surface-2)] hover:text-[var(--osool-text)] focus:outline-none focus-visible:ring-2 focus-visible:ring-[var(--osool-accent)] md:h-9 md:w-9"
            >
              {theme === 'dark' ? <Sun className="w-4 h-4" /> : <Moon className="w-4 h-4" />}
            </button>

            {/* Language */}
            <button
              onClick={toggleLanguage}
              aria-label={language === 'en' ? 'Switch to Arabic' : 'Switch to English'}
              className="flex h-11 w-11 items-center justify-center rounded-xl text-[var(--osool-muted)] transition-colors hover:bg-[var(--osool-surface-2)] hover:text-[var(--osool-text)] focus:outline-none focus-visible:ring-2 focus-visible:ring-[var(--osool-accent)] md:h-9 md:w-9"
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
                  aria-label="User menu"
                  aria-expanded={userMenuOpen}
                  aria-haspopup="true"
                  className="flex h-11 w-11 items-center justify-center rounded-xl transition-colors hover:bg-[var(--osool-surface-2)] focus:outline-none focus-visible:ring-2 focus-visible:ring-[var(--osool-accent)] md:h-9 md:w-9"
                >
                  <div className="w-7 h-7 rounded-full bg-gradient-to-br from-[var(--osool-accent)] to-[var(--osool-accent-dark)] flex items-center justify-center text-white text-[10px] font-bold">
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
                      className="absolute end-0 top-full mt-2 w-56 bg-[var(--osool-surface)] border border-[var(--osool-border)] rounded-2xl shadow-xl shadow-black/10 py-1.5 z-50"
                    >
                      <div className="px-4 py-3 border-b border-[var(--osool-border)]">
                        <div className="text-sm font-semibold text-[var(--osool-text)] truncate">
                          {user?.full_name || 'User'}
                        </div>
                        <div className="text-[11px] text-[var(--osool-muted)] truncate mt-0.5">
                          {user?.email}
                        </div>
                      </div>
                      <button
                        onClick={() => { setUserMenuOpen(false); onInvite(); }}
                        className="flex items-center gap-2.5 w-full px-4 py-2.5 text-sm text-[var(--osool-accent)] hover:bg-[var(--osool-surface-2)] transition-colors"
                      >
                        <Gift className="w-4 h-4" />
                        {language === 'ar' ? 'دعوة أصدقاء' : 'Invite Friends'}
                      </button>
                      <button
                        onClick={() => { setUserMenuOpen(false); logout(); }}
                        className="flex items-center gap-2.5 w-full px-4 py-2.5 text-sm text-[var(--osool-danger)] hover:bg-[var(--osool-surface-2)] transition-colors"
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
                className="hidden sm:flex items-center gap-1.5 px-3.5 py-2 rounded-xl bg-[var(--osool-accent)] text-white text-sm font-semibold hover:bg-[var(--osool-accent-dark)] transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-[var(--osool-accent)]"
              >
                {language === 'ar' ? 'دخول' : 'Login'}
              </Link>
            )}

            {/* Mobile nav button */}
            <button
              onClick={() => setMoreOpen(true)}
              aria-label="Open navigation menu"
              className="flex h-11 w-11 items-center justify-center rounded-xl text-[var(--osool-muted)] transition-colors hover:bg-[var(--osool-surface-2)] hover:text-[var(--osool-text)] focus:outline-none focus-visible:ring-2 focus-visible:ring-[var(--osool-accent)] md:hidden"
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
