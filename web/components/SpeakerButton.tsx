'use client';

import { motion, AnimatePresence } from 'framer-motion';
import { Volume2, Loader2, Pause } from 'lucide-react';
import type { PlaybackStatus } from '@/hooks/useVoicePlayback';

interface SpeakerButtonProps {
  status: PlaybackStatus;
  onClick: () => void;
  isRTL?: boolean;
  className?: string;
}

const BAR_HEIGHTS = [0.4, 0.7, 1.0, 0.7, 0.4];

export default function SpeakerButton({
  status,
  onClick,
  isRTL = false,
  className = '',
}: SpeakerButtonProps) {
  const isPlaying = status === 'playing';
  const isLoading = status === 'loading';
  const isPaused  = status === 'paused';

  return (
    <button
      onClick={onClick}
      aria-label={isRTL ? 'استمع للرد' : 'Listen to response'}
      title={
        isPlaying ? (isRTL ? 'إيقاف مؤقت' : 'Pause')
          : isPaused ? (isRTL ? 'استئناف' : 'Resume')
          : isRTL ? 'استمع للرد' : 'Listen'
      }
      className={`p-1.5 hover:bg-[var(--color-surface)] rounded-lg text-[var(--color-text-muted)] hover:text-[var(--color-text-primary)] transition-colors ${className}`}
    >
      <AnimatePresence mode="wait">
        {isLoading ? (
          <motion.div
            key="loading"
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.8 }}
            transition={{ duration: 0.12 }}
          >
            <motion.div
              animate={{ rotate: 360 }}
              transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
            >
              <Loader2 className="w-3.5 h-3.5" />
            </motion.div>
          </motion.div>
        ) : isPlaying ? (
          <motion.span
            key="bars"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.15 }}
            className="flex items-center gap-[1.5px]"
            style={{ width: 14, height: 14 }}
          >
            {BAR_HEIGHTS.map((h, i) => (
              <motion.span
                key={i}
                animate={{
                  scaleY: [1, h * 1.6, 1],
                  opacity: [0.6, 1, 0.6],
                }}
                transition={{
                  duration: 0.5,
                  repeat: Infinity,
                  ease: 'easeInOut',
                  delay: i * 0.08,
                }}
                style={{
                  display: 'inline-block',
                  width: 2,
                  height: 10,
                  borderRadius: 1,
                  backgroundColor: 'var(--osool-deep-teal, #0d9488)',
                  transformOrigin: 'center center',
                }}
              />
            ))}
          </motion.span>
        ) : isPaused ? (
          <motion.div
            key="paused"
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.8 }}
            transition={{ duration: 0.12 }}
          >
            <Pause className="w-3.5 h-3.5 text-emerald-500" />
          </motion.div>
        ) : (
          <motion.div
            key="idle"
            initial={{ opacity: 0, scale: 0.8 }}
            animate={{ opacity: 1, scale: 1 }}
            exit={{ opacity: 0, scale: 0.8 }}
            transition={{ duration: 0.12 }}
          >
            <Volume2 className="w-3.5 h-3.5" />
          </motion.div>
        )}
      </AnimatePresence>
    </button>
  );
}
