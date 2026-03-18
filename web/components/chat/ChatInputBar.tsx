'use client';

import React, { useRef, useEffect, useCallback } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { ArrowUp } from 'lucide-react';
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
}: ChatInputProps) {
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
    <motion.div layoutId="input-bar" className="w-full" transition={{ type: 'spring', damping: 30, stiffness: 300 }}>
      <div
        className={`bg-[var(--color-surface)]/95 backdrop-blur-2xl rounded-[24px] flex flex-col transition-all duration-300 ${
          disabled ? 'opacity-70 scale-[0.99]' : ''
        } shadow-[0_8px_30px_rgba(0,0,0,0.04)] border ${
          isListening
            ? 'border-emerald-500/40 shadow-[0_0_0_3px_rgba(16,185,129,0.06)]'
            : 'border-[var(--color-border)]/40'
        }${transcriptHighlight ? ' ring-2 ring-emerald-500/40' : ''}`}
      >
        {/* Voice status bar */}
        <AnimatePresence>
          {(voiceStatus === 'recording' || voiceStatus === 'processing') && (
            <motion.div
              initial={{ height: 0, opacity: 0 }}
              animate={{ height: 'auto', opacity: 1 }}
              exit={{ height: 0, opacity: 0 }}
              transition={{ duration: 0.25 }}
              className="px-5 pt-3 pb-0 flex items-center gap-2.5 overflow-hidden"
            >
              <VoiceOrb status={voiceStatus} amplitude={amplitude} onClick={onVoiceToggle} isRTL={language === 'ar'} size="sm" />
              <span className="ms-auto text-[11px] text-emerald-600 dark:text-emerald-400 font-semibold animate-pulse flex-shrink-0">
                {voiceStatus === 'processing'
                  ? (language === 'ar' ? 'يعالج...' : 'Transcribing...')
                  : (language === 'ar' ? 'يستمع...' : 'Listening...')}
              </span>
            </motion.div>
          )}
        </AnimatePresence>

        <div className="flex items-end gap-2">
          <textarea
            dir="auto"
            ref={inputRef}
            value={value}
            onChange={(e) => onChange(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={
              language === 'ar'
                ? 'اسأل عن العقارات، بيانات السوق، أو الاستثمار...'
                : 'Ask about properties, market data, or investments...'
            }
            className="flex-1 bg-transparent border-none text-[var(--color-text-primary)] placeholder-[var(--color-text-muted)] focus:ring-0 resize-none py-2.5 md:py-4 px-4 md:px-6 text-[14px] md:text-[15px] max-h-[120px] md:max-h-[180px] outline-none ring-0 leading-normal font-medium"
            rows={1}
            disabled={disabled}
          />

          <div className="flex-shrink-0 pb-2 md:pb-3 pe-2 md:pe-3 flex items-center gap-1.5">
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
              className="p-2 md:p-2.5 bg-gray-900 dark:bg-white text-white dark:text-gray-900 rounded-xl hover:scale-105 active:scale-95 shadow-sm transition-all duration-200 disabled:opacity-20 disabled:pointer-events-none"
            >
              <ArrowUp className="w-4 h-4" strokeWidth={2.5} />
            </button>
          </div>
        </div>
      </div>
    </motion.div>
  );
}
