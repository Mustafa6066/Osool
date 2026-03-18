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
  Terminal,
} from 'lucide-react';
import type { ElementType } from 'react';

export interface NavItem {
  key: string;
  label: string;
  labelAr: string;
  icon: ElementType;
  href: string;
}

/** Authenticated users — first 4 items appear in mobile bottom bar */
export const AUTH_NAV: NavItem[] = [
  { key: 'chat',      label: 'Chat',    labelAr: 'المحادثة',  icon: MessageSquare,   href: '/chat' },
  { key: 'explore',   label: 'Explore', labelAr: 'استكشف',    icon: Compass,         href: '/explore' },
  { key: 'saved',     label: 'Saved',   labelAr: 'المحفوظات', icon: Heart,           href: '/favorites' },
  { key: 'dashboard', label: 'Home',    labelAr: 'الرئيسية',  icon: LayoutDashboard, href: '/dashboard' },
  { key: 'market',    label: 'Market',  labelAr: 'السوق',     icon: TrendingUp,      href: '/market' },
  { key: 'terminal',  label: 'Terminal', labelAr: 'المحطة',    icon: Terminal,        href: '/terminal' },
];

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
  if (pathname === '/terminal') return 'terminal';
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
