import { useState, useEffect, useRef, useCallback } from 'react';

export interface UseVoiceInputReturn {
    isListening: boolean;
    transcript: string;
    interimTranscript: string;
    error: string | null;
    supported: boolean;
    start: (lang?: string) => void;
    stop: () => void;
    cancel: () => void;
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
function getSpeechRecognitionCtor(): any | null {
    if (typeof window === 'undefined') return null;
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    return (window as any).SpeechRecognition ?? (window as any).webkitSpeechRecognition ?? null;
}

export function useVoiceInput(): UseVoiceInputReturn {
    const [isListening, setIsListening] = useState(false);
    const [transcript, setTranscript] = useState('');
    const [interimTranscript, setInterimTranscript] = useState('');
    const [error, setError] = useState<string | null>(null);
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    const recognitionRef = useRef<any>(null);

    const supported = !!getSpeechRecognitionCtor();

    const cleanup = useCallback(() => {
        if (recognitionRef.current) {
            recognitionRef.current.onresult = null;
            recognitionRef.current.onerror = null;
            recognitionRef.current.onend = null;
            recognitionRef.current.abort();
            recognitionRef.current = null;
        }
        setIsListening(false);
        setInterimTranscript('');
    }, []);

    useEffect(() => () => cleanup(), [cleanup]);

    const start = useCallback((lang = 'ar-EG') => {
        const Ctor = getSpeechRecognitionCtor();
        if (!Ctor) return;

        cleanup();
        setError(null);
        setTranscript('');
        setInterimTranscript('');

        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        const recognition: any = new Ctor();
        recognition.continuous = false;
        recognition.interimResults = true;
        recognition.lang = lang;
        recognition.maxAlternatives = 1;

        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        recognition.onresult = (event: any) => {
            let finalText = '';
            let interimText = '';
            for (let i = event.resultIndex; i < event.results.length; i++) {
                const result = event.results[i];
                if (result.isFinal) {
                    finalText += result[0].transcript;
                } else {
                    interimText += result[0].transcript;
                }
            }
            if (finalText) setTranscript((prev) => (prev + ' ' + finalText).trim());
            setInterimTranscript(interimText);
        };

        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        recognition.onerror = (event: any) => {
            if (event.error === 'no-speech' || event.error === 'aborted') {
                setError(null);
            } else {
                setError(String(event.error));
            }
            setIsListening(false);
            setInterimTranscript('');
        };

        recognition.onend = () => {
            setIsListening(false);
            setInterimTranscript('');
        };

        recognitionRef.current = recognition;
        recognition.start();
        setIsListening(true);
    }, [cleanup]);

    const stop = useCallback(() => {
        if (recognitionRef.current) {
            recognitionRef.current.stop();
        }
        setIsListening(false);
        setInterimTranscript('');
    }, []);

    const cancel = useCallback(() => {
        cleanup();
        setTranscript('');
    }, [cleanup]);

    return { isListening, transcript, interimTranscript, error, supported, start, stop, cancel };
}
