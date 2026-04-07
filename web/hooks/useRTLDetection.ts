'use client';

import { useCallback } from 'react';
import { useChatStore } from '@/stores/useChatStore';

/**
 * useRTLDetection — Detects and tracks RTL (Arabic) text direction.
 * Combines the explicit isRTL prop with auto-detection from user input.
 */
export function useRTLDetection(isRTL = false) {
  const detectedRTL = useChatStore((s) => s.detectedRTL);
  const setDetectedRTL = useChatStore((s) => s.setDetectedRTL);

  const effectiveRTL = isRTL || detectedRTL;

  const detectFromText = useCallback(
    (text: string) => {
      if (/[\u0600-\u06FF\u0750-\u077F]/.test(text)) {
        setDetectedRTL(true);
      }
    },
    [setDetectedRTL],
  );

  return { effectiveRTL, detectFromText };
}
