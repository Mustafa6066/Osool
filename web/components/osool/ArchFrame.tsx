/**
 * ArchFrame — signature arch-top card shape. Rounded at the top
 * corners (24px), square at the bottom. Echoes the OsoolAvatar
 * doorway and gives the brand a distinctive silhouette without
 * shouting "Arabian." Reserve for 1-2 uses per page — typically
 * the hero composer panel or a premium upgrade callout. Used
 * everywhere it stops being a signature.
 *
 * The stroke-draw animation on the inner arch outline plays once
 * when this frame scrolls into view via the .osool-reveal observer
 * already wired in the landing page.
 */

import { ReactNode } from 'react';

interface ArchFrameProps {
  children: ReactNode;
  className?: string;
  /** When true, render a hairline arch outline along the curved top.
      The line uses the arch stroke-draw motion. Default false. */
  outline?: boolean;
  /** Forward additional inline styles (e.g. background gradient). */
  style?: React.CSSProperties;
}

export default function ArchFrame({
  children,
  className,
  outline = false,
  style,
}: ArchFrameProps) {
  return (
    <div
      className={'osool-arch-top ' + (className ?? '')}
      style={{
        position: 'relative',
        background: 'var(--osool-surface)',
        border: '1px solid var(--osool-border)',
        overflow: 'hidden',
        ...style,
      }}
    >
      {outline && (
        <svg
          aria-hidden="true"
          width="100%"
          height="56"
          viewBox="0 0 400 56"
          preserveAspectRatio="none"
          style={{
            position: 'absolute',
            top: 0,
            left: 0,
            pointerEvents: 'none',
          }}
        >
          {/* Draws the arch curve in terracotta at 30% opacity.
              Width is responsive; the curve scales to the frame. */}
          <path
            className="osool-arch-stroke"
            d="M0,56 L0,24 Q0,0 200,0 Q400,0 400,24 L400,56"
            fill="none"
            stroke="var(--osool-accent)"
            strokeWidth="1.5"
            opacity="0.35"
          />
        </svg>
      )}
      {children}
    </div>
  );
}
