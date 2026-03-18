'use client';

import { useState, useRef, useCallback, useEffect } from 'react';

export type PlaybackStatus = 'idle' | 'loading' | 'playing' | 'paused' | 'error';

export interface UseVoicePlaybackReturn {
  playbackStatus: PlaybackStatus;
  isPlaying: boolean;
  speak: (text: string, language: string) => Promise<void>;
  pause: () => void;
  resume: () => void;
  stop: () => void;
}

/** Cost-guard: truncate long messages to keep TTS affordable */
const TTS_MAX_CHARS = 500;

export function useVoicePlayback(): UseVoicePlaybackReturn {
  const [playbackStatus, setPlaybackStatus] = useState<PlaybackStatus>('idle');
  const audioRef = useRef<HTMLAudioElement | null>(null);
  const abortRef = useRef<AbortController | null>(null);
  const cacheRef = useRef<{ key: string; url: string } | null>(null);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      abortRef.current?.abort();
      if (audioRef.current) {
        audioRef.current.pause();
        audioRef.current.src = '';
      }
      if (cacheRef.current) {
        URL.revokeObjectURL(cacheRef.current.url);
      }
    };
  }, []);

  const stop = useCallback(() => {
    abortRef.current?.abort();
    if (audioRef.current) {
      audioRef.current.pause();
      audioRef.current.currentTime = 0;
    }
    setPlaybackStatus('idle');
  }, []);

  const pause = useCallback(() => {
    if (audioRef.current && playbackStatus === 'playing') {
      audioRef.current.pause();
      setPlaybackStatus('paused');
    }
  }, [playbackStatus]);

  const resume = useCallback(() => {
    if (audioRef.current && playbackStatus === 'paused') {
      audioRef.current.play().catch(() => setPlaybackStatus('error'));
      setPlaybackStatus('playing');
    }
  }, [playbackStatus]);

  const speak = useCallback(async (text: string, language: string) => {
    // If already playing, stop first
    stop();

    const truncated = text.slice(0, TTS_MAX_CHARS);
    const cacheKey = `${language}:${truncated}`;

    // Reuse cached blob if same text
    if (cacheRef.current?.key === cacheKey) {
      const audio = new Audio(cacheRef.current.url);
      audioRef.current = audio;
      audio.onended = () => setPlaybackStatus('idle');
      audio.onerror = () => setPlaybackStatus('error');
      setPlaybackStatus('playing');
      await audio.play().catch(() => setPlaybackStatus('error'));
      return;
    }

    setPlaybackStatus('loading');
    abortRef.current = new AbortController();

    try {
      const res = await fetch('/api/tts', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ text: truncated, language }),
        signal: abortRef.current.signal,
      });

      if (!res.ok) {
        throw new Error(await res.text().catch(() => 'TTS request failed'));
      }

      const blob = await res.blob();
      // Revoke previous cache
      if (cacheRef.current) URL.revokeObjectURL(cacheRef.current.url);
      const url = URL.createObjectURL(blob);
      cacheRef.current = { key: cacheKey, url };

      const audio = new Audio(url);
      audioRef.current = audio;
      audio.onended = () => setPlaybackStatus('idle');
      audio.onerror = () => setPlaybackStatus('error');

      setPlaybackStatus('playing');
      await audio.play();
    } catch (err: unknown) {
      if (err instanceof Error && err.name === 'AbortError') {
        setPlaybackStatus('idle');
        return;
      }
      console.warn('[TTS]', err);
      setPlaybackStatus('error');
    }
  }, [stop]);

  return {
    playbackStatus,
    isPlaying: playbackStatus === 'playing',
    speak,
    pause,
    resume,
    stop,
  };
}
