'use client';

import { useState, useCallback } from 'react';

interface GlossaryEntry {
  term: string;
  arabic: string;
  transliteration: string;
  definition: string;
}

const GLOSSARY: GlossaryEntry[] = [
  { term: 'la2ta', arabic: 'لقطة', transliteration: 'La2ta', definition: 'Catch/bargain deal — a unit priced 10%+ below market value' },
  { term: 'maba7', arabic: 'ماباع', transliteration: "Maba7", definition: 'Sold out — developer inventory depleted' },
  { term: 'noss-tashteeb', arabic: 'نص تشطيب', transliteration: 'Noss-Tashteeb', definition: 'Semi-finished / core & shell — buyer completes interior' },
  { term: 'metshatteb', arabic: 'متشطب', transliteration: 'Metshatteb', definition: 'Fully finished — ready to move in' },
  { term: 'super lux', arabic: 'سوبر لوكس', transliteration: 'Super Lux', definition: 'Premium deluxe finishing grade' },
  { term: 'estilam fawri', arabic: 'استلام فوري', transliteration: 'Estilam Fawri', definition: 'Immediate delivery — unit is ready now' },
  { term: 'ta2seet', arabic: 'تقسيط', transliteration: "Ta2seet", definition: 'Installment payment plan from the developer' },
  { term: 'mo2addam', arabic: 'مقدم', transliteration: "Mo2addam", definition: 'Down payment — initial upfront amount' },
  { term: '3addad', arabic: 'عداد', transliteration: "3addad", definition: 'Utility meters (gas/electric) — proxy for delivery readiness' },
  { term: 'compound', arabic: 'كمباوند', transliteration: 'Compound', definition: 'Gated community with shared amenities and security' },
  { term: 'resale', arabic: 'ريسيل', transliteration: 'Resale', definition: 'Secondary market unit sold by an owner, not the developer' },
  { term: 'overprice', arabic: 'أوفربرايس', transliteration: 'Overprice', definition: 'Unit priced above fair market benchmark' },
  { term: '3a2ed eigari', arabic: 'عائد إيجاري', transliteration: "3a2ed Eigari", definition: 'Rental yield — annual rent as % of purchase price' },
];

// Build regex pattern matching Arabic terms and transliterated terms
const PATTERN = new RegExp(
  `(${GLOSSARY.flatMap(g => [
    g.arabic.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'),
    g.transliteration.replace(/[.*+?^${}()|[\]\\]/g, '\\$&'),
  ]).join('|')})`,
  'gi',
);

function Tooltip({ entry, children }: { entry: GlossaryEntry; children: React.ReactNode }) {
  const [open, setOpen] = useState(false);

  return (
    <span
      className="relative inline-block"
      onMouseEnter={() => setOpen(true)}
      onMouseLeave={() => setOpen(false)}
      onClick={() => setOpen((v) => !v)}
    >
      <span className="border-b border-dotted border-emerald-500/60 cursor-help">
        {children}
      </span>
      {open && (
        <span className="absolute z-50 bottom-full left-1/2 -translate-x-1/2 mb-2 w-64 p-3 rounded-xl bg-[var(--color-surface)] border border-[var(--color-border)] shadow-xl text-sm pointer-events-none">
          <span className="block font-semibold text-emerald-500">{entry.arabic} ({entry.transliteration})</span>
          <span className="block mt-1 text-[var(--color-text-secondary)] text-xs leading-relaxed">
            {entry.definition}
          </span>
        </span>
      )}
    </span>
  );
}

/**
 * Wraps Egyptian real estate terms in a text string with hoverable tooltips.
 * Use on rendered chat messages for English-speaking users.
 */
export function GlossaryAnnotated({ text }: { text: string }) {
  const findEntry = useCallback((match: string): GlossaryEntry | undefined => {
    const lower = match.toLowerCase();
    return GLOSSARY.find(
      (g) =>
        g.arabic === match ||
        g.transliteration.toLowerCase() === lower,
    );
  }, []);

  const parts = text.split(PATTERN);

  return (
    <>
      {parts.map((part, i) => {
        const entry = findEntry(part);
        if (entry) {
          return <Tooltip key={i} entry={entry}>{part}</Tooltip>;
        }
        return <span key={i}>{part}</span>;
      })}
    </>
  );
}

export { GLOSSARY };
