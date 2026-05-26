'use client';

import { useEffect, useMemo, useRef, useState } from 'react';

interface OsoolAvatarProps {
  size?: number;
  animated?: boolean;
  state?: 'idle' | 'thinking';
  className?: string;
}

/**
 * Osool — animated mascot. Blinks naturally, tracks the cursor with its eyes,
 * idles with a tiny sparkle. Pass state="thinking" to wake it up.
 *
 * Port of avatar.jsx from the claude.ai/design handoff. Pure SVG + a single
 * useEffect for cursor tracking; respects prefers-reduced-motion.
 */
export default function OsoolAvatar({
  size = 28,
  animated = false,
  state = 'idle',
  className,
}: OsoolAvatarProps) {
  const ref = useRef<SVGSVGElement>(null);

  // Per-instance random offsets so multiple avatars don't blink in sync
  const seed = useMemo(
    () => ({
      blink: (Math.random() * 4 + 2.5).toFixed(2), // 2.5–6.5s between blinks
      sparkle: (Math.random() * 2).toFixed(2),
    }),
    [],
  );

  const [eye, setEye] = useState({ x: 0, y: 0 });

  useEffect(() => {
    if (!animated) return;
    if (typeof window === 'undefined') return;
    if (window.matchMedia?.('(prefers-reduced-motion: reduce)').matches) return;

    let raf = 0;
    const onMove = (e: MouseEvent) => {
      cancelAnimationFrame(raf);
      raf = requestAnimationFrame(() => {
        const el = ref.current;
        if (!el) return;
        const r = el.getBoundingClientRect();
        if (!r.width) return;
        const cx = r.left + r.width / 2;
        const cy = r.top + r.height * 0.55;
        const dx = e.clientX - cx;
        const dy = e.clientY - cy;
        const dist = Math.hypot(dx, dy) || 1;
        const max = 1.4; // px in viewBox units
        const reach = Math.min(1, dist / 480);
        setEye({
          x: (dx / dist) * max * reach,
          y: (dy / dist) * max * reach * 0.7,
        });
      });
    };
    window.addEventListener('mousemove', onMove, { passive: true });
    return () => {
      window.removeEventListener('mousemove', onMove);
      cancelAnimationFrame(raf);
    };
  }, [animated]);

  const eyeCls = animated
    ? state === 'thinking'
      ? 'osool-eyes osool-eyes-thinking'
      : 'osool-eyes'
    : '';
  const sparkCls = animated ? 'osool-sparkle' : '';

  return (
    <svg
      ref={ref}
      width={size}
      height={size}
      viewBox="0 0 40 40"
      fill="none"
      aria-hidden="true"
      className={className}
      style={{ overflow: 'visible' }}
    >
      {/* Sparkle — 4-point AI star above the arch */}
      <g
        className={sparkCls}
        style={{ animationDelay: `${seed.sparkle}s`, transformOrigin: '20px 6.25px' }}
      >
        <path
          d="M20 2.6 Q20.5 5.4, 23.2 6.25 Q20.5 7.1, 20 9.9 Q19.5 7.1, 16.8 6.25 Q19.5 5.4, 20 2.6 Z"
          fill="currentColor"
        />
      </g>

      {/* The arched doorway */}
      <g>
        <path
          d="M9 31 L 9 19.5 C 9 13.8, 14 11, 20 11 C 26 11, 31 13.8, 31 19.5 L 31 31"
          stroke="currentColor"
          strokeWidth="1.9"
          strokeLinecap="round"
          strokeLinejoin="round"
        />
        <path
          d="M5.5 31.5 L 34.5 31.5"
          stroke="currentColor"
          strokeWidth="1.9"
          strokeLinecap="round"
        />
      </g>

      {/* Eyes — outer translates for cursor tracking; inner blinks */}
      <g
        style={{
          transform: `translate(${eye.x}px, ${eye.y}px)`,
          transition: 'transform 240ms cubic-bezier(.4,.0,.2,1)',
        }}
      >
        <g className={eyeCls} style={{ animationDelay: `${seed.blink}s` }}>
          <circle cx="15" cy="21.5" r="1.4" fill="currentColor" />
          <circle cx="25" cy="21.5" r="1.4" fill="currentColor" />
        </g>
      </g>
    </svg>
  );
}
