'use client';

import { AnimatePresence, motion } from 'framer-motion';
import Link from 'next/link';
import { usePathname } from 'next/navigation';
import {
  Sun, Moon, Gift, LogOut, User, Shield, Ticket,
  TrendingUp, Layers, Search, Sparkles,
} from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';
import { useTheme } from '@/contexts/ThemeContext';
import { useLanguage } from '@/contexts/LanguageContext';
import { getActiveKey, type NavItem } from './nav-items';

interface MoreSheetProps {
  open: boolean;
  onClose: () => void;
  onInvite: () => void;
}

export default function MoreSheet({ open, onClose, onInvite }: MoreSheetProps) {
  const pathname = usePathname();
  const { user, isAuthenticated, logout } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const { language, toggleLanguage } = useLanguage();
  const activeKey = getActiveKey(pathname);
  const isAdmin = user?.role === 'admin';

  const extraLinks: NavItem[] = isAuthenticated
    ? [
        { key: 'market', label: 'Market', labelAr: 'السوق', icon: TrendingUp, href: '/market' },
        { key: 'tickets', label: 'Support', labelAr: 'الدعم', icon: Ticket, href: '/tickets' },
        ...(isAdmin
          ? [{ key: 'admin', label: 'Admin', labelAr: 'الإدارة', icon: Shield, href: '/admin' }]
          : []),
      ]
    : [
        { key: 'projects', label: 'Projects', labelAr: 'المشاريع', icon: Layers, href: '/projects' },
      ];

  return (
    <AnimatePresence>
      {open && (
        <>
          {/* Backdrop */}
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            className="fixed inset-0 bg-black/40 backdrop-blur-sm z-50 md:hidden"
            onClick={onClose}
          />

          {/* Sheet */}
          <motion.div
            initial={{ y: '100%' }}
            animate={{ y: 0 }}
            exit={{ y: '100%' }}
            transition={{ type: 'spring', damping: 28, stiffness: 300 }}
            className="fixed bottom-0 left-0 right-0 z-50 md:hidden bg-[var(--color-surface)] border-t border-[var(--color-border)] rounded-t-3xl px-5 pb-8 pt-3"
          >
            {/* Handle */}
            <div className="flex justify-center mb-4">
              <div className="w-10 h-1 rounded-full bg-[var(--color-border)]" />
            </div>

            {/* User info */}
            {isAuthenticated && user && (
              <div className="flex items-center gap-3 mb-5 pb-4 border-b border-[var(--color-border)]">
                <div className="w-10 h-10 rounded-full bg-gradient-to-br from-emerald-400 to-emerald-600 flex items-center justify-center text-white text-sm font-bold">
                  {(user.full_name || user.email || 'U').charAt(0).toUpperCase()}
                </div>
                <div className="flex-1 min-w-0">
                  <div className="text-sm font-semibold text-[var(--color-text-primary)] truncate">
                    {user.full_name || 'User'}
                  </div>
                  <div className="text-xs text-[var(--color-text-muted)] truncate">{user.email}</div>
                </div>
              </div>
            )}

            {/* Nav grid */}
            <div className="grid grid-cols-3 gap-2 mb-5">
              {extraLinks.map((item) => {
                const Icon = item.icon;
                const active = item.key === activeKey;
                return (
                  <Link
                    key={item.key}
                    href={item.href}
                    onClick={onClose}
                    className={`flex flex-col items-center gap-1.5 p-3 rounded-2xl border transition-colors ${
                      active
                        ? 'bg-emerald-500/10 border-emerald-500/20 text-emerald-500'
                        : 'bg-[var(--color-surface-elevated)] border-[var(--color-border)] text-[var(--color-text-muted)]'
                    }`}
                  >
                    <Icon className="w-5 h-5" />
                    <span className="text-xs font-medium">
                      {language === 'ar' ? item.labelAr : item.label}
                    </span>
                  </Link>
                );
              })}

              {/* Search shortcut */}
              <button
                onClick={() => {
                  onClose();
                  setTimeout(() => {
                    document.dispatchEvent(
                      new KeyboardEvent('keydown', {
                        key: 'k',
                        ctrlKey: true,
                        metaKey: true,
                        bubbles: true,
                      }),
                    );
                  }, 200);
                }}
                className="flex flex-col items-center gap-1.5 p-3 rounded-2xl border bg-[var(--color-surface-elevated)] border-[var(--color-border)] text-[var(--color-text-muted)] transition-colors"
              >
                <Search className="w-5 h-5" />
                <span className="text-xs font-medium">
                  {language === 'ar' ? 'بحث' : 'Search'}
                </span>
              </button>
            </div>

            {/* Actions */}
            <div className="space-y-0.5">
              <button
                onClick={() => { toggleTheme(); onClose(); }}
                className="flex items-center gap-3 w-full px-4 py-3 rounded-xl text-[var(--color-text-secondary)] hover:bg-[var(--color-surface-elevated)] transition-colors text-sm"
              >
                {theme === 'dark' ? <Sun className="w-5 h-5" /> : <Moon className="w-5 h-5" />}
                {theme === 'dark'
                  ? (language === 'ar' ? 'الوضع الفاتح' : 'Light mode')
                  : (language === 'ar' ? 'الوضع الداكن' : 'Dark mode')}
              </button>

              <button
                onClick={() => { toggleLanguage(); onClose(); }}
                className="flex items-center gap-3 w-full px-4 py-3 rounded-xl text-[var(--color-text-secondary)] hover:bg-[var(--color-surface-elevated)] transition-colors text-sm"
              >
                <span
                  className="w-5 h-5 flex items-center justify-center text-xs font-bold"
                  style={{ fontFamily: language === 'en' ? 'Cairo, sans-serif' : 'Inter, sans-serif' }}
                >
                  {language === 'en' ? 'ع' : 'En'}
                </span>
                {language === 'en' ? 'العربية' : 'English'}
              </button>

              {isAuthenticated ? (
                <>
                  <button
                    onClick={() => { onClose(); onInvite(); }}
                    className="flex items-center gap-3 w-full px-4 py-3 rounded-xl text-emerald-600 dark:text-emerald-400 hover:bg-emerald-500/10 transition-colors text-sm"
                  >
                    <Gift className="w-5 h-5" />
                    {language === 'ar' ? 'دعوة صديق' : 'Invite Friends'}
                  </button>
                  <button
                    onClick={() => { logout(); onClose(); }}
                    className="flex items-center gap-3 w-full px-4 py-3 rounded-xl text-red-500 hover:bg-red-500/10 transition-colors text-sm"
                  >
                    <LogOut className="w-5 h-5" />
                    {language === 'ar' ? 'تسجيل الخروج' : 'Sign Out'}
                  </button>
                </>
              ) : (
                <>
                  <Link
                    href="/chat"
                    onClick={onClose}
                    className="flex items-center gap-3 w-full px-4 py-3 rounded-xl bg-emerald-500 text-white hover:bg-emerald-600 transition-colors text-sm font-semibold mt-2"
                  >
                    <Sparkles className="w-5 h-5" />
                    {language === 'ar' ? 'ابدأ مع أصول' : 'Start with Osool'}
                  </Link>
                  <Link
                    href="/login"
                    onClick={onClose}
                    className="flex items-center gap-3 w-full px-4 py-3 rounded-xl text-[var(--color-text-secondary)] hover:bg-[var(--color-surface-elevated)] transition-colors text-sm"
                  >
                    <User className="w-5 h-5" />
                    {language === 'ar' ? 'تسجيل الدخول' : 'Sign In'}
                  </Link>
                </>
              )}
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  );
}
