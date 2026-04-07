'use client';

import { useChatStore } from '@/stores/useChatStore';
import { useRTLDetection } from './useRTLDetection';
import { useStreamSend } from './useStreamSend';
import { useRetry } from './useRetry';

/**
 * useStreamingChat — High-level hook that composes granular hooks
 * (useRTLDetection, useStreamSend, useRetry) into a single interface
 * for streaming chat. Inspired by src/QueryEngine.ts.
 */
export function useStreamingChat({ isRTL = false }: { isRTL?: boolean } = {}) {
  const {
    messages,
    activeTool,
    suggestions,
    streamingMessageId,
    clearMessages,
    copyMessage,
    setFeedback,
  } = useChatStore();

  const { effectiveRTL, detectFromText } = useRTLDetection(isRTL);

  const { send, stop, isStreaming, streamStatus } = useStreamSend({
    effectiveRTL,
    onDetectRTL: detectFromText,
  });

  const { retry, regenerate } = useRetry(send);

  const hasMessages = messages.length > 0;

  return {
    // State
    messages,
    streamStatus,
    activeTool,
    suggestions,
    streamingMessageId,
    effectiveRTL,
    isStreaming,
    hasMessages,

    // Actions
    send,
    stop,
    retry,
    regenerate,
    clearMessages,
    copyMessage,
    setFeedback,
  };
}
