'use client';

import React, { useState, useEffect, useCallback, useRef } from 'react';
import { createPortal } from 'react-dom';
import { usePathname, useRouter } from 'next/navigation';
import Link from 'next/link';
import { motion, AnimatePresence, useAnimationControls, useMotionValue, type PanInfo } from 'framer-motion';
import {
  Sparkles, Sun, Moon, Gift, LogOut, Shield, Search, LogIn, Languages,
} from 'lucide-react';
import { useAuth } from '@/contexts/AuthContext';
import { useTheme } from '@/contexts/ThemeContext';
import { useLanguage } from '@/contexts/LanguageContext';
import { AUTH_NAV, PUBLIC_NAV, getActiveKey, type NavItem } from '@/components/nav/nav-items';
import NotificationBell from '@/components/NotificationBell';

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

interface IconButtonProps {
  icon: NavItem['icon'];
  active?: boolean;
  label: string;
  onClick?: () => void;
  href?: string;
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

function DockIconButton({ icon: Icon, active = false, label, onClick, href }: IconButtonProps) {
  const className = `group shrink-0 flex h-10 w-10 items-center justify-center rounded-xl border transition-colors ${
    active
      ? 'border-emerald-500/25 bg-emerald-500/10 text-emerald-600 dark:text-emerald-400'
      : 'border-[var(--color-border)] bg-[var(--color-background)] text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)]'
  }`;

  if (href) {
    return (
      <Link
        href={href}
        className={className}
        aria-label={label}
        title={label}
        data-haptic="light"
      >
        <Icon className="h-4 w-4" />
      </Link>
    );
  }

  return (
    <motion.button
      onClick={onClick}
      whileTap={{ scale: 0.95 }}
      className={className}
      aria-label={label}
      title={label}
      data-haptic="light"
    >
      <Icon className="h-4 w-4" />
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

  const isMobile = window.innerWidth < 640;
  const panelWidth = isMobile ? window.innerWidth : Math.min(window.innerWidth - 24, 740);

  return createPortal(
    <>
      <AnimatePresence>
        {expanded && (
          <motion.div
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.16 }}
            className="fixed inset-0 z-[88] bg-black/10 backdrop-blur-[1px]"
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
        className="fixed z-[91] flex h-12 w-12 items-center justify-center rounded-xl border border-[var(--color-border)] bg-[var(--color-surface)]/96 backdrop-blur-xl shadow-[0_10px_26px_rgba(0,0,0,0.16)]"
        aria-label={expanded ? (language === 'ar' ? 'طي لوحة التنقل' : 'Collapse navigation panel') : (language === 'ar' ? 'فتح لوحة التنقل' : 'Expand navigation panel')}
        title={expanded ? (language === 'ar' ? 'طي' : 'Collapse') : (language === 'ar' ? 'فتح' : 'Expand')}
        data-haptic="medium"
      >
        <div className="relative h-5 w-6">
          {[0, 1, 2].map((dot) => (
            <motion.span
              key={dot}
              animate={{
                width: expanded ? 18 : 14,
                opacity: expanded ? 0.95 : 0.84,
                y: dot === 0 ? (expanded ? -5 : -6) : dot === 1 ? 0 : (expanded ? 5 : 6),
              }}
              transition={{ duration: 0.2, ease: 'easeOut' }}
              className="absolute left-1/2 top-1/2 block h-[3px] -translate-x-1/2 rounded-full bg-[var(--color-text-secondary)]"
            />
          ))}
        </div>
      </motion.button>

      <AnimatePresence>
        {expanded && (
          <motion.nav
            ref={panelRef}
            initial={{ opacity: 0, y: 18, scale: 0.985, filter: 'blur(5px)' }}
            animate={{ opacity: 1, y: 0, scale: 1, filter: 'blur(0px)' }}
            exit={{ opacity: 0, y: 10, scale: 0.99, filter: 'blur(4px)' }}
            transition={SPRING_PANEL}
            style={{ width: panelWidth }}
            className={`fixed left-1/2 bottom-[calc(env(safe-area-inset-bottom,0px)+12px)] z-[90] -translate-x-1/2 border border-[var(--color-border)] bg-[var(--color-surface)]/97 backdrop-blur-2xl shadow-[0_24px_56px_rgba(0,0,0,0.16)] ${
              isMobile ? 'rounded-none border-x-0 p-2.5' : 'rounded-2xl p-3'
            }`}
            aria-label={language === 'ar' ? 'لوحة التنقل العائمة' : 'Floating navigation panel'}
          >
            <div className="flex items-center justify-center">
              <div className="flex max-w-full items-center justify-center gap-1.5 overflow-x-auto overflow-y-visible whitespace-nowrap [scrollbar-width:none] [-ms-overflow-style:none] [&::-webkit-scrollbar]:hidden">
                <DockIconButton
                  icon={Sparkles}
                  label={language === 'ar' ? 'الرئيسية' : 'Home'}
                  href="/"
                />

                <div className="h-6 w-px shrink-0 bg-[var(--color-border)]" aria-hidden />

                <DockIconButton
                  icon={Search}
                  label={language === 'ar' ? 'اسأل أصول' : 'Ask Osool'}
                  onClick={triggerSearch}
                />
                <NotificationBell buttonClassName="h-10 w-10 shrink-0 rounded-xl border border-[var(--color-border)] bg-[var(--color-background)] text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)]" />
                <DockIconButton
                  icon={theme === 'dark' ? Sun : Moon}
                  label={theme === 'dark' ? 'Light mode' : 'Dark mode'}
                  onClick={toggleTheme}
                />
                <DockIconButton
                  icon={Languages}
                  label={language === 'en' ? 'العربية' : 'English'}
                  onClick={toggleLanguage}
                />

                <div className="h-6 w-px shrink-0 bg-[var(--color-border)]" aria-hidden />

                {items.map((item) => (
                  <DockIconButton
                    key={item.key}
                    icon={item.icon}
                    active={item.key === activeKey}
                    label={language === 'ar' ? item.labelAr : item.label}
                    onClick={() => handleNavigate(item.href)}
                  />
                ))}

                {isAdmin && (
                  <DockIconButton
                    icon={Shield}
                    active={activeKey === 'admin'}
                    label={language === 'ar' ? 'المدير' : 'Admin'}
                    onClick={() => handleNavigate('/admin')}
                  />
                )}

                <div className="h-6 w-px shrink-0 bg-[var(--color-border)]" aria-hidden />

                {isAuthenticated ? (
                  <>
                    <DockIconButton
                      icon={Gift}
                      label={language === 'ar' ? 'دعوة أصدقاء' : 'Invite Friends'}
                      onClick={() => {
                        onInvite();
                        setExpanded(false);
                      }}
                    />
                    <DockIconButton
                      icon={LogOut}
                      label={language === 'ar' ? 'تسجيل الخروج' : 'Sign Out'}
                      onClick={() => {
                        logout();
                        setExpanded(false);
                      }}
                    />
                  </>
                ) : (
                  <DockIconButton
                    icon={LogIn}
                    label={language === 'ar' ? 'تسجيل الدخول' : 'Login'}
                    href="/login"
                  />
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
