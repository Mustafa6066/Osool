'use client';

import { useCallback } from 'react';
import { useChatStore } from '@/stores/useChatStore';

/**
 * useRetry — Retry and regenerate logic for chat messages.
 * Finds the preceding user message and re-sends it.
 */
export function useRetry(send: (content: string) => Promise<void>) {
  const removeMessage = useChatStore((s) => s.removeMessage);

  const retry = useCallback(
    (messageId: string) => {
      const msgs = useChatStore.getState().messages;
      const idx = msgs.findIndex((m) => m.id === messageId);
      if (idx <= 0) return;
      const prevUser = msgs
        .slice(0, idx)
        .reverse()
        .find((m) => m.role === 'user');
      if (!prevUser) return;
      removeMessage(messageId);
      send(prevUser.content);
    },
    [removeMessage, send],
  );

  const regenerate = useCallback(
    (messageId: string) => {
      const msgs = useChatStore.getState().messages;
      const idx = msgs.findIndex((m) => m.id === messageId);
      if (idx <= 0) return;
      const prevUser = msgs
        .slice(0, idx)
        .reverse()
        .find((m) => m.role === 'user');
      if (!prevUser) return;
      removeMessage(messageId);
      send(prevUser.content);
    },
    [removeMessage, send],
  );

  return { retry, regenerate };
}
