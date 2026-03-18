'use client';

import React, { useState, useEffect, useCallback, useRef } from 'react';
import { createPortal } from 'react-dom';
import { usePathname, useRouter } from 'next/navigation';
import Link from 'next/link';
import { motion, AnimatePresence, useAnimationControls, useMotionValue, type PanInfo } from 'framer-motion';
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
const LAUNCHER_POS_KEY = 'osool:floating-nav-launcher-position';
const LAUNCHER_SIZE = 48;
const SAFE_GAP = 12;

interface SmartNavProps {
  onInvite: () => void;
}

interface Position {
  x: number;
  y: number;
}

interface NavPillProps {
  item: NavItem;
  active: boolean;
  language: string;
  onClick: () => void;
}

function clampPosition(pos: Position): Position {
  if (typeof window === 'undefined') return pos;
  const maxX = Math.max(SAFE_GAP, window.innerWidth - LAUNCHER_SIZE - SAFE_GAP);
  const maxY = Math.max(SAFE_GAP, window.innerHeight - LAUNCHER_SIZE - SAFE_GAP);
  return {
    x: Math.min(Math.max(pos.x, SAFE_GAP), maxX),
    y: Math.min(Math.max(pos.y, SAFE_GAP), maxY),
  };
}

function getDefaultLauncherPosition(): Position {
  if (typeof window === 'undefined') return { x: 16, y: 16 };
  return {
    x: 16,
    y: window.innerHeight - 82,
  };
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

  const [mounted, setMounted] = useState(false);
  const [expanded, setExpanded] = useState(false);
  const [launcherPos, setLauncherPos] = useState<Position>({ x: 16, y: 16 });

  const panelRef = useRef<HTMLDivElement>(null);
  const launcherRef = useRef<HTMLButtonElement>(null);
  const justDraggedRef = useRef(false);

  const toggleControls = useAnimationControls();
  const dragX = useMotionValue(0);
  const dragY = useMotionValue(0);

  useEffect(() => {
    setMounted(true);

    const savedExpanded = localStorage.getItem(NAV_EXPANDED_KEY);
    const savedPos = localStorage.getItem(LAUNCHER_POS_KEY);

    if (savedExpanded === '1') setExpanded(true);

    if (savedPos) {
      try {
        const parsed = JSON.parse(savedPos) as Position;
        setLauncherPos(clampPosition(parsed));
      } catch {
        setLauncherPos(clampPosition(getDefaultLauncherPosition()));
      }
    } else {
      setLauncherPos(clampPosition(getDefaultLauncherPosition()));
    }
  }, []);

  useEffect(() => {
    if (!mounted) return;
    localStorage.setItem(NAV_EXPANDED_KEY, expanded ? '1' : '0');
  }, [expanded, mounted]);

  useEffect(() => {
    if (!mounted) return;
    localStorage.setItem(LAUNCHER_POS_KEY, JSON.stringify(launcherPos));
  }, [launcherPos, mounted]);

  useEffect(() => {
    setExpanded(false);
  }, [pathname]);

  useEffect(() => {
    const keyHandler = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setExpanded(false);
    };

    const clickHandler = (e: MouseEvent) => {
      if (!expanded) return;
      const target = e.target as Node;
      const clickedPanel = panelRef.current?.contains(target);
      const clickedLauncher = launcherRef.current?.contains(target);
      if (!clickedPanel && !clickedLauncher) setExpanded(false);
    };

    const resizeHandler = () => {
      setLauncherPos((prev) => clampPosition(prev));
    };

    document.addEventListener('keydown', keyHandler);
    document.addEventListener('mousedown', clickHandler);
    window.addEventListener('resize', resizeHandler);

    return () => {
      document.removeEventListener('keydown', keyHandler);
      document.removeEventListener('mousedown', clickHandler);
      window.removeEventListener('resize', resizeHandler);
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
    if (justDraggedRef.current) {
      justDraggedRef.current = false;
      return;
    }

    setExpanded((v) => !v);
    void toggleControls.start({
      scale: [1, 0.93, 1.05, 1],
      transition: { duration: 0.28, times: [0, 0.3, 0.68, 1], ease: 'easeOut' },
    });
  }, [toggleControls]);

  const onDragEnd = useCallback((_: MouseEvent | TouchEvent | PointerEvent, info: PanInfo) => {
    const movedEnough = Math.abs(info.offset.x) > 4 || Math.abs(info.offset.y) > 4;
    if (movedEnough) {
      justDraggedRef.current = true;
      window.setTimeout(() => {
        justDraggedRef.current = false;
      }, 120);
    }

    setLauncherPos((prev) =>
      clampPosition({
        x: prev.x + info.offset.x,
        y: prev.y + info.offset.y,
      })
    );

    dragX.set(0);
    dragY.set(0);
  }, [dragX, dragY]);

  if (!mounted) return null;

  const panelWidth = Math.min(window.innerWidth - 24, 940);

  return createPortal(
    <>
      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="fixed inset-0 z-[88] bg-black/14 backdrop-blur-[1px]"
            aria-hidden
          />
        )}
      </AnimatePresence>

      <motion.button
        ref={launcherRef}
        drag
        dragMomentum={false}
        dragElastic={0.08}
        onDragEnd={onDragEnd}
        onClick={handleToggle}
        initial={false}
        animate={toggleControls}
        whileTap={{ scale: 0.94 }}
        whileHover={{ scale: 1.03 }}
        style={{ left: launcherPos.x, top: launcherPos.y, x: dragX, y: dragY }}
        className="fixed z-[91] flex h-12 w-12 items-center justify-center rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)]/95 backdrop-blur-xl shadow-[0_10px_26px_rgba(0,0,0,0.18)]"
        aria-label={expanded ? (language === 'ar' ? 'طي لوحة التنقل' : 'Collapse navigation panel') : (language === 'ar' ? 'فتح لوحة التنقل' : 'Expand navigation panel')}
        title={expanded ? (language === 'ar' ? 'طي' : 'Collapse') : (language === 'ar' ? 'فتح' : 'Expand')}
      >
        {/* Always-visible 3-dot launcher */}
        <div className="relative h-5 w-6">
          {[0, 1, 2].map((dot) => (
            <motion.span
              key={dot}
              animate={{
                width: expanded ? 18 : 14,
                opacity: expanded ? 0.95 : 0.82,
                y: dot === 0 ? (expanded ? -5 : -6) : dot === 1 ? 0 : (expanded ? 5 : 6),
              }}
              transition={{ duration: 0.22, ease: 'easeOut' }}
              className="absolute left-1/2 top-1/2 block h-[3px] -translate-x-1/2 rounded-full bg-[var(--color-text-secondary)]"
            />
          ))}
        </div>
      </motion.button>

      <AnimatePresence>
        {expanded && (
          <motion.nav
            ref={panelRef}
            initial={{ opacity: 0, y: 20, scale: 0.98, filter: 'blur(6px)' }}
            animate={{ opacity: 1, y: 0, scale: 1, filter: 'blur(0px)' }}
            exit={{ opacity: 0, y: 14, scale: 0.985, filter: 'blur(4px)' }}
            transition={SPRING_PANEL}
            style={{ width: panelWidth }}
            className="fixed left-1/2 bottom-[calc(env(safe-area-inset-bottom,0px)+12px)] z-[90] -translate-x-1/2 rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)]/96 p-3 sm:p-4 backdrop-blur-2xl shadow-[0_24px_56px_rgba(0,0,0,0.18)]"
            aria-label={language === 'ar' ? 'لوحة التنقل العائمة' : 'Floating navigation panel'}
          >
            <div className="flex flex-wrap items-center justify-between gap-2 pb-2">
              <Link
                href="/"
                onClick={() => setExpanded(false)}
                className="inline-flex items-center gap-2 rounded-lg px-2 py-1.5 text-[var(--color-text-primary)] hover:bg-[var(--color-background)] transition-colors"
              >
                <div className="w-6 h-6 rounded-md bg-gradient-to-br from-emerald-400 to-emerald-600 flex items-center justify-center">
                  <Sparkles className="w-3.5 h-3.5 text-white" />
                </div>
                <span className="text-sm font-semibold">{language === 'ar' ? 'أصول' : 'Osool'}</span>
              </Link>

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
    </>,
    document.body
  );
}
