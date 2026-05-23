import React from 'react';
import { LayoutGrid, Table2 } from 'lucide-react';

interface LayoutModeSwitchProps {
  mode: 'homebuyer' | 'investor';
  onChange: (mode: 'homebuyer' | 'investor') => void;
  homebuyerLabel: string;
  investorLabel: string;
}

export default function LayoutModeSwitch({
  mode,
  onChange,
  homebuyerLabel,
  investorLabel,
}: LayoutModeSwitchProps) {
  return (
    <div className="inline-flex items-center rounded-2xl border border-zinc-800/70 bg-zinc-900/70 p-1 backdrop-blur-md">
      <button
        type="button"
        onClick={() => onChange('homebuyer')}
        className={[
          'inline-flex items-center gap-1.5 rounded-xl px-3 py-2 text-xs font-semibold transition-all duration-200',
          mode === 'homebuyer'
            ? 'bg-zinc-800 text-zinc-100 shadow-[0_8px_24px_rgba(0,0,0,0.25)]'
            : 'text-zinc-400 hover:text-zinc-200',
        ].join(' ')}
        aria-pressed={mode === 'homebuyer'}
      >
        <LayoutGrid className="h-3.5 w-3.5" aria-hidden="true" />
        {homebuyerLabel}
      </button>

      <button
        type="button"
        onClick={() => onChange('investor')}
        className={[
          'inline-flex items-center gap-1.5 rounded-xl px-3 py-2 text-xs font-semibold transition-all duration-200',
          mode === 'investor'
            ? 'bg-zinc-800 text-zinc-100 shadow-[0_8px_24px_rgba(0,0,0,0.25)]'
            : 'text-zinc-400 hover:text-zinc-200',
        ].join(' ')}
        aria-pressed={mode === 'investor'}
      >
        <Table2 className="h-3.5 w-3.5" aria-hidden="true" />
        {investorLabel}
      </button>
    </div>
  );
}
