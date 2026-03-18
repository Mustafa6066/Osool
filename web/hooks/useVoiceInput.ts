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

declare global {
    interface Window {
        SpeechRecognition?: typeof SpeechRecognition;
        webkitSpeechRecognition?: typeof SpeechRecognition;
    }
}

export function useVoiceInput(): UseVoiceInputReturn {
    const [isListening, setIsListening] = useState(false);
    const [transcript, setTranscript] = useState('');
    const [interimTranscript, setInterimTranscript] = useState('');
    const [error, setError] = useState<string | null>(null);
    const recognitionRef = useRef<SpeechRecognition | null>(null);

    const supported = typeof window !== 'undefined'
        && ('SpeechRecognition' in window || 'webkitSpeechRecognition' in window);

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
        if (!supported) return;

        cleanup();
        setError(null);
        setTranscript('');
        setInterimTranscript('');

        const SpeechRecognitionCtor = window.SpeechRecognition ?? window.webkitSpeechRecognition;
        // eslint-disable-next-line @typescript-eslint/no-non-null-assertion
        const recognition = new SpeechRecognitionCtor!();
        recognition.continuous = false;
        recognition.interimResults = true;
        recognition.lang = lang;
        recognition.maxAlternatives = 1;

        recognition.onresult = (event: SpeechRecognitionEvent) => {
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

        recognition.onerror = (event: SpeechRecognitionErrorEvent) => {
            if (event.error === 'no-speech' || event.error === 'aborted') {
                setError(null);
            } else {
                setError(event.error);
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
    }, [supported, cleanup]);

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
