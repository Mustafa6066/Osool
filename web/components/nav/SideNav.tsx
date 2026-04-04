'use client';

import React, { useState, useEffect, useRef, useCallback } from 'react';
import Link from 'next/link';
import { usePathname, useRouter } from 'next/navigation';
import { motion, AnimatePresence, useReducedMotion } from 'framer-motion';
import {
  Sparkles, Sun, Moon, LogOut, Shield, Languages, Gift,
  LogIn, Settings, ChevronRight, Menu, X,
} from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';
import { useTheme } from '@/contexts/ThemeContext';
import { useLanguage } from '@/contexts/LanguageContext';
import {
  AUTH_NAV_PRIMARY, AUTH_NAV_SECONDARY,
  PUBLIC_NAV, getActiveKey, type NavItem,
} from '@/components/nav/nav-items';
import NotificationBell from '@/components/NotificationBell';

/* ─── Constants ─────────────────────────────── */
const SPRING = { type: 'spring' as const, damping: 28, stiffness: 240 };
const EASE_OUT = { duration: 0.18, ease: [0.16, 1, 0.3, 1] as const };
const MOBILE_HIDE_THRESHOLD = 10;

/* ─── Types ──────────────────────────────────── */
interface SideNavProps {
  onInvite: () => void;
}

/* ─── Tooltip ─────────────────────────────────── */
function Tooltip({ label, isRTL }: { label: string; isRTL: boolean }) {
  return (
    <motion.div
      initial={{ opacity: 0, x: isRTL ? 8 : -8 }}
      animate={{ opacity: 1, x: 0 }}
      exit={{ opacity: 0, x: isRTL ? 8 : -8 }}
      transition={EASE_OUT}
      className={`pointer-events-none absolute top-1/2 -translate-y-1/2 z-[200] whitespace-nowrap ${
        isRTL ? 'right-full mr-3' : 'left-full ml-3'
      }`}
    >
      <span className="rounded-lg bg-[var(--color-text-primary)] px-2.5 py-1.5 text-[12px] font-medium text-[var(--color-background)] shadow-lg">
        {label}
      </span>
    </motion.div>
  );
}

/* ─── NavItem Button ─────────────────────────── */
function SideNavItem({
  item,
  isActive,
  isExpanded,
  isRTL,
  onClick,
}: {
  item: NavItem;
  isActive: boolean;
  isExpanded: boolean;
  isRTL: boolean;
  onClick?: () => void;
}) {
  const { language } = useLanguage();
  const [showTooltip, setShowTooltip] = useState(false);
  const label = language === 'ar' ? item.labelAr : item.label;
  const Icon = item.icon;

  const inner = (
    <div
      className={`relative flex h-10 w-full items-center rounded-xl transition-all duration-150 ${
        isExpanded ? 'px-3 gap-3' : 'justify-center'
      } ${
        isActive
          ? 'bg-emerald-500/12 text-emerald-600 dark:text-emerald-400'
          : 'text-[var(--color-text-muted)] hover:bg-[var(--color-surface-elevated)] hover:text-[var(--color-text-primary)]'
      }`}
      onMouseEnter={() => !isExpanded && setShowTooltip(true)}
      onMouseLeave={() => setShowTooltip(false)}
    >
      {/* Active left indicator */}
      {isActive && (
        <motion.span
          layoutId="nav-active-bar"
          className={`absolute inset-y-2 w-0.5 rounded-full bg-emerald-500 ${
            isRTL ? 'right-0' : 'left-0'
          }`}
          transition={SPRING}
        />
      )}

      <Icon
        className="h-[18px] w-[18px] shrink-0"
        strokeWidth={isActive ? 2.4 : 1.8}
      />

      <AnimatePresence>
        {isExpanded && (
          <motion.span
            initial={{ opacity: 0, width: 0 }}
            animate={{ opacity: 1, width: 'auto' }}
            exit={{ opacity: 0, width: 0 }}
            transition={EASE_OUT}
            className="overflow-hidden whitespace-nowrap text-[13px] font-medium"
          >
            {label}
          </motion.span>
        )}
      </AnimatePresence>

      {/* Tooltip when collapsed */}
      <AnimatePresence>
        {showTooltip && !isExpanded && (
          <Tooltip label={label} isRTL={isRTL} />
        )}
      </AnimatePresence>
    </div>
  );

  if (onClick) {
    return (
      <button
        onClick={onClick}
        className="w-full"
        aria-label={label}
        title={label}
      >
        {inner}
      </button>
    );
  }

  return (
    <Link href={item.href} className="w-full" aria-label={label} title={label}>
      {inner}
    </Link>
  );
}

/* ─── Icon-only action button ────────────────── */
function SideActionButton({
  icon: Icon,
  label,
  onClick,
  isExpanded,
  isRTL,
  children,
}: {
  icon: React.ElementType;
  label: string;
  onClick?: () => void;
  isExpanded: boolean;
  isRTL: boolean;
  children?: React.ReactNode;
}) {
  const [showTooltip, setShowTooltip] = useState(false);

  return (
    <div className="relative w-full">
      <button
        onClick={onClick}
        aria-label={label}
        title={label}
        onMouseEnter={() => !isExpanded && setShowTooltip(true)}
        onMouseLeave={() => setShowTooltip(false)}
        className={`flex h-10 w-full items-center rounded-xl text-[var(--color-text-muted)] hover:bg-[var(--color-surface-elevated)] hover:text-[var(--color-text-primary)] transition-colors ${
          isExpanded ? 'px-3 gap-3' : 'justify-center'
        }`}
      >
        <Icon className="h-[18px] w-[18px] shrink-0" strokeWidth={1.8} />
        <AnimatePresence>
          {isExpanded && (
            <motion.span
              initial={{ opacity: 0, width: 0 }}
              animate={{ opacity: 1, width: 'auto' }}
              exit={{ opacity: 0, width: 0 }}
              transition={EASE_OUT}
              className="overflow-hidden whitespace-nowrap text-[13px] font-medium"
            >
              {label}
            </motion.span>
          )}
        </AnimatePresence>
        {children}
      </button>
      <AnimatePresence>
        {showTooltip && !isExpanded && (
          <Tooltip label={label} isRTL={isRTL} />
        )}
      </AnimatePresence>
    </div>
  );
}

/* ─── Avatar Button ───────────────────────────── */
function AvatarButton({
  user,
  isExpanded,
  isRTL,
  onOpenMenu,
}: {
  user: { full_name?: string; email?: string } | null;
  isExpanded: boolean;
  isRTL: boolean;
  onOpenMenu: () => void;
}) {
  const initials = user?.full_name
    ? user.full_name.split(' ').map((n) => n[0]).slice(0, 2).join('').toUpperCase()
    : '?';

  return (
    <button
      onClick={onOpenMenu}
      aria-label="User menu"
      className={`flex h-10 w-full items-center rounded-xl hover:bg-[var(--color-surface-elevated)] transition-colors ${
        isExpanded ? 'px-3 gap-3' : 'justify-center'
      }`}
    >
      <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full bg-emerald-500/20 text-[11px] font-bold text-emerald-600 dark:text-emerald-400 ring-1 ring-emerald-500/30">
        {initials}
      </span>
      <AnimatePresence>
        {isExpanded && (
          <motion.div
            initial={{ opacity: 0, width: 0 }}
            animate={{ opacity: 1, width: 'auto' }}
            exit={{ opacity: 0, width: 0 }}
            transition={EASE_OUT}
            className="flex min-w-0 flex-1 flex-col overflow-hidden text-start"
          >
            <span className="truncate text-[12px] font-semibold text-[var(--color-text-primary)] leading-tight">
              {user?.full_name ?? 'Account'}
            </span>
            <span className="truncate text-[11px] text-[var(--color-text-muted)] leading-tight">
              {user?.email ?? ''}
            </span>
          </motion.div>
        )}
      </AnimatePresence>
      {isExpanded && (
        <ChevronRight className="h-3.5 w-3.5 shrink-0 text-[var(--color-text-muted)] ml-auto" />
      )}
    </button>
  );
}

/* ─── User Dropdown ───────────────────────────── */
function UserDropdown({
  isRTL,
  language,
  onInvite,
  onLogout,
  onClose,
}: {
  isRTL: boolean;
  language: string;
  onInvite: () => void;
  onLogout: () => void;
  onClose: () => void;
}) {
  const ref = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const handler = (e: MouseEvent) => {
      if (ref.current && !ref.current.contains(e.target as Node)) onClose();
    };
    document.addEventListener('mousedown', handler);
    return () => document.removeEventListener('mousedown', handler);
  }, [onClose]);

  const items = [
    { label: language === 'ar' ? 'الإعدادات' : 'Settings', icon: Settings, href: '/settings' },
    { label: language === 'ar' ? 'دعوة صديق' : 'Invite a friend', icon: Gift, onClick: onInvite },
    { label: language === 'ar' ? 'تسجيل الخروج' : 'Sign out', icon: LogOut, onClick: onLogout, danger: true },
  ];

  return (
    <motion.div
      ref={ref}
      initial={{ opacity: 0, scale: 0.95, y: 8 }}
      animate={{ opacity: 1, scale: 1, y: 0 }}
      exit={{ opacity: 0, scale: 0.95, y: 8 }}
      transition={EASE_OUT}
      className={`absolute bottom-14 z-[200] w-[200px] rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] shadow-xl ${
        isRTL ? 'right-2' : 'left-2'
      }`}
    >
      <div className="p-1.5">
        {items.map((item) => {
          const Icon = item.icon;
          const inner = (
            <div className={`flex items-center gap-3 rounded-xl px-3 py-2.5 text-[13px] font-medium transition-colors ${
              item.danger
                ? 'text-red-500 hover:bg-red-500/8'
                : 'text-[var(--color-text-primary)] hover:bg-[var(--color-surface-elevated)]'
            }`}>
              <Icon className="h-4 w-4 shrink-0" strokeWidth={1.8} />
              {item.label}
            </div>
          );

          if ('href' in item && item.href) {
            return (
              <Link key={item.label} href={item.href} onClick={onClose}>
                {inner}
              </Link>
            );
          }
          return (
            <button
              key={item.label}
              className="w-full text-start"
              onClick={() => { item.onClick?.(); onClose(); }}
            >
              {inner}
            </button>
          );
        })}
      </div>
    </motion.div>
  );
}

/* ─── Divider ─────────────────────────────────── */
function NavDivider() {
  return <div className="my-1 h-px bg-[var(--color-border)]" />;
}

/* ═══════════════════════════════════════════════
   MAIN COMPONENT
   ═══════════════════════════════════════════════ */
export default function SideNav({ onInvite }: SideNavProps) {
  const pathname = usePathname();
  const router = useRouter();
  const { user, isAuthenticated, logout } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const { language, toggleLanguage } = useLanguage();

  const activeKey = getActiveKey(pathname);
  const isRTL = language === 'ar';
  const isAdmin = user?.role === 'admin';
  const primaryItems = isAuthenticated ? AUTH_NAV_PRIMARY : PUBLIC_NAV;
  const secondaryItems = isAuthenticated ? AUTH_NAV_SECONDARY : [];

  const [isExpanded, setIsExpanded] = useState(false);
  const [showUserMenu, setShowUserMenu] = useState(false);
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);
  const [mobileNavVisible, setMobileNavVisible] = useState(true);
  const [mounted, setMounted] = useState(false);
  const lastScrollTopRef = useRef(0);
  const prefersReducedMotion = useReducedMotion();

  useEffect(() => { setMounted(true); }, []);
  // Close on route change
  useEffect(() => {
    setMobileMenuOpen(false);
    setShowUserMenu(false);
    setMobileNavVisible(true);
  }, [pathname]);

  useEffect(() => {
    if (!mounted) return;

    const isMobileViewport = () => window.matchMedia('(max-width: 1023px)').matches;

    const updateVisibility = (nextScrollTop: number) => {
      const clampedTop = Math.max(0, nextScrollTop);
      const delta = clampedTop - lastScrollTopRef.current;

      if (clampedTop <= 16) {
        setMobileNavVisible(true);
        lastScrollTopRef.current = clampedTop;
        return;
      }

      if (Math.abs(delta) < MOBILE_HIDE_THRESHOLD) {
        return;
      }

      setMobileNavVisible(delta < 0);
      lastScrollTopRef.current = clampedTop;
    };

    const handleScroll = (event: Event) => {
      if (!isMobileViewport() || mobileMenuOpen) {
        return;
      }

      const target = event.target;
      if (target instanceof HTMLElement) {
        updateVisibility(target.scrollTop);
        return;
      }

      updateVisibility(window.scrollY || document.documentElement.scrollTop || 0);
    };

    const handleResize = () => {
      if (!isMobileViewport()) {
        setMobileNavVisible(true);
      }
    };

    lastScrollTopRef.current = window.scrollY || document.documentElement.scrollTop || 0;

    document.addEventListener('scroll', handleScroll, { capture: true, passive: true });
    window.addEventListener('resize', handleResize);

    return () => {
      document.removeEventListener('scroll', handleScroll, true);
      window.removeEventListener('resize', handleResize);
    };
  }, [mounted, mobileMenuOpen]);

  useEffect(() => {
    if (mobileMenuOpen) {
      setMobileNavVisible(true);
    }
  }, [mobileMenuOpen]);

  const handleLogout = useCallback(() => {
    logout();
    router.push('/');
  }, [logout, router]);

  if (!mounted) return null;

  /* ── Mobile items (bottom 5) ── */
  const mobileItems: NavItem[] = isAuthenticated
    ? [AUTH_NAV_PRIMARY[0], AUTH_NAV_PRIMARY[1], AUTH_NAV_SECONDARY[1], AUTH_NAV_SECONDARY[2]]
    : [PUBLIC_NAV[0], PUBLIC_NAV[1], PUBLIC_NAV[2], PUBLIC_NAV[3]];

  return (
    <>
      {/* ╔══════════════════════════════╗
          ║  DESKTOP SIDEBAR (lg+)       ║
          ╚══════════════════════════════╝ */}
      <motion.nav
        onMouseEnter={() => setIsExpanded(true)}
        onMouseLeave={() => { setIsExpanded(false); setShowUserMenu(false); }}
        animate={{ width: isExpanded ? 220 : 56 }}
        transition={SPRING}
        className={`hidden lg:flex fixed top-0 bottom-0 z-50 flex-col overflow-hidden
                    border-[var(--color-border)] bg-[var(--color-surface)]/95 backdrop-blur-2xl
                    shadow-[1px_0_0_0_var(--color-border)]
                    ${isRTL ? 'right-0 border-l' : 'left-0 border-r'}`}
      >
        {/* Brand */}
        <div className={`flex h-[60px] shrink-0 items-center border-b border-[var(--color-border)] ${
          isExpanded ? 'px-4 gap-3' : 'justify-center'
        }`}>
          <div className="flex h-8 w-8 shrink-0 items-center justify-center rounded-xl bg-emerald-500/15 ring-1 ring-emerald-500/25">
            <Sparkles className="h-4 w-4 text-emerald-500" strokeWidth={2} />
          </div>
          <AnimatePresence>
            {isExpanded && (
              <motion.div
                initial={{ opacity: 0, width: 0 }}
                animate={{ opacity: 1, width: 'auto' }}
                exit={{ opacity: 0, width: 0 }}
                transition={EASE_OUT}
                className="overflow-hidden"
              >
                <span className="whitespace-nowrap text-[15px] font-bold tracking-tight text-[var(--color-text-primary)]">
                  Osool
                </span>
                <span className="ms-1.5 rounded-full bg-emerald-500/15 px-1.5 py-0.5 text-[10px] font-semibold text-emerald-600 dark:text-emerald-400">
                  AI
                </span>
              </motion.div>
            )}
          </AnimatePresence>
        </div>

        {/* Nav items */}
        <div className="flex flex-1 flex-col gap-0.5 overflow-y-auto overflow-x-hidden px-2 py-3 [scrollbar-width:none]">
          {/* Primary */}
          {primaryItems.map((item) => (
            <SideNavItem
              key={item.key}
              item={item}
              isActive={item.key === activeKey}
              isExpanded={isExpanded}
              isRTL={isRTL}
            />
          ))}

          {/* Secondary */}
          {secondaryItems.length > 0 && (
            <>
              <NavDivider />
              {secondaryItems.map((item) => (
                <SideNavItem
                  key={item.key}
                  item={item}
                  isActive={item.key === activeKey}
                  isExpanded={isExpanded}
                  isRTL={isRTL}
                />
              ))}
            </>
          )}

          {/* Admin */}
          {isAdmin && (
            <>
              <NavDivider />
              <SideNavItem
                item={{ key: 'admin', label: 'Admin', labelAr: 'الإدارة', icon: Shield, href: '/admin' }}
                isActive={activeKey === 'admin'}
                isExpanded={isExpanded}
                isRTL={isRTL}
              />
            </>
          )}
        </div>

        {/* Footer actions */}
        <div className="flex flex-col gap-0.5 border-t border-[var(--color-border)] px-2 py-3">
          {/* Notification bell */}
          <div className={`flex h-10 w-full items-center rounded-xl hover:bg-[var(--color-surface-elevated)] transition-colors ${
            isExpanded ? 'px-3 gap-3' : 'justify-center'
          }`}>
            <NotificationBell
              buttonClassName="flex items-center"
            />
            <AnimatePresence>
              {isExpanded && (
                <motion.span
                  initial={{ opacity: 0, width: 0 }}
                  animate={{ opacity: 1, width: 'auto' }}
                  exit={{ opacity: 0, width: 0 }}
                  transition={EASE_OUT}
                  className="overflow-hidden whitespace-nowrap text-[13px] font-medium text-[var(--color-text-muted)]"
                >
                  {language === 'ar' ? 'الإشعارات' : 'Notifications'}
                </motion.span>
              )}
            </AnimatePresence>
          </div>

          {/* Theme toggle */}
          <SideActionButton
            icon={theme === 'dark' ? Sun : Moon}
            label={theme === 'dark' ? (language === 'ar' ? 'الوضع الفاتح' : 'Light mode') : (language === 'ar' ? 'الوضع الداكن' : 'Dark mode')}
            onClick={toggleTheme}
            isExpanded={isExpanded}
            isRTL={isRTL}
          />

          {/* Language toggle */}
          <SideActionButton
            icon={Languages}
            label={language === 'en' ? 'العربية' : 'English'}
            onClick={toggleLanguage}
            isExpanded={isExpanded}
            isRTL={isRTL}
          />

          <NavDivider />

          {/* User / Login */}
          {isAuthenticated ? (
            <div className="relative">
              <AvatarButton
                user={user}
                isExpanded={isExpanded}
                isRTL={isRTL}
                onOpenMenu={() => setShowUserMenu((v) => !v)}
              />
              <AnimatePresence>
                {showUserMenu && (
                  <UserDropdown
                    isRTL={isRTL}
                    language={language}
                    onInvite={() => { onInvite(); setShowUserMenu(false); }}
                    onLogout={handleLogout}
                    onClose={() => setShowUserMenu(false)}
                  />
                )}
              </AnimatePresence>
            </div>
          ) : (
            <SideNavItem
              item={{ key: 'login', label: 'Sign in', labelAr: 'تسجيل الدخول', icon: LogIn, href: '/login' }}
              isActive={false}
              isExpanded={isExpanded}
              isRTL={isRTL}
            />
          )}
        </div>
      </motion.nav>

      {/* ╔══════════════════════════════╗
          ║  MOBILE BOTTOM TAB BAR       ║
          ╚══════════════════════════════╝ */}
      <motion.nav
        initial={false}
        animate={{
          y: mobileNavVisible ? 0 : 110,
          opacity: mobileNavVisible ? 1 : 0,
        }}
        transition={prefersReducedMotion ? { duration: 0 } : { duration: 0.28, ease: [0.16, 1, 0.3, 1] }}
        className={`lg:hidden fixed inset-x-3 z-50 flex items-stretch rounded-[26px]
                    border border-[var(--color-border)] bg-[var(--color-surface)]/95
                    backdrop-blur-2xl shadow-[0_18px_40px_rgba(0,0,0,0.2)]`}
        style={{
          bottom: 'max(12px, env(safe-area-inset-bottom, 0px))',
          paddingBottom: 'max(6px, env(safe-area-inset-bottom, 0px))',
          pointerEvents: mobileNavVisible ? 'auto' : 'none',
        }}
        aria-hidden={!mobileNavVisible}
      >
        {mobileItems.map((item) => {
          const isActive = item.key === activeKey;
          const Icon = item.icon;
          const label = language === 'ar' ? item.labelAr : item.label;

          return (
            <Link
              key={item.key}
              href={item.href}
              className="flex flex-1 flex-col items-center justify-center gap-1 min-h-[58px] py-2 px-1.5 relative"
              aria-label={label}
            >
              {isActive && (
                <motion.span
                  layoutId="mobile-active-bg"
                  className="absolute inset-x-2 inset-y-1.5 rounded-xl bg-emerald-500/12"
                  transition={SPRING}
                />
              )}
              <Icon
                className={`relative z-10 h-5 w-5 transition-colors ${
                  isActive
                    ? 'text-emerald-600 dark:text-emerald-400'
                    : 'text-[var(--color-text-muted)]'
                }`}
                strokeWidth={isActive ? 2.4 : 1.8}
              />
              <span
                className={`relative z-10 text-[10px] font-medium transition-colors leading-none ${
                  isActive
                    ? 'text-emerald-600 dark:text-emerald-400'
                    : 'text-[var(--color-text-muted)]'
                }`}
              >
                {label}
              </span>
            </Link>
          );
        })}

        {/* More tab */}
        <button
          onClick={() => setMobileMenuOpen(true)}
          className="flex flex-1 flex-col items-center justify-center gap-1 min-h-[58px] py-2 px-1.5"
          aria-label={language === 'ar' ? 'المزيد' : 'More'}
        >
          <Menu
            className="h-5 w-5 text-[var(--color-text-muted)]"
            strokeWidth={1.8}
          />
          <span className="text-[10px] font-medium text-[var(--color-text-muted)] leading-none">
            {language === 'ar' ? 'المزيد' : 'More'}
          </span>
        </button>
      </motion.nav>

      {/* ╔══════════════════════════════╗
          ║  MOBILE MENU SHEET           ║
          ╚══════════════════════════════╝ */}
      <AnimatePresence>
        {mobileMenuOpen && (
          <>
            {/* Backdrop */}
            <motion.div
              initial={{ opacity: 0 }}
              animate={{ opacity: 1 }}
              exit={{ opacity: 0 }}
              transition={{ duration: 0.2 }}
              onClick={() => setMobileMenuOpen(false)}
              className="lg:hidden fixed inset-0 z-[60] bg-black/40 backdrop-blur-sm"
            />

            {/* Sheet */}
            <motion.div
              initial={{ y: '100%' }}
              animate={{ y: 0 }}
              exit={{ y: '100%' }}
              transition={SPRING}
              className="lg:hidden fixed bottom-0 inset-x-0 z-[70] rounded-t-3xl border-t border-[var(--color-border)] bg-[var(--color-surface)] px-4 pt-3"
              style={{ paddingBottom: 'calc(env(safe-area-inset-bottom, 16px) + 16px)' }}
            >
              {/* Drag handle */}
              <div className="mx-auto mb-4 h-1 w-10 rounded-full bg-[var(--color-border)]" />

              {/* Close */}
              <button
                onClick={() => setMobileMenuOpen(false)}
                className="absolute right-4 top-4 flex h-8 w-8 items-center justify-center rounded-full bg-[var(--color-surface-elevated)]"
              >
                <X size={16} className="text-[var(--color-text-muted)]" />
              </button>

              <p className="mb-4 text-[11px] font-semibold uppercase tracking-wider text-[var(--color-text-muted)]">
                {language === 'ar' ? 'التنقل' : 'Navigate'}
              </p>

              {/* All nav items */}
              <div className="grid grid-cols-4 gap-2 mb-4">
                {[...primaryItems, ...secondaryItems].map((item) => {
                  const isActive = item.key === activeKey;
                  const Icon = item.icon;
                  const label = language === 'ar' ? item.labelAr : item.label;

                  return (
                    <Link
                      key={item.key}
                      href={item.href}
                      onClick={() => setMobileMenuOpen(false)}
                      className={`flex flex-col items-center gap-1.5 rounded-2xl p-3 transition-colors ${
                        isActive
                          ? 'bg-emerald-500/12 text-emerald-600 dark:text-emerald-400'
                          : 'bg-[var(--color-surface-elevated)] text-[var(--color-text-muted)]'
                      }`}
                    >
                      <Icon className="h-5 w-5" strokeWidth={isActive ? 2.2 : 1.8} />
                      <span className="text-[11px] font-medium leading-tight text-center">{label}</span>
                    </Link>
                  );
                })}

                {isAdmin && (
                  <Link
                    href="/admin"
                    onClick={() => setMobileMenuOpen(false)}
                    className={`flex flex-col items-center gap-1.5 rounded-2xl p-3 transition-colors ${
                      activeKey === 'admin'
                        ? 'bg-emerald-500/12 text-emerald-600 dark:text-emerald-400'
                        : 'bg-[var(--color-surface-elevated)] text-[var(--color-text-muted)]'
                    }`}
                  >
                    <Shield className="h-5 w-5" strokeWidth={1.8} />
                    <span className="text-[11px] font-medium">{language === 'ar' ? 'الإدارة' : 'Admin'}</span>
                  </Link>
                )}
              </div>

              <div className="h-px bg-[var(--color-border)] mb-4" />

              {/* Actions row */}
              <div className="flex items-center gap-2 mb-4">
                <button
                  onClick={() => { toggleTheme(); }}
                  className="flex flex-1 items-center justify-center gap-2 rounded-2xl bg-[var(--color-surface-elevated)] py-3 text-[13px] font-medium text-[var(--color-text-secondary)] transition-colors hover:bg-[var(--color-border)]"
                >
                  {theme === 'dark' ? <Sun size={16} /> : <Moon size={16} />}
                  {theme === 'dark' ? (language === 'ar' ? 'فاتح' : 'Light') : (language === 'ar' ? 'داكن' : 'Dark')}
                </button>
                <button
                  onClick={() => { toggleLanguage(); }}
                  className="flex flex-1 items-center justify-center gap-2 rounded-2xl bg-[var(--color-surface-elevated)] py-3 text-[13px] font-medium text-[var(--color-text-secondary)] transition-colors hover:bg-[var(--color-border)]"
                >
                  <Languages size={16} />
                  {language === 'en' ? 'العربية' : 'English'}
                </button>
              </div>

              {/* Auth row */}
              {isAuthenticated ? (
                <div className="flex items-center gap-2">
                  {isAuthenticated && (
                    <button
                      onClick={() => { onInvite(); setMobileMenuOpen(false); }}
                      className="flex flex-1 items-center justify-center gap-2 rounded-2xl bg-emerald-500/10 py-3 text-[13px] font-semibold text-emerald-600 dark:text-emerald-400 transition-colors"
                    >
                      <Gift size={16} />
                      {language === 'ar' ? 'دعوة صديق' : 'Invite friend'}
                    </button>
                  )}
                  <button
                    onClick={() => { handleLogout(); setMobileMenuOpen(false); }}
                    className="flex flex-1 items-center justify-center gap-2 rounded-2xl bg-[var(--color-surface-elevated)] py-3 text-[13px] font-medium text-red-500 transition-colors"
                  >
                    <LogOut size={16} />
                    {language === 'ar' ? 'خروج' : 'Sign out'}
                  </button>
                </div>
              ) : (
                <Link
                  href="/login"
                  onClick={() => setMobileMenuOpen(false)}
                  className="flex w-full items-center justify-center gap-2 rounded-2xl bg-emerald-600 py-3.5 text-[14px] font-semibold text-white"
                >
                  <LogIn size={16} />
                  {language === 'ar' ? 'تسجيل الدخول' : 'Sign in'}
                </Link>
              )}
            </motion.div>
          </>
        )}
      </AnimatePresence>
    </>
  );
}
