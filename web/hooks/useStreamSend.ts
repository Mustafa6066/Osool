'use client';

import { useCallback, useRef } from 'react';
import { useChatStore } from '@/stores/useChatStore';
import { useAppStore } from '@/stores/useAppStore';

/**
 * useStreamSend — Manages the send/stop lifecycle with latency tracking.
 * Pure streaming lifecycle, no retry or RTL logic.
 */
export function useStreamSend({
  effectiveRTL,
  onDetectRTL,
}: {
  effectiveRTL: boolean;
  onDetectRTL?: (text: string) => void;
}) {
  const streamStatus = useChatStore((s) => s.streamStatus);
  const sendMessage = useChatStore((s) => s.sendMessage);
  const stopGeneration = useChatStore((s) => s.stopGeneration);
  const { setLastResponseMs } = useAppStore();
  const sendTimestamp = useRef<number | null>(null);

  const send = useCallback(
    async (content: string) => {
      if (!content.trim() || streamStatus === 'streaming' || streamStatus === 'connecting') return;

      onDetectRTL?.(content);
      sendTimestamp.current = performance.now();

      const language: 'ar' | 'en' | 'auto' = effectiveRTL ? 'ar' : 'auto';
      await sendMessage(content, language);

      if (sendTimestamp.current) {
        const elapsed = performance.now() - sendTimestamp.current;
        setLastResponseMs(elapsed);
        sendTimestamp.current = null;
      }
    },
    [streamStatus, effectiveRTL, sendMessage, setLastResponseMs, onDetectRTL],
  );

  const stop = useCallback(() => {
    stopGeneration();
  }, [stopGeneration]);

  const isStreaming =
    streamStatus === 'streaming' || streamStatus === 'connecting' || streamStatus === 'tool-running';

  return { send, stop, isStreaming, streamStatus };
}
