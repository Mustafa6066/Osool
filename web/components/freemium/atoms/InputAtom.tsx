import React from 'react';

interface InputAtomProps {
  id: string;
  label: string;
  value: string;
  onChange: (value: string) => void;
  placeholder?: string;
  type?: 'text' | 'number';
  suffix?: string;
  error?: string;
  dir?: 'ltr' | 'rtl';
  min?: number;
  max?: number;
  step?: number;
}

export default function InputAtom({
  id,
  label,
  value,
  onChange,
  placeholder,
  type = 'text',
  suffix,
  error,
  dir = 'ltr',
  min,
  max,
  step,
}: InputAtomProps) {
  return (
    <div className="flex flex-col gap-2">
      <label
        htmlFor={id}
        className="text-[11px] font-semibold uppercase tracking-[0.16em] text-zinc-500"
      >
        {label}
      </label>

      <div className="relative">
        <input
          id={id}
          type={type}
          value={value}
          onChange={(event) => onChange(event.target.value)}
          placeholder={placeholder}
          dir={dir}
          min={min}
          max={max}
          step={step}
          aria-invalid={Boolean(error)}
          className={[
            'w-full rounded-2xl border bg-zinc-950/90 px-4 py-3 text-sm text-zinc-100',
            'outline-none transition-all duration-200 placeholder:text-zinc-600',
            suffix ? 'pr-14' : '',
            error
              ? 'border-red-500/50 focus:border-red-500 focus:ring-2 focus:ring-red-500/25'
              : 'border-zinc-800/70 focus:border-emerald-500/55 focus:ring-2 focus:ring-emerald-500/15',
          ].join(' ')}
        />

        {suffix ? (
          <span className="pointer-events-none absolute right-4 top-1/2 -translate-y-1/2 text-xs font-semibold text-zinc-500">
            {suffix}
          </span>
        ) : null}
      </div>

      {error ? <p className="text-xs text-red-400">{error}</p> : null}
    </div>
  );
}
