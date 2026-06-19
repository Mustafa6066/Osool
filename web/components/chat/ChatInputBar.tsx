'use client';

import React, { useEffect, useCallback, useState } from 'react';
import { motion, AnimatePresence, useReducedMotion } from 'framer-motion';
import { ArrowUp, Paperclip } from 'lucide-react';
import VoiceOrb from '@/components/VoiceOrb';
import type { RecordingStatus } from '@/hooks/useVoiceRecording';

/* ─── Props ──────────────────────────────────── */
interface ChatInputProps {
  value: string;
  onChange: (value: string) => void;
  onSend: () => void;
  disabled: boolean;
  language: string;
  voiceStatus: RecordingStatus;
  amplitude: number;
  isListening: boolean;
  transcriptHighlight: boolean;
  onVoiceToggle: () => void;
  inputRef: React.RefObject<HTMLTextAreaElement | null>;
  onFileAttach?: () => void;
  placeholder?: string;
}

/* ═══════════════════════════════════════════════
   ChatInput — Floating input bar
   Auto-resizing textarea + voice orb + send button.
   Glassmorphic styling with voice status bar.
   ═══════════════════════════════════════════════ */
export default function ChatInput({
  value,
  onChange,
  onSend,
  disabled,
  language,
  voiceStatus,
  amplitude,
  isListening,
  transcriptHighlight,
  onVoiceToggle,
  inputRef,
  onFileAttach,
  placeholder,
}: ChatInputProps) {
  const reduceMotion = useReducedMotion();
  const [isFocused, setIsFocused] = useState(false);
  const isActive = isFocused || Boolean(value.trim()) || isListening || transcriptHighlight;

  // Auto-resize textarea
  useEffect(() => {
    if (inputRef.current) {
      inputRef.current.style.height = 'auto';
      inputRef.current.style.height = `${Math.min(inputRef.current.scrollHeight, 150)}px`;
    }
  }, [value, inputRef]);

  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        onSend();
      }
    },
    [onSend]
  );

  return (
    <motion.div
      layoutId="input-bar"
      className="w-full"
      animate={reduceMotion ? undefined : { y: isFocused ? -1 : 0 }}
      transition={{ type: 'spring', damping: 28, stiffness: 360 }}
    >
      <div
        className={`relative flex flex-col overflow-hidden rounded-[22px] border bg-[var(--color-surface)]/88 shadow-[0_14px_44px_-36px_rgba(15,23,42,0.5)] backdrop-blur-xl transition-[background-color,border-color,box-shadow,opacity,transform] duration-200 focus-within:border-[var(--osool-accent-mid)] focus-within:bg-[var(--color-surface)]/96 ${
          disabled ? 'opacity-70 scale-[0.99]' : ''
        } ${
          isListening
            ? 'border-[var(--osool-accent-mid)]'
            : 'border-[var(--color-border)]/45'
        }${transcriptHighlight ? ' ring-2 ring-[var(--osool-accent-mid)]' : ''}`}
      >
        <motion.span
          aria-hidden="true"
          className="pointer-events-none absolute inset-x-4 bottom-0 h-px origin-center rounded-full bg-gradient-to-r from-transparent via-[var(--osool-accent)] to-transparent"
          initial={false}
          animate={reduceMotion ? { opacity: isActive ? 1 : 0.35 } : { opacity: isActive ? 1 : 0.25, scaleX: isActive ? 1 : 0.35 }}
          transition={{ duration: reduceMotion ? 0 : 0.22, ease: 'easeOut' }}
        />
        {/* Voice status bar */}
        <AnimatePresence>
          {(voiceStatus === 'recording' || voiceStatus === 'processing') && (
            <motion.div
              initial={{ y: -6, opacity: 0 }}
              animate={{ y: 0, opacity: 1 }}
              exit={{ y: -6, opacity: 0 }}
              transition={{ duration: 0.25 }}
              className="px-5 pt-3 pb-0 flex items-center gap-2.5"
            >
              <VoiceOrb status={voiceStatus} amplitude={amplitude} onClick={onVoiceToggle} isRTL={language === 'ar'} size="sm" />
              <span className="ms-auto text-[11px] text-[var(--osool-accent)] font-semibold animate-pulse flex-shrink-0">
                {voiceStatus === 'processing'
                  ? (language === 'ar' ? 'يعالج...' : 'Transcribing...')
                  : (language === 'ar' ? 'يستمع...' : 'Listening...')}
              </span>
            </motion.div>
          )}
        </AnimatePresence>

        <div className="flex items-end gap-1.5">
          <textarea
            dir="auto"
            ref={inputRef}
            value={value}
            onChange={(e) => onChange(e.target.value)}
            onFocus={() => setIsFocused(true)}
            onBlur={() => setIsFocused(false)}
            onKeyDown={handleKeyDown}
            aria-label={language === 'ar' ? 'اكتب رسالتك' : 'Type your message'}
            placeholder={placeholder ?? (
              language === 'ar'
                ? 'اسأل عن العقارات، بيانات السوق، أو الاستثمار...'
                : 'Ask about properties, market data, or investments...'
            )}
            className="min-h-12 flex-1 resize-none border-none bg-transparent px-4 py-3 text-[15px] font-normal leading-normal text-[var(--color-text-primary)] outline-none ring-0 placeholder:text-[var(--color-text-muted)] focus:ring-0 md:max-h-[170px] md:px-5 md:py-3.5"
            rows={1}
            disabled={disabled}
          />

          <div className="flex flex-shrink-0 items-center gap-1 pb-1.5 pe-1.5 md:pb-2 md:pe-2">
            {onFileAttach && (
              <button
                type="button"
                onClick={onFileAttach}
                aria-label={language === 'ar' ? 'إرفاق ملف' : 'Attach file'}
                title={language === 'ar' ? 'إرفاق ملف' : 'Attach file'}
                className="inline-flex h-11 w-11 items-center justify-center rounded-2xl text-[var(--color-text-muted)] transition-[background-color,color,transform] duration-150 hover:bg-[var(--color-surface-elevated)] hover:text-[var(--color-text-primary)] active:scale-95"
              >
                <Paperclip className="w-4 h-4" strokeWidth={1.8} />
              </button>
            )}
            <VoiceOrb
              status={voiceStatus}
              amplitude={amplitude}
              onClick={onVoiceToggle}
              isRTL={language === 'ar'}
              size="sm"
            />
            <button
              onClick={onSend}
              disabled={disabled || !value.trim()}
              aria-label={language === 'ar' ? 'إرسال الرسالة' : 'Send message'}
              title="Send message"
              className="inline-flex h-11 w-11 items-center justify-center rounded-2xl bg-[var(--color-text-primary)] text-[var(--color-background)] shadow-[0_8px_20px_-16px_rgba(0,0,0,0.75)] transition-[opacity,transform,box-shadow] duration-150 hover:opacity-90 active:scale-95 disabled:pointer-events-none disabled:opacity-20"
            >
              <ArrowUp className="w-4 h-4" strokeWidth={2.5} />
            </button>
          </div>
        </div>
      </div>
    </motion.div>
  );
}
