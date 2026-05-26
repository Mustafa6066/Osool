import React from 'react';

interface GlassPanelProps extends React.HTMLAttributes<HTMLDivElement> {
  as?: 'div' | 'section' | 'article';
}

export default function GlassPanel({
  as = 'div',
  className = '',
  children,
  ...props
}: GlassPanelProps) {
  const Tag = as;

  return (
    <Tag
      className={[
        'rounded-3xl border border-zinc-800/60 bg-zinc-900/40 backdrop-blur-md',
        className,
      ].join(' ')}
      {...props}
    >
      {children}
    </Tag>
  );
}
