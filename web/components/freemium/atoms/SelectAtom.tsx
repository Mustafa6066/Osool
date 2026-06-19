import React from 'react';
import { ChevronDown } from 'lucide-react';

interface SelectOption {
  value: string;
  label: string;
}

interface SelectAtomProps {
  id: string;
  label: string;
  value: string;
  onChange: (value: string) => void;
  options: SelectOption[];
}

export default function SelectAtom({
  id,
  label,
  value,
  onChange,
  options,
}: SelectAtomProps) {
  return (
    <div className="flex flex-col gap-2">
      <label
        htmlFor={id}
        className="text-[11px] font-semibold uppercase tracking-[0.16em] text-zinc-500"
      >
        {label}
      </label>

      <div className="relative">
        <select
          id={id}
          value={value}
          onChange={(event) => onChange(event.target.value)}
          className="w-full appearance-none rounded-2xl border border-zinc-800/70 bg-zinc-950/90 px-4 py-3 text-sm text-zinc-100 outline-none transition-all duration-200 focus:border-[var(--osool-accent)] focus:ring-2 focus:ring-[var(--osool-accent-mid)]"
        >
          {options.map((option) => (
            <option key={option.value} value={option.value} className="bg-zinc-900">
              {option.label}
            </option>
          ))}
        </select>

        <ChevronDown
          className="pointer-events-none absolute right-3 top-1/2 h-4 w-4 -translate-y-1/2 text-zinc-500"
          aria-hidden="true"
        />
      </div>
    </div>
  );
}
