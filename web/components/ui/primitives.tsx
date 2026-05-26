'use client';

import React from 'react';

// ═══════════════════════════════════════════════════════════
// OSOOL DESIGN SYSTEM — Themed Primitives
// Inspired by src/components/design-system (Claude Code)
//
// Provides consistent, theme-aware, RTL-ready base components
// that respect CSS custom properties and dark/light mode.
// ═══════════════════════════════════════════════════════════

// ─── Surface ─────────────────────────────────────────────
// A container with consistent background, border, and radius.
// Replaces ad-hoc bg-[var(--color-surface)] usage.

type SurfaceVariant = 'default' | 'elevated' | 'sunken' | 'glass';

const surfaceStyles: Record<SurfaceVariant, string> = {
  default: 'bg-[var(--color-surface)] border-[var(--color-border)]',
  elevated: 'bg-[var(--color-surface-elevated)] border-[var(--color-border)] shadow-sm',
  sunken: 'bg-[var(--color-background)] border-[var(--color-border)]/50',
  glass: 'bg-[var(--color-surface)]/60 backdrop-blur-xl border-[var(--color-border)]/40',
};

interface SurfaceProps extends React.HTMLAttributes<HTMLDivElement> {
  variant?: SurfaceVariant;
  rounded?: 'sm' | 'md' | 'lg' | 'xl' | '2xl' | 'full';
  border?: boolean;
  padding?: 'none' | 'sm' | 'md' | 'lg';
  as?: 'div' | 'section' | 'article' | 'aside';
}

const roundedMap = {
  sm: 'rounded-sm',
  md: 'rounded-md',
  lg: 'rounded-lg',
  xl: 'rounded-xl',
  '2xl': 'rounded-2xl',
  full: 'rounded-full',
};

const paddingMap = {
  none: '',
  sm: 'p-2',
  md: 'p-4',
  lg: 'p-6',
};

export function Surface({
  variant = 'default',
  rounded = 'xl',
  border = true,
  padding = 'md',
  as: Component = 'div',
  className = '',
  children,
  ...props
}: SurfaceProps) {
  const classes = [
    surfaceStyles[variant],
    roundedMap[rounded],
    border ? 'border' : '',
    paddingMap[padding],
    className,
  ]
    .filter(Boolean)
    .join(' ');

  return (
    <Component className={classes} {...props}>
      {children}
    </Component>
  );
}

// ─── Text ────────────────────────────────────────────────
// Theme-aware text with semantic levels.

type TextLevel = 'display' | 'title' | 'heading' | 'body' | 'caption' | 'label' | 'muted';

const textStyles: Record<TextLevel, string> = {
  display: 'text-2xl sm:text-3xl font-bold text-[var(--color-text-primary)] tracking-tight',
  title: 'text-xl font-semibold text-[var(--color-text-primary)]',
  heading: 'text-base font-semibold text-[var(--color-text-primary)]',
  body: 'text-[15px] leading-relaxed text-[var(--color-text-secondary)]',
  caption: 'text-xs text-[var(--color-text-muted)]',
  label: 'text-[11px] font-medium uppercase tracking-wider text-[var(--color-text-muted)]',
  muted: 'text-sm text-[var(--color-text-muted)]',
};

interface TextProps extends React.HTMLAttributes<HTMLElement> {
  level?: TextLevel;
  as?: 'p' | 'span' | 'h1' | 'h2' | 'h3' | 'h4' | 'div' | 'label';
  truncate?: boolean;
  align?: 'start' | 'center' | 'end';
}

export function Text({
  level = 'body',
  as: Component = 'p',
  truncate = false,
  align,
  className = '',
  children,
  ...props
}: TextProps) {
  const classes = [
    textStyles[level],
    truncate ? 'truncate' : '',
    align ? `text-${align}` : '',
    className,
  ]
    .filter(Boolean)
    .join(' ');

  return (
    <Component className={classes} {...props}>
      {children}
    </Component>
  );
}

// ─── Badge ───────────────────────────────────────────────

type BadgeVariant = 'default' | 'success' | 'warning' | 'error' | 'info' | 'emerald';

const badgeStyles: Record<BadgeVariant, string> = {
  default: 'bg-[var(--color-surface-elevated)] text-[var(--color-text-secondary)] border-[var(--color-border)]',
  success: 'bg-emerald-500/10 text-emerald-600 dark:text-emerald-400 border-emerald-500/20',
  warning: 'bg-amber-500/10 text-amber-600 dark:text-amber-400 border-amber-500/20',
  error: 'bg-red-500/10 text-red-600 dark:text-red-400 border-red-500/20',
  info: 'bg-blue-500/10 text-blue-600 dark:text-blue-400 border-blue-500/20',
  emerald: 'bg-emerald-500/90 text-white border-emerald-600/30',
};

interface BadgeProps extends React.HTMLAttributes<HTMLSpanElement> {
  variant?: BadgeVariant;
  size?: 'xs' | 'sm' | 'md';
  icon?: React.ReactNode;
}

const badgeSizeMap = {
  xs: 'text-[9px] px-1.5 py-0.5',
  sm: 'text-[10px] px-2 py-0.5',
  md: 'text-xs px-2.5 py-1',
};

export function Badge({
  variant = 'default',
  size = 'sm',
  icon,
  className = '',
  children,
  ...props
}: BadgeProps) {
  return (
    <span
      className={`inline-flex items-center gap-1 rounded-full border font-semibold ${badgeStyles[variant]} ${badgeSizeMap[size]} ${className}`}
      {...props}
    >
      {icon}
      {children}
    </span>
  );
}

// ─── IconButton ──────────────────────────────────────────

type IconButtonVariant = 'ghost' | 'subtle' | 'solid';

const iconButtonStyles: Record<IconButtonVariant, string> = {
  ghost: 'text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)] hover:bg-[var(--color-surface-elevated)]',
  subtle: 'text-[var(--color-text-secondary)] bg-[var(--color-surface)] hover:bg-[var(--color-surface-elevated)] border border-[var(--color-border)]',
  solid: 'text-white bg-[var(--color-primary)] hover:bg-[var(--color-primary-dark)]',
};

interface IconButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: IconButtonVariant;
  size?: 'sm' | 'md' | 'lg';
}

const iconButtonSizeMap = {
  sm: 'p-1 rounded-md',
  md: 'p-1.5 rounded-lg',
  lg: 'p-2 rounded-xl',
};

export function IconButton({
  variant = 'ghost',
  size = 'md',
  className = '',
  children,
  ...props
}: IconButtonProps) {
  return (
    <button
      className={`transition-colors ${iconButtonStyles[variant]} ${iconButtonSizeMap[size]} ${className}`}
      {...props}
    >
      {children}
    </button>
  );
}

// ─── Divider ─────────────────────────────────────────────

interface DividerProps {
  className?: string;
  vertical?: boolean;
}

export function Divider({ className = '', vertical = false }: DividerProps) {
  if (vertical) {
    return <div className={`w-px self-stretch bg-[var(--color-border)]/50 ${className}`} />;
  }
  return <div className={`h-px w-full bg-[var(--color-border)]/50 ${className}`} />;
}

// ─── Skeleton ────────────────────────────────────────────

interface SkeletonProps {
  className?: string;
  width?: string;
  height?: string;
  rounded?: 'sm' | 'md' | 'lg' | 'xl' | 'full';
}

export function Skeleton({ className = '', width, height, rounded = 'md' }: SkeletonProps) {
  return (
    <div
      className={`animate-pulse bg-[var(--color-surface-elevated)] ${roundedMap[rounded]} ${className}`}
      style={{ width, height }}
    />
  );
}

// ─── StatusDot ───────────────────────────────────────────

type StatusDotColor = 'green' | 'yellow' | 'red' | 'blue' | 'gray';

const dotColors: Record<StatusDotColor, string> = {
  green: 'bg-emerald-500',
  yellow: 'bg-amber-500',
  red: 'bg-red-500',
  blue: 'bg-blue-500',
  gray: 'bg-gray-400',
};

interface StatusDotProps {
  color?: StatusDotColor;
  pulse?: boolean;
  className?: string;
}

export function StatusDot({ color = 'green', pulse = false, className = '' }: StatusDotProps) {
  return (
    <span className={`relative inline-flex h-2 w-2 ${className}`}>
      {pulse && (
        <span className={`absolute inline-flex h-full w-full animate-ping rounded-full ${dotColors[color]} opacity-75`} />
      )}
      <span className={`relative inline-flex h-2 w-2 rounded-full ${dotColors[color]}`} />
    </span>
  );
}
