'use client';

import { useEffect, useRef } from 'react';

const CLICKABLE_SELECTOR = [
  'button',
  'a',
  '[role="button"]',
  'input[type="button"]',
  'input[type="submit"]',
  'input[type="reset"]',
  'summary',
  '[data-haptic]',
].join(',');

function vibrateByLevel(level: string) {
  if (typeof navigator === 'undefined' || typeof navigator.vibrate !== 'function') return;

  if (level === 'heavy') {
    navigator.vibrate([16]);
    return;
  }

  if (level === 'medium') {
    navigator.vibrate([10]);
    return;
  }

  navigator.vibrate([6]);
}

export default function HapticFeedback() {
  const lastTriggerRef = useRef(0);

  useEffect(() => {
    const trigger = (level: string) => {
      const now = Date.now();
      if (now - lastTriggerRef.current < 36) return;
      lastTriggerRef.current = now;
      vibrateByLevel(level);
    };

    const pointerHandler = (event: Event) => {
      const target = event.target as Element | null;
      if (!target) return;

      const clickable = target.closest(CLICKABLE_SELECTOR) as HTMLElement | null;
      if (!clickable) return;

      const level = clickable.dataset.haptic || 'light';
      trigger(level);
    };

    const keyHandler = (event: KeyboardEvent) => {
      if (event.key !== 'Enter' && event.key !== ' ') return;

      const target = document.activeElement as HTMLElement | null;
      if (!target) return;

      const clickable = target.matches(CLICKABLE_SELECTOR)
        ? target
        : (target.closest(CLICKABLE_SELECTOR) as HTMLElement | null);

      if (!clickable) return;

      const level = clickable.dataset.haptic || 'light';
      trigger(level);
    };

    document.addEventListener('pointerdown', pointerHandler, true);
    document.addEventListener('keydown', keyHandler, true);

    return () => {
      document.removeEventListener('pointerdown', pointerHandler, true);
      document.removeEventListener('keydown', keyHandler, true);
    };
  }, []);

  return null;
}
