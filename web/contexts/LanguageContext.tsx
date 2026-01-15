"use client";

import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';

type Language = 'en' | 'ar';
type Direction = 'ltr' | 'rtl';

interface LanguageContextType {
    language: Language;
    direction: Direction;
    toggleLanguage: () => void;
    setLanguage: (lang: Language) => void;
    t: (key: string) => string;
}

const LanguageContext = createContext<LanguageContextType | undefined>(undefined);

// Import translations
import { translations } from '@/lib/translations';

export function LanguageProvider({ children }: { children: ReactNode }) {
    const [language, setLanguageState] = useState<Language>('en');
    const [mounted, setMounted] = useState(false);

    const direction: Direction = language === 'ar' ? 'rtl' : 'ltr';

    useEffect(() => {
        setMounted(true);
        // Check localStorage
        const savedLang = localStorage.getItem('osool-language') as Language | null;
        if (savedLang) {
            setLanguageState(savedLang);
        }
    }, []);

    useEffect(() => {
        if (!mounted) return;

        // Update document attributes
        document.documentElement.lang = language;
        document.documentElement.dir = direction;

        // Persist to localStorage
        localStorage.setItem('osool-language', language);
    }, [language, direction, mounted]);

    const toggleLanguage = () => {
        setLanguageState(prev => prev === 'en' ? 'ar' : 'en');
    };

    const setLanguage = (lang: Language) => {
        setLanguageState(lang);
    };

    // Translation function with dot notation support
    const t = (key: string): string => {
        const keys = key.split('.');
        let value: unknown = translations[language];

        for (const k of keys) {
            if (value && typeof value === 'object' && k in value) {
                value = (value as Record<string, unknown>)[k];
            } else {
                // Return key if translation not found
                return key;
            }
        }

        return typeof value === 'string' ? value : key;
    };

    // Create a translation function that works even before mount
    const preRenderT = (key: string): string => {
        const keys = key.split('.');
        let value: unknown = translations['en']; // Default to English before mount

        for (const k of keys) {
            if (value && typeof value === 'object' && k in value) {
                value = (value as Record<string, unknown>)[k];
            } else {
                return key;
            }
        }

        return typeof value === 'string' ? value : key;
    };

    // Prevent hydration mismatch - but still provide working translations
    if (!mounted) {
        return (
            <LanguageContext.Provider value={{
                language: 'en',
                direction: 'ltr',
                toggleLanguage: () => { },
                setLanguage: () => { },
                t: preRenderT
            }}>
                {children}
            </LanguageContext.Provider>
        );
    }

    return (
        <LanguageContext.Provider value={{ language, direction, toggleLanguage, setLanguage, t }}>
            {children}
        </LanguageContext.Provider>
    );
}

export function useLanguage() {
    const context = useContext(LanguageContext);
    if (context === undefined) {
        throw new Error('useLanguage must be used within a LanguageProvider');
    }
    return context;
}
