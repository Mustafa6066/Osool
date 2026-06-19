'use client';

import { useMemo, useState } from 'react';
import { usePathname, useRouter } from 'next/navigation';
import {
  Badge,
  Button,
  Drawer,
  DrawerBody,
  DrawerHeader,
  DrawerHeaderTitle,
  Subtitle2,
  Title3,
} from '@fluentui/react-components';
import {
  Menu,
  X,
  Sun,
  Moon,
  Languages,
  LogIn,
  LogOut,
  Gift,
  Shield,
} from 'lucide-react';
import InvitationModal from '@/components/InvitationModal';
import { useAuth } from '@/contexts/AuthContext';
import { useTheme } from '@/contexts/ThemeContext';
import { useLanguage } from '@/contexts/LanguageContext';
import { AUTH_NAV_PRIMARY, AUTH_NAV_SECONDARY, PUBLIC_NAV, getActiveKey, type NavItem } from '@/components/nav/nav-items';

interface AppShellProps {
  children: React.ReactNode;
}

export default function AppShell({ children }: AppShellProps) {
  const pathname = usePathname();
  const router = useRouter();
  const { user, isAuthenticated, logout } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const { language, toggleLanguage } = useLanguage();

  const [showInviteModal, setShowInviteModal] = useState(false);
  const [mobileOpen, setMobileOpen] = useState(false);
  const openInvite = () => setShowInviteModal(true);
  const activeKey = getActiveKey(pathname);

  const primaryItems = useMemo<NavItem[]>(
    () => (isAuthenticated ? AUTH_NAV_PRIMARY : PUBLIC_NAV),
    [isAuthenticated]
  );
  const secondaryItems = useMemo<NavItem[]>(
    () => (isAuthenticated ? AUTH_NAV_SECONDARY : []),
    [isAuthenticated]
  );
  const mobileItems = useMemo(() => primaryItems.slice(0, 4), [primaryItems]);

  const isAdmin = user?.role === 'admin';

  function navigateTo(href: string) {
    router.push(href);
    setMobileOpen(false);
  }

  function renderNavButton(item: NavItem, compact = false) {
    const Icon = item.icon;
    const label = language === 'ar' ? item.labelAr : item.label;
    const active = item.key === activeKey;

    return (
      <Button
        key={item.key}
        appearance={active ? 'primary' : 'subtle'}
        icon={<Icon size={16} />}
        onClick={() => navigateTo(item.href)}
        className={`!justify-start ${compact ? '!w-full' : '!w-full'} ${active ? '' : '!text-[var(--osool-text-2)]'}`}
      >
        {label}
      </Button>
    );
  }

  return (
    <>
      <InvitationModal isOpen={showInviteModal} onClose={() => setShowInviteModal(false)} />

      <div className="min-h-dvh bg-[var(--osool-bg)] text-[var(--osool-text)]">
        <aside className="hidden lg:flex fixed inset-y-0 start-0 w-72 border-e border-[var(--osool-border)] bg-[var(--osool-surface)]/95 backdrop-blur-md z-30">
          <div className="flex h-full w-full flex-col p-4 gap-4">
            <div className="rounded-2xl border border-[var(--osool-border)] bg-[var(--osool-bg)] px-3 py-3">
              <div className="flex items-center justify-between gap-3">
                <div>
                  <Title3 as="h2" className="!text-[var(--osool-text)]">Osool</Title3>
                  <Subtitle2 className="!text-[var(--osool-text-2)]">
                    {language === 'ar' ? 'منصة الاستثمار العقاري' : 'Real Estate Advisor'}
                  </Subtitle2>
                </div>
                {isAuthenticated && (
                  <Badge appearance="tint" color="informative">
                    {user?.full_name?.split(' ')[0] || 'User'}
                  </Badge>
                )}
              </div>
            </div>

            <div className="space-y-2">
              {primaryItems.map((item) => renderNavButton(item))}
            </div>

            {secondaryItems.length > 0 && (
              <div className="space-y-2 pt-2 border-t border-[var(--osool-border)]">
                {secondaryItems.map((item) => renderNavButton(item))}
              </div>
            )}

            <div className="mt-auto space-y-2 border-t border-[var(--osool-border)] pt-3">
              <Button appearance="subtle" icon={theme === 'dark' ? <Sun size={16} /> : <Moon size={16} />} onClick={toggleTheme} className="!w-full !justify-start">
                {theme === 'dark' ? 'Light mode' : 'Dark mode'}
              </Button>
              <Button appearance="subtle" icon={<Languages size={16} />} onClick={toggleLanguage} className="!w-full !justify-start">
                {language === 'en' ? 'العربية' : 'English'}
              </Button>
              {isAdmin && (
                <Button appearance="subtle" icon={<Shield size={16} />} onClick={() => navigateTo('/admin')} className="!w-full !justify-start">
                  {language === 'ar' ? 'لوحة المدير' : 'Admin'}
                </Button>
              )}
              {isAuthenticated ? (
                <>
                  <Button appearance="subtle" icon={<Gift size={16} />} onClick={openInvite} className="!w-full !justify-start">
                    {language === 'ar' ? 'دعوة صديق' : 'Invite friend'}
                  </Button>
                  <Button appearance="subtle" icon={<LogOut size={16} />} onClick={logout} className="!w-full !justify-start !text-red-500">
                    {language === 'ar' ? 'تسجيل الخروج' : 'Sign out'}
                  </Button>
                </>
              ) : (
                <Button appearance="primary" icon={<LogIn size={16} />} onClick={() => navigateTo('/login')} className="!w-full !justify-start !bg-[var(--osool-accent)] hover:!bg-[var(--osool-accent-dark)] !text-white !border-transparent">
                  {language === 'ar' ? 'تسجيل الدخول' : 'Sign in'}
                </Button>
              )}
            </div>
          </div>
        </aside>

        <header className="lg:hidden sticky top-0 z-40 border-b border-[var(--osool-border)] bg-[var(--osool-surface)]/95 backdrop-blur-md px-3 py-2 flex items-center justify-between">
          <Button
            appearance="subtle"
            icon={<Menu size={18} />}
            aria-label="Open navigation"
            onClick={() => setMobileOpen(true)}
          />
          <div className="text-sm font-semibold text-[var(--osool-text)]">
            {language === 'ar' ? 'أصول' : 'Osool'}
          </div>
          <Button
            appearance="subtle"
            icon={theme === 'dark' ? <Sun size={16} /> : <Moon size={16} />}
            aria-label="Toggle theme"
            onClick={toggleTheme}
          />
        </header>

        <main className="flex flex-col min-h-dvh overflow-x-hidden overflow-y-auto lg:ps-72 pb-[calc(env(safe-area-inset-bottom,0px)+5.25rem)] lg:pb-0">
          {children}
        </main>

        <nav className="lg:hidden fixed bottom-0 inset-x-0 z-40 border-t border-[var(--osool-border)] bg-[var(--osool-surface)]/97 backdrop-blur-md px-2 pt-2 pb-[calc(env(safe-area-inset-bottom,0px)+0.5rem)]">
          <div className="grid grid-cols-4 gap-1">
            {mobileItems.map((item) => {
              const Icon = item.icon;
              const isActive = item.key === activeKey;
              return (
                <button
                  key={item.key}
                  onClick={() => navigateTo(item.href)}
                  className={`h-14 rounded-xl flex flex-col items-center justify-center gap-1 text-xs transition-colors ${
                    isActive
                      ? 'bg-[var(--osool-accent-mid)] text-[var(--osool-accent)]'
                      : 'text-[var(--osool-text-2)]'
                  }`}
                  aria-current={isActive ? 'page' : undefined}
                >
                  <Icon size={18} />
                  <span className="leading-none">{language === 'ar' ? item.labelAr : item.label}</span>
                </button>
              );
            })}
          </div>
        </nav>

        <Drawer
          open={mobileOpen}
          onOpenChange={(_, data) => setMobileOpen(data.open)}
          position="start"
          modalType="modal"
          size="medium"
        >
          <DrawerHeader>
            <DrawerHeaderTitle
              action={
                <Button
                  appearance="subtle"
                  icon={<X size={16} />}
                  onClick={() => setMobileOpen(false)}
                  aria-label="Close navigation"
                />
              }
            >
              {language === 'ar' ? 'القائمة' : 'Navigation'}
            </DrawerHeaderTitle>
          </DrawerHeader>
          <DrawerBody>
            <div className="space-y-2">
              {primaryItems.map((item) => renderNavButton(item, true))}
              {secondaryItems.map((item) => renderNavButton(item, true))}
              {isAdmin && (
                <Button appearance="subtle" icon={<Shield size={16} />} onClick={() => navigateTo('/admin')} className="!w-full !justify-start">
                  {language === 'ar' ? 'لوحة المدير' : 'Admin'}
                </Button>
              )}
            </div>
            <div className="space-y-2 mt-5 pt-4 border-t border-[var(--osool-border)]">
              <Button appearance="subtle" icon={<Languages size={16} />} onClick={toggleLanguage} className="!w-full !justify-start">
                {language === 'en' ? 'العربية' : 'English'}
              </Button>
              {isAuthenticated ? (
                <>
                  <Button appearance="subtle" icon={<Gift size={16} />} onClick={() => { openInvite(); setMobileOpen(false); }} className="!w-full !justify-start">
                    {language === 'ar' ? 'دعوة صديق' : 'Invite friend'}
                  </Button>
                  <Button appearance="subtle" icon={<LogOut size={16} />} onClick={() => { logout(); setMobileOpen(false); }} className="!w-full !justify-start !text-red-500">
                    {language === 'ar' ? 'تسجيل الخروج' : 'Sign out'}
                  </Button>
                </>
              ) : (
                <Button appearance="primary" icon={<LogIn size={16} />} onClick={() => navigateTo('/login')} className="!w-full !justify-start !bg-[var(--osool-accent)] hover:!bg-[var(--osool-accent-dark)] !text-white !border-transparent">
                  {language === 'ar' ? 'تسجيل الدخول' : 'Sign in'}
                </Button>
              )}
            </div>
          </DrawerBody>
        </Drawer>
      </div>
    </>
  );
}
