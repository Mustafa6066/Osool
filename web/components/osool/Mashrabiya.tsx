/**
 * Mashrabiya — geometric latticework pattern as a quiet section
 * watermark. Real Cairo mashrabiya geometry (8-point star repeating
 * across a square lattice), not a Photoshop "Arabian" texture.
 *
 * Used at 5% opacity in light theme, 8% in dark — see .osool-mashrabiya
 * in osool-theme.css. Position the parent element relative; this fills
 * its bounding box, then content above it gets z-index >= 1.
 *
 * Visual restraint is the entire point. If you can see this clearly,
 * the opacity is wrong.
 */

interface MashrabiyaProps {
  /** Width in pixels of one repeat tile. Bigger = sparser pattern. */
  tile?: number;
  className?: string;
}

export default function Mashrabiya({ tile = 64, className }: MashrabiyaProps) {
  const patternId = `mashrabiya-${tile}`;
  return (
    <svg
      className={className ?? 'osool-mashrabiya'}
      aria-hidden="true"
      width="100%"
      height="100%"
      preserveAspectRatio="xMidYMid slice"
    >
      <defs>
        <pattern
          id={patternId}
          x="0"
          y="0"
          width={tile}
          height={tile}
          patternUnits="userSpaceOnUse"
        >
          {/* 8-point star geometry — a square + a 45deg rotated square,
              the classic Islamic-geometry foundation seen in Cairo
              mashrabiya screens, Mamluk tilework, and Mosque of Sultan
              Hassan window frames. */}
          <g
            stroke="currentColor"
            strokeWidth="1"
            fill="none"
            transform={`translate(${tile / 2}, ${tile / 2})`}
          >
            <rect
              x={-tile / 3}
              y={-tile / 3}
              width={(tile / 3) * 2}
              height={(tile / 3) * 2}
            />
            <rect
              x={-tile / 3}
              y={-tile / 3}
              width={(tile / 3) * 2}
              height={(tile / 3) * 2}
              transform="rotate(45)"
            />
            <circle cx="0" cy="0" r={tile / 12} />
          </g>
          {/* Corner dots to tie the lattice together. */}
          <circle cx="0" cy="0" r="1" fill="currentColor" />
          <circle cx={tile} cy="0" r="1" fill="currentColor" />
          <circle cx="0" cy={tile} r="1" fill="currentColor" />
          <circle cx={tile} cy={tile} r="1" fill="currentColor" />
        </pattern>
      </defs>
      <rect width="100%" height="100%" fill={`url(#${patternId})`} />
    </svg>
  );
}
