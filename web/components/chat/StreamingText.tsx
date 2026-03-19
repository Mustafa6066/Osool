'use client';

import { useState, useEffect, useRef } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { sanitizeAgentContent } from '@/lib/chat-utils';
import MarkdownMessage from './MarkdownMessage';

/* ─── Typewriter hook — character-by-character reveal ─── */
function useTypewriter(text: string, enabled: boolean, speed = 16) {
  const [displayed, setDisplayed] = useState(text);
  const [done, setDone] = useState(!enabled);
  const idx = useRef(0);

  useEffect(() => {
    let interval: ReturnType<typeof setInterval> | null = null;
    const timer = window.setTimeout(() => {
      if (!enabled) {
        setDisplayed(text);
        setDone(true);
        return;
      }

      idx.current = 0;
      setDisplayed('');
      setDone(false);
      const step = text.length > 800 ? 4 : text.length > 400 ? 3 : 2;
      interval = setInterval(() => {
        idx.current = Math.min(text.length, idx.current + step);
        if (idx.current >= text.length) {
          setDisplayed(text);
          setDone(true);
          if (interval) clearInterval(interval);
        } else {
          setDisplayed(text.slice(0, idx.current));
        }
      }, speed);
    }, 0);

    return () => {
      window.clearTimeout(timer);
      if (interval) clearInterval(interval);
    };
  }, [text, enabled, speed]);

  return { displayed, done };
}

/* ─── Spring presets ─────────────────────────── */
const CURSOR_SPRING = { type: 'spring' as const, damping: 20, stiffness: 300 };

/* ═══════════════════════════════════════════════
   StreamingText — Framer-animated typewriter effect
   Shows characters appearing with an animated cursor.
   Falls back to full MarkdownMessage once complete.
   ═══════════════════════════════════════════════ */
interface StreamingTextProps {
  content: string;
  animate: boolean;
  forceRTL?: boolean;
}

export default function StreamingText({ content, animate, forceRTL = false }: StreamingTextProps) {
  const sanitized = sanitizeAgentContent(content);
  const { displayed, done } = useTypewriter(sanitized, animate, 16);

  // Once done, render the full markdown
  if (done) {
    return <MarkdownMessage content={sanitized} forceRTL={forceRTL} />;
  }

  // While streaming: raw text with animated cursor
  const isRTL = forceRTL || /[\u0600-\u06FF]/.test(displayed);

  return (
    <div dir={isRTL ? 'rtl' : 'ltr'} className={isRTL ? 'text-end' : 'text-start'}>
      <div className="whitespace-pre-wrap leading-relaxed text-[15px] text-[var(--color-text-secondary)]">
        {displayed}
        {/* Animated cursor — pulses while streaming */}
        <AnimatePresence>
          <motion.span
            initial={{ opacity: 0, scaleY: 0.5 }}
            animate={{ opacity: [0.4, 1, 0.4], scaleY: 1 }}
            transition={{
              opacity: { duration: 0.8, repeat: Infinity, ease: 'easeInOut' },
              scaleY: CURSOR_SPRING,
            }}
            className="inline-block w-[2px] h-[1.1em] bg-emerald-500 align-text-bottom ms-0.5 rounded-full"
          />
        </AnimatePresence>
      </div>
    </div>
  );
}
