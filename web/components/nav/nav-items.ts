import {
  MessageSquare,
  Compass,
  TrendingUp,
  Heart,
  LayoutDashboard,
  Home,
  Building2,
  MapPin,
  Layers,
} from 'lucide-react';
import type { ElementType } from 'react';

export interface NavItem {
  key: string;
  label: string;
  labelAr: string;
  icon: ElementType;
  href: string;
}

/** Authenticated users — primary navigation items */
export const AUTH_NAV_PRIMARY: NavItem[] = [
  { key: 'chat',       label: 'Chat',       labelAr: 'المحادثة',  icon: MessageSquare,   href: '/chat' },
  { key: 'explore',    label: 'Explore',    labelAr: 'استكشف',    icon: Compass,         href: '/explore' },
  { key: 'areas',      label: 'Areas',      labelAr: 'المناطق',   icon: MapPin,          href: '/areas' },
  { key: 'developers', label: 'Developers', labelAr: 'المطورون',  icon: Building2,       href: '/developers' },
  { key: 'projects',   label: 'Projects',   labelAr: 'المشاريع',  icon: Layers,          href: '/projects' },
];

/** Authenticated users — secondary navigation items */
export const AUTH_NAV_SECONDARY: NavItem[] = [
  { key: 'dashboard', label: 'Dashboard', labelAr: 'الرئيسية',  icon: LayoutDashboard, href: '/dashboard' },
  { key: 'saved',     label: 'Saved',     labelAr: 'المحفوظات', icon: Heart,           href: '/favorites' },
  { key: 'market',    label: 'Market',    labelAr: 'السوق',     icon: TrendingUp,      href: '/market' },
];

/** Authenticated users — all items combined (backward compat) */
export const AUTH_NAV: NavItem[] = [...AUTH_NAV_PRIMARY, ...AUTH_NAV_SECONDARY];

/** Public visitors — first 4 items appear in mobile bottom bar */
export const PUBLIC_NAV: NavItem[] = [
  { key: 'home',       label: 'Home',       labelAr: 'الرئيسية',  icon: Home,     href: '/' },
  { key: 'explore',    label: 'Explore',    labelAr: 'استكشف',    icon: Compass,  href: '/explore' },
  { key: 'developers', label: 'Developers', labelAr: 'المطورون',  icon: Building2, href: '/developers' },
  { key: 'areas',      label: 'Areas',      labelAr: 'المناطق',   icon: MapPin,   href: '/areas' },
  { key: 'projects',   label: 'Projects',   labelAr: 'المشاريع',  icon: Layers,   href: '/projects' },
];

/** Resolve pathname → nav key for active-state highlighting */
export function getActiveKey(pathname: string): string {
  if (pathname === '/') return 'home';
  if (pathname === '/chat') return 'chat';
  if (pathname === '/dashboard') return 'dashboard';
  if (pathname === '/favorites') return 'saved';
  if (pathname === '/market') return 'market';
  if (pathname.startsWith('/admin')) return 'admin';
  if (pathname.startsWith('/tickets')) return 'tickets';
  if (
    pathname.startsWith('/explore') ||
    pathname.startsWith('/properties') ||
    pathname.startsWith('/property/') ||
    pathname.startsWith('/compare')
  )
    return 'explore';
  if (pathname.startsWith('/developers')) return 'developers';
  if (pathname.startsWith('/areas') || pathname.startsWith('/roi') || pathname.startsWith('/buying-guide'))
    return 'areas';
  if (pathname.startsWith('/projects')) return 'projects';
  return '';
}
