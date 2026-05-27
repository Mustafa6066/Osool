/**
 * Osool icon set — minimal stroke SVG primitives.
 * Port of icons.js from the claude.ai/design handoff.
 *
 * Each export is a React component; pass size + className.
 * All icons inherit `currentColor` for stroke so they tint with text color.
 */

type IconProps = {
  size?: number;
  className?: string;
  strokeWidth?: number;
  style?: React.CSSProperties;
};

function makeIcon(
  paths: string[],
  opts: { fill?: string; stroke?: string } = {},
) {
  return function Icon({
    size = 16,
    className,
    strokeWidth = 1.75,
    style,
  }: IconProps) {
    return (
      <svg
        width={size}
        height={size}
        viewBox="0 0 24 24"
        fill={opts.fill ?? 'none'}
        stroke={opts.stroke ?? 'currentColor'}
        strokeWidth={strokeWidth}
        strokeLinecap="round"
        strokeLinejoin="round"
        className={className}
        style={style}
      >
        {paths.map((d, i) => (
          <path key={i} d={d} />
        ))}
      </svg>
    );
  };
}

export const IconPlus = makeIcon(['M12 5v14', 'M5 12h14']);
export const IconSearch = makeIcon(['M11 19a8 8 0 1 0 0-16 8 8 0 0 0 0 16Z', 'm21 21-4.3-4.3']);
export const IconSpark = makeIcon(['M12 3l1.8 5.4L19 10l-5.2 1.6L12 17l-1.8-5.4L5 10l5.2-1.6L12 3z']);
export const IconCalc = makeIcon([
  'M5 3h14a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2z',
  'M8 7h8',
  'M8 11h2',
  'M12 11h4',
  'M8 15h2',
  'M12 15h4',
]);
export const IconShield = makeIcon(['M12 3 4 6v6c0 5 3.5 8.5 8 9 4.5-.5 8-4 8-9V6l-8-3z']);
export const IconHome = makeIcon(['m3 11 9-8 9 8', 'M5 9.5V21h14V9.5']);
export const IconMic = makeIcon([
  'M12 2a3 3 0 0 0-3 3v7a3 3 0 0 0 6 0V5a3 3 0 0 0-3-3z',
  'M19 10v2a7 7 0 0 1-14 0v-2',
  'M12 19v4',
  'M8 23h8',
]);
export const IconPaperclip = makeIcon([
  'm21 11.5-9.2 9.2a6 6 0 1 1-8.5-8.5l9.2-9.2a4 4 0 1 1 5.7 5.7l-9.3 9.2a2 2 0 0 1-2.8-2.8l8.5-8.5',
]);
export const IconUp = makeIcon(['m6 9 6-6 6 6', 'M12 3v18']);
export const IconWand = makeIcon([
  'm15 4 5 5',
  'm4 21 11.5-11.5',
  'm18 1 1 1',
  'm22 5 1 1',
  'm20 8 1 1',
  'm1 22 1 1',
]);
export const IconSend = makeIcon(['m22 2-7 20-4-9-9-4 20-7z']);
export const IconSparkles = makeIcon([
  'M9 3 10.5 7.5 15 9l-4.5 1.5L9 15l-1.5-4.5L3 9l4.5-1.5L9 3z',
  'M18 13l1 2.5 2.5 1-2.5 1L18 20l-1-2.5L14.5 16.5l2.5-1L18 13z',
]);

// ── Chat-surface additions ─────────────────────────────────────────
export const IconChevDown = makeIcon(['m6 9 6 6 6-6']);
export const IconPanelLeft = makeIcon(['M3 3h18v18H3z', 'M9 3v18']);
export const IconGlobe = makeIcon([
  'M12 22a10 10 0 1 0 0-20 10 10 0 0 0 0 20z',
  'M2 12h20',
  'M12 2a14 14 0 0 1 0 20 14 14 0 0 1 0-20z',
]);
export const IconSun = makeIcon([
  'M12 17a5 5 0 1 0 0-10 5 5 0 0 0 0 10z',
  'M12 2v2',
  'M12 20v2',
  'm4.9 4.9 1.4 1.4',
  'm17.7 17.7 1.4 1.4',
  'M2 12h2',
  'M20 12h2',
  'm4.9 19.1 1.4-1.4',
  'm17.7 6.3 1.4-1.4',
]);
export const IconMoon = makeIcon(['M21 12.8A9 9 0 1 1 11.2 3a7 7 0 0 0 9.8 9.8z']);
export const IconShare = makeIcon([
  'M4 12v8a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-8',
  'm16 6-4-4-4 4',
  'M12 2v13',
]);
export const IconStop = makeIcon(['M5 5h14v14H5z'], { fill: 'currentColor', stroke: 'none' });
export const IconFlag = makeIcon([
  'M4 21V4',
  'M4 5h11l-1.5 4L15 13H4',
]);
export const IconTrending = makeIcon(['M3 17l6-6 4 4 8-8', 'M14 7h7v7']);
export const IconMessageSquare = makeIcon([
  'M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2v10z',
]);
