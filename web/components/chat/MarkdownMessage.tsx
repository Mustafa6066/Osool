'use client';

import React from 'react';
import ReactMarkdown from 'react-markdown';
import remarkGfm from 'remark-gfm';
import { isArabic, normalizeMarkdown } from '@/lib/chat-utils';
import { GlossaryAnnotated } from '@/components/GlossaryTooltip';

/* ═══════════════════════════════════════════════
   MarkdownMessage — Rich markdown renderer
   Handles RTL, tables, glossary annotations,
   code blocks, and all standard markdown elements.
   ═══════════════════════════════════════════════ */
interface MarkdownMessageProps {
  content: string;
}

export default function MarkdownMessage({ content }: MarkdownMessageProps) {
  const msgIsArabic = isArabic(content);
  const normalized = normalizeMarkdown(content);

  return (
    <div dir={msgIsArabic ? 'rtl' : 'ltr'} className={msgIsArabic ? 'text-end' : 'text-start'}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        components={{
          p: ({ node, children, ...props }) => {
            if (!msgIsArabic) {
              const annotated = React.Children.map(children, (child, i) =>
                typeof child === 'string'
                  ? <GlossaryAnnotated key={i} text={child} />
                  : child
              );
              return <p className="mb-1.5 md:mb-3 last:mb-0 leading-[1.6] md:leading-relaxed text-start" {...props}>{annotated}</p>;
            }
            return <p className="mb-1.5 md:mb-3 last:mb-0 leading-[1.6] md:leading-relaxed text-end" {...props}>{children}</p>;
          },
          ul: ({ node, ...props }) => (
            <ul className="list-disc mb-2 md:mb-3 space-y-0.5 md:space-y-1 ps-5" {...props} />
          ),
          ol: ({ node, ...props }) => (
            <ol className="list-decimal mb-2 md:mb-3 space-y-0.5 md:space-y-1 ps-5" {...props} />
          ),
          li: ({ node, ...props }) => <li className="mb-0.5 md:mb-1" {...props} />,
          strong: ({ node, ...props }) => (
            <strong className="font-semibold text-[var(--color-text-primary)]" {...props} />
          ),
          em: ({ node, ...props }) => (
            <em className="italic text-[var(--color-text-secondary)]" {...props} />
          ),
          h1: ({ node, ...props }) => <h1 className="text-xl font-semibold mb-2 md:mb-3 mt-3 md:mt-4" {...props} />,
          h2: ({ node, ...props }) => <h2 className="text-lg font-semibold mb-1.5 md:mb-2 mt-2 md:mt-3" {...props} />,
          h3: ({ node, ...props }) => <h3 className="text-base font-medium mb-1.5 md:mb-2 mt-1.5 md:mt-2" {...props} />,
          blockquote: ({ node, ...props }) => (
            <blockquote
              className="border-s-2 ps-4 border-emerald-500/40 py-1 my-2 text-[var(--color-text-secondary)]"
              {...props}
            />
          ),
          a: ({ node, ...props }) => (
            <a className="text-emerald-600 dark:text-emerald-400 hover:underline underline-offset-2" target="_blank" rel="noopener noreferrer" {...props} />
          ),
          code: ({ node, className, children, ...props }) => {
            const isInline = !className;
            return isInline ? (
              <code className="bg-[var(--color-surface-elevated)] text-[var(--color-text-primary)] px-1.5 py-0.5 rounded text-[13px] font-mono" {...props}>{children}</code>
            ) : (
              <pre className="bg-[var(--color-surface)] border border-[var(--color-border)] rounded-xl p-4 my-3 overflow-x-auto">
                <code className="text-sm text-[var(--color-text-secondary)] font-mono" {...props}>{children}</code>
              </pre>
            );
          },
          hr: ({ node, ...props }) => <hr className="border-[var(--color-border)] my-4" {...props} />,
          table: ({ node, ...props }) => (
            <div className="overflow-x-auto my-3 rounded-lg border border-[var(--color-border)]">
              <table className="w-full border-collapse text-sm" {...props} />
            </div>
          ),
          th: ({ node, ...props }) => (
            <th className="border-b border-[var(--color-border)] bg-[var(--color-surface)] px-3 py-2.5 text-start text-[var(--color-text-primary)] font-medium text-xs uppercase tracking-wider" {...props} />
          ),
          td: ({ node, ...props }) => (
            <td className="border-b border-[var(--color-border)] px-3 py-2.5 text-[var(--color-text-secondary)]" {...props} />
          ),
        }}
      >
        {normalized}
      </ReactMarkdown>
    </div>
  );
}
