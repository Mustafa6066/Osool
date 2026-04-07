'use client';

import { motion, AnimatePresence } from 'framer-motion';
import { Mic, Loader2 } from 'lucide-react';
import type { RecordingStatus } from '@/hooks/useVoiceRecording';

interface VoiceOrbProps {
  status: RecordingStatus;
  amplitude: number; // 0–1
  onClick: () => void;
  isRTL?: boolean;
  size?: 'sm' | 'md';
  className?: string;
}

const BAR_MULTIPLIERS = [0.6, 0.9, 1.0, 0.9, 0.6];
const BAR_DURATIONS   = [0.40, 0.38, 0.35, 0.38, 0.40];

export default function VoiceOrb({
  status,
  amplitude,
  onClick,
  isRTL = false,
  size = 'md',
  className = '',
}: VoiceOrbProps) {
  const isRecording  = status === 'recording';
  const isProcessing = status === 'processing';
  const iconSize     = size === 'sm' ? 18 : 20;

  const baseClass =
    size === 'sm'
      ? 'inline-flex min-h-11 min-w-11 p-1.5 transition-colors rounded-full'
      : 'chatgpt-input-btn rounded-full min-h-11 min-w-11';

  return (
    <motion.button
      onClick={onClick}
      aria-label={isRTL ? 'إدخال صوتي' : 'Voice input'}
      title={isRTL ? 'إدخال صوتي' : 'Voice input'}
      className={`relative flex items-center justify-center ${baseClass} ${
        isRecording
          ? 'text-red-500 bg-red-500/10'
          : 'text-[var(--color-text-muted-studio)] hover:text-[var(--osool-deep-teal)]'
      } ${className}`}
      animate={
        isRecording
          ? {
              boxShadow: [
                '0 0 0 0px rgba(20,184,166,0.4)',
                '0 0 0 8px rgba(20,184,166,0)',
              ],
            }
          : { boxShadow: '0 0 0 0px rgba(20,184,166,0)' }
      }
      transition={
        isRecording
          ? { duration: 1.2, repeat: Infinity, ease: 'easeOut' }
          : { duration: 0.3 }
      }
    >
      <AnimatePresence mode="wait">
        {isProcessing ? (
          <motion.div
            key="processing"
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.8 }}
            transition={{ duration: 0.15 }}
          >
            <motion.div
              animate={{ rotate: 360 }}
              transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
            >
              <Loader2 size={iconSize} />
            </motion.div>
          </motion.div>
        ) : isRecording ? (
          <motion.span
            key="waveform"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="flex items-center gap-[2px]"
            style={{ height: iconSize }}
          >
            {BAR_MULTIPLIERS.map((multiplier, i) => (
              <motion.span
                key={i}
                animate={{
                  scaleY: [1, 1 + amplitude * multiplier * 1.8, 1],
                  opacity: [0.7, 1, 0.7],
                }}
                transition={{
                  duration: BAR_DURATIONS[i],
                  repeat: Infinity,
                  ease: 'easeInOut',
                  delay: i * 0.07,
                }}
                style={{
                  display: 'inline-block',
                  width: size === 'sm' ? 2.5 : 3,
                  height: size === 'sm' ? 12 : 14,
                  borderRadius: 2,
                  backgroundColor: 'var(--osool-deep-teal)',
                  transformOrigin: 'center center',
                }}
              />
            ))}
          </motion.span>
        ) : (
          <motion.div
            key="mic"
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.8 }}
            transition={{ duration: 0.15 }}
          >
            <Mic size={iconSize} />
          </motion.div>
        )}
      </AnimatePresence>
    </motion.button>
  );
}
