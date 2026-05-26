'use client';

import { useState, useRef, useCallback, useEffect } from 'react';

export type RecordingStatus =
  | 'idle'
  | 'requesting-permission'
  | 'recording'
  | 'processing'
  | 'error';

export interface UseVoiceRecordingOptions {
  language: 'ar-EG' | 'en-US' | 'auto';
  silenceThresholdMs?: number;
  silenceVolumeLevel?: number;
  onTranscript: (text: string) => void;
  onError?: (message: string) => void;
}

export interface UseVoiceRecordingReturn {
  status: RecordingStatus;
  isListening: boolean;
  amplitude: number;
  startRecording: () => Promise<void>;
  stopRecording: () => void;
  cancelRecording: () => void;
}

function getSupportedMimeType(): string | null {
  const types = [
    'audio/webm;codecs=opus',
    'audio/webm',
    'audio/mp4',
    'audio/ogg;codecs=opus',
    'audio/ogg',
  ];
  for (const type of types) {
    if (typeof MediaRecorder !== 'undefined' && MediaRecorder.isTypeSupported(type)) {
      return type;
    }
  }
  return null;
}

function mimeToExt(mimeType: string): string {
  if (mimeType.startsWith('audio/webm')) return 'webm';
  if (mimeType.startsWith('audio/mp4')) return 'mp4';
  if (mimeType.startsWith('audio/ogg')) return 'ogg';
  return 'webm';
}

export function useVoiceRecording(options: UseVoiceRecordingOptions): UseVoiceRecordingReturn {
  const {
    language,
    silenceThresholdMs = 2000,
    silenceVolumeLevel = 8,
    onTranscript,
    onError,
  } = options;

  const [status, setStatus] = useState<RecordingStatus>('idle');
  const [amplitude, setAmplitude] = useState(0);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const streamRef = useRef<MediaStream | null>(null);
  const audioCtxRef = useRef<AudioContext | null>(null);
  const silenceIntervalRef = useRef<ReturnType<typeof setInterval> | null>(null);
  const silenceSinceRef = useRef<number | null>(null);
  const chunksRef = useRef<Blob[]>([]);
  const abortRef = useRef<AbortController | null>(null);
  const recognitionRef = useRef<SpeechRecognition | null>(null);

  const cleanup = useCallback(() => {
    if (silenceIntervalRef.current) {
      clearInterval(silenceIntervalRef.current);
      silenceIntervalRef.current = null;
    }
    if (audioCtxRef.current) {
      audioCtxRef.current.close().catch(() => {});
      audioCtxRef.current = null;
    }
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((t) => t.stop());
      streamRef.current = null;
    }
    if (recognitionRef.current) {
      recognitionRef.current.abort();
      recognitionRef.current = null;
    }
    chunksRef.current = [];
    silenceSinceRef.current = null;
    setAmplitude(0);
  }, []);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      cleanup();
      abortRef.current?.abort();
    };
  }, [cleanup]);

  const sendToWhisper = useCallback(
    async (chunks: Blob[], mimeType: string) => {
      setStatus('processing');
      abortRef.current = new AbortController();

      try {
        const blob = new Blob(chunks, { type: mimeType });
        const ext = mimeToExt(mimeType);
        const formData = new FormData();
        formData.append('audio', blob, `recording.${ext}`);
        // Empty string = Whisper auto-detect (best for Franco-Arab mixed speech)
        const langCode =
          language === 'auto' ? '' : language === 'ar-EG' ? 'ar' : 'en';
        formData.append('language', langCode);

        const res = await fetch('/api/transcribe', {
          method: 'POST',
          body: formData,
          signal: abortRef.current.signal,
        });

        if (!res.ok) {
          const body = await res.text().catch(() => 'Unknown error');
          throw new Error(body);
        }

        const { text } = (await res.json()) as { text: string };
        onTranscript(text);
        navigator.vibrate?.([30, 20, 30]);
        setStatus('idle');
      } catch (err: unknown) {
        if (err instanceof Error && err.name === 'AbortError') {
          setStatus('idle');
          return;
        }
        const message = err instanceof Error ? err.message : 'Transcription failed';
        onError?.(message);
        setStatus('idle');
      }
    },
    [language, onTranscript, onError]
  );

  const startFallback = useCallback(() => {
    const SpeechRecognitionCtor =
      typeof window !== 'undefined'
        ? window.SpeechRecognition || window.webkitSpeechRecognition
        : null;

    if (!SpeechRecognitionCtor) {
      onError?.('Voice input is not supported in this browser.');
      setStatus('error');
      return;
    }

    const recognition = new SpeechRecognitionCtor();
    recognition.lang = language === 'auto' || language === 'ar-EG' ? 'ar-EG' : 'en-US';
    recognition.interimResults = true;
    recognition.continuous = false;
    recognition.onstart = () => setStatus('recording');
    recognition.onresult = (event: SpeechRecognitionEvent) => {
      const transcript = Array.from(event.results)
        .map((r) => r[0].transcript)
        .join('');
      if (event.results[0]?.isFinal) {
        onTranscript(transcript);
        setStatus('idle');
      }
    };
    recognition.onerror = () => setStatus('idle');
    recognition.onend = () => setStatus('idle');

    recognitionRef.current = recognition;
    recognition.start();
  }, [language, onTranscript, onError]);

  const setupSilenceDetection = useCallback(
    (stream: MediaStream) => {
      try {
        const audioCtx = new AudioContext();
        audioCtxRef.current = audioCtx;
        const source = audioCtx.createMediaStreamSource(stream);
        const analyser = audioCtx.createAnalyser();
        analyser.fftSize = 256;
        const bufferLength = analyser.frequencyBinCount;
        const dataArray = new Uint8Array(bufferLength);
        source.connect(analyser);

        silenceIntervalRef.current = setInterval(() => {
          analyser.getByteFrequencyData(dataArray);
          const avg = dataArray.reduce((sum, v) => sum + v, 0) / bufferLength;
          setAmplitude(avg / 128);

          if (avg < silenceVolumeLevel) {
            if (silenceSinceRef.current === null) {
              silenceSinceRef.current = Date.now();
            } else if (Date.now() - silenceSinceRef.current > silenceThresholdMs) {
              stopRecordingRef.current?.();
            }
          } else {
            silenceSinceRef.current = null;
          }
        }, 200);
      } catch {
        // AudioContext not available — silence detection skipped, user must stop manually
      }
    },
    [silenceVolumeLevel, silenceThresholdMs]
  );

  // Use a ref to avoid stale closure in the silence detection interval
  const stopRecordingRef = useRef<(() => void) | null>(null);

  const stopRecording = useCallback(() => {
    if (recognitionRef.current) {
      recognitionRef.current.stop();
      return;
    }
    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      // Collect remaining chunk, then onstop fires sendToWhisper
      mediaRecorderRef.current.stop();
    }
    if (silenceIntervalRef.current) {
      clearInterval(silenceIntervalRef.current);
      silenceIntervalRef.current = null;
    }
    if (audioCtxRef.current) {
      audioCtxRef.current.close().catch(() => {});
      audioCtxRef.current = null;
    }
    if (streamRef.current) {
      streamRef.current.getTracks().forEach((t) => t.stop());
      streamRef.current = null;
    }
    setAmplitude(0);
  }, []);

  useEffect(() => {
    stopRecordingRef.current = stopRecording;
  }, [stopRecording]);

  const cancelRecording = useCallback(() => {
    abortRef.current?.abort();
    cleanup();
    mediaRecorderRef.current?.stop();
    mediaRecorderRef.current = null;
    setStatus('idle');
  }, [cleanup]);

  const startRecording = useCallback(async () => {
    if (status !== 'idle' && status !== 'error') return;

    setStatus('requesting-permission');

    // Try MediaRecorder path first
    const mimeType = getSupportedMimeType();
    if (!mimeType || typeof MediaRecorder === 'undefined') {
      startFallback();
      return;
    }

    let stream: MediaStream;
    try {
      stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    } catch {
      onError?.('Microphone permission denied.');
      setStatus('idle');
      return;
    }

    streamRef.current = stream;
    navigator.vibrate?.([50]);

    chunksRef.current = [];
    const recorder = new MediaRecorder(stream, { mimeType });
    mediaRecorderRef.current = recorder;

    recorder.ondataavailable = (e) => {
      if (e.data.size > 0) chunksRef.current.push(e.data);
    };

    recorder.onstop = () => {
      const captured = [...chunksRef.current];
      chunksRef.current = [];
      if (captured.length > 0) {
        sendToWhisper(captured, mimeType);
      } else {
        setStatus('idle');
      }
    };

    recorder.start(250);
    setStatus('recording');
    setupSilenceDetection(stream);
  }, [status, startFallback, onError, sendToWhisper, setupSilenceDetection]);

  return {
    status,
    isListening: status === 'recording',
    amplitude,
    startRecording,
    stopRecording,
    cancelRecording,
  };
}
