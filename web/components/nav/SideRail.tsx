'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { Sparkles, Search, Sun, Moon, Shield, Gift, LogOut, User } from 'lucide-react';
import { motion } from 'framer-motion';
import { useAuth } from '@/contexts/AuthContext';
import { useTheme } from '@/contexts/ThemeContext';
import { useLanguage } from '@/contexts/LanguageContext';
import { AUTH_NAV, PUBLIC_NAV, getActiveKey } from './nav-items';
import { useState, useRef, useEffect } from 'react';

interface SideRailProps {
  onInvite: () => void;
}

export default function SideRail({ onInvite }: SideRailProps) {
  const pathname = usePathname();
  const { user, isAuthenticated, logout } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const { language, toggleLanguage } = useLanguage();
  const activeKey = getActiveKey(pathname);
  const [userMenuOpen, setUserMenuOpen] = useState(false);
  const menuRef = useRef<HTMLDivElement>(null);

  const items = isAuthenticated ? AUTH_NAV : PUBLIC_NAV;
  const isAdmin = user?.role === 'admin';

  // Close menu on route change
  useEffect(() => {
    setUserMenuOpen(false);
  }, [pathname]);

  // Close on outside click
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
    <aside className="hidden md:flex flex-col items-center w-[60px] h-screen fixed start-0 top-0 z-40 bg-[var(--color-background)]/80 backdrop-blur-2xl border-e border-[var(--color-border)] py-3">
      {/* ── Logo ── */}
      <Link
        href={isAuthenticated ? '/dashboard' : '/'}
        className="flex items-center justify-center w-9 h-9 rounded-xl bg-[var(--color-text-primary)] text-[var(--color-background)] mb-1 hover:scale-105 transition-transform"
        title="Osool.ai"
      >
        <Sparkles className="w-4 h-4" strokeWidth={2.5} />
      </Link>

      {/* ── Search hint (triggers ⌘K) ── */}
      <button
        onClick={() => {
          document.dispatchEvent(
            new KeyboardEvent('keydown', {
              key: 'k',
              ctrlKey: true,
              metaKey: true,
              bubbles: true,
            }),
          );
        }}
        title="Search  ⌘K"
        className="flex items-center justify-center w-10 h-8 rounded-lg text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)] hover:bg-[var(--color-surface-elevated)] transition-colors mb-2"
      >
        <Search className="w-4 h-4" />
      </button>

      {/* ── Main nav ── */}
      <nav className="flex flex-col items-center gap-0.5 flex-1">
        {items.map((item) => {
          const Icon = item.icon;
          const isActive = item.key === activeKey;
          return (
            <Link key={item.key} href={item.href} title={language === 'ar' ? item.labelAr : item.label}>
              <motion.div
                className={`relative flex items-center justify-center w-10 h-10 rounded-xl transition-colors ${
                  isActive
                    ? 'bg-emerald-500/10 text-emerald-500'
                    : 'text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)] hover:bg-[var(--color-surface-elevated)]'
                }`}
                whileHover={{ scale: 1.08 }}
                whileTap={{ scale: 0.95 }}
              >
                {isActive && (
                  <motion.div
                    className="absolute start-0 top-1/2 -translate-y-1/2 -translate-x-[15px] w-[3px] h-5 rounded-full bg-emerald-500"
                    layoutId="rail-indicator"
                    transition={{ type: 'spring', stiffness: 380, damping: 30 }}
                  />
                )}
                <Icon className="w-5 h-5" strokeWidth={isActive ? 2.5 : 1.8} />
              </motion.div>
            </Link>
          );
        })}

        {/* Admin link */}
        {isAdmin && (
          <Link href="/admin" title={language === 'ar' ? 'الإدارة' : 'Admin'} className="mt-2">
            <motion.div
              className={`relative flex items-center justify-center w-10 h-10 rounded-xl transition-colors ${
                activeKey === 'admin'
                  ? 'bg-emerald-500/10 text-emerald-500'
                  : 'text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)] hover:bg-[var(--color-surface-elevated)]'
              }`}
              whileHover={{ scale: 1.08 }}
              whileTap={{ scale: 0.95 }}
            >
              {activeKey === 'admin' && (
                <motion.div
                  className="absolute start-0 top-1/2 -translate-y-1/2 -translate-x-[15px] w-[3px] h-5 rounded-full bg-emerald-500"
                  layoutId="rail-indicator"
                  transition={{ type: 'spring', stiffness: 380, damping: 30 }}
                />
              )}
              <Shield className="w-5 h-5" strokeWidth={activeKey === 'admin' ? 2.5 : 1.8} />
            </motion.div>
          </Link>
        )}
      </nav>

      {/* ── Bottom utilities ── */}
      <div className="flex flex-col items-center gap-0.5 pt-2 mt-2 border-t border-[var(--color-border)]">
        {/* Theme */}
        <button
          onClick={toggleTheme}
          title={theme === 'dark' ? 'Light mode' : 'Dark mode'}
          className="w-10 h-10 rounded-xl flex items-center justify-center text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)] hover:bg-[var(--color-surface-elevated)] transition-colors"
        >
          {theme === 'dark' ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
        </button>

        {/* Language */}
        <button
          onClick={toggleLanguage}
          title={language === 'en' ? 'العربية' : 'English'}
          className="w-10 h-10 rounded-xl flex items-center justify-center text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)] hover:bg-[var(--color-surface-elevated)] transition-colors"
        >
          <span
            className="text-xs font-bold"
            style={{ fontFamily: language === 'en' ? 'Cairo, sans-serif' : 'Inter, sans-serif' }}
          >
            {language === 'en' ? 'ع' : 'En'}
          </span>
        </button>

        {/* User */}
        {isAuthenticated ? (
          <div className="relative" ref={menuRef}>
            <button
              onClick={() => setUserMenuOpen(!userMenuOpen)}
              className="w-10 h-10 rounded-xl flex items-center justify-center hover:bg-[var(--color-surface-elevated)] transition-colors"
              title={user?.full_name || 'Profile'}
            >
              <div className="w-7 h-7 rounded-full bg-gradient-to-br from-emerald-400 to-emerald-600 flex items-center justify-center text-white text-[10px] font-bold">
                {(user?.full_name || user?.email || 'U').charAt(0).toUpperCase()}
              </div>
            </button>

            {userMenuOpen && (
              <motion.div
                initial={{ opacity: 0, x: -8 }}
                animate={{ opacity: 1, x: 0 }}
                transition={{ duration: 0.15 }}
                className="absolute start-full bottom-0 ms-2 w-56 bg-[var(--color-surface)] border border-[var(--color-border)] rounded-2xl shadow-xl shadow-black/10 py-1.5 z-50"
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
                  onClick={() => {
                    setUserMenuOpen(false);
                    onInvite();
                  }}
                  className="flex items-center gap-2.5 w-full px-4 py-2.5 text-sm text-emerald-600 dark:text-emerald-400 hover:bg-[var(--color-surface-elevated)] transition-colors"
                >
                  <Gift className="w-4 h-4" />
                  {language === 'ar' ? 'دعوة أصدقاء' : 'Invite Friends'}
                </button>
                <button
                  onClick={() => {
                    setUserMenuOpen(false);
                    logout();
                  }}
                  className="flex items-center gap-2.5 w-full px-4 py-2.5 text-sm text-red-500 hover:bg-[var(--color-surface-elevated)] transition-colors"
                >
                  <LogOut className="w-4 h-4" />
                  {language === 'ar' ? 'تسجيل الخروج' : 'Sign Out'}
                </button>
              </motion.div>
            )}
          </div>
        ) : (
          <Link
            href="/login"
            title={language === 'ar' ? 'تسجيل الدخول' : 'Sign in'}
            className="w-10 h-10 rounded-xl flex items-center justify-center text-[var(--color-text-muted)] hover:text-emerald-500 hover:bg-emerald-500/10 transition-colors"
          >
            <User className="w-5 h-5" />
          </Link>
        )}
      </div>
    </aside>
  );
}
