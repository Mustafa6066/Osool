'use client';

import React, { useEffect, useState } from 'react';
import { TrendingUp } from 'lucide-react';

interface XPToastProps {
    amount: number;
    action?: string;
    onDone?: () => void;
}

/**
 * XP Toast V5 — B/W Glass + Emerald accent
 * Appears briefly when user earns XP, then auto-dismisses.
 */
export default function XPToast({ amount, action, onDone }: XPToastProps) {
    const [visible, setVisible] = useState(true);

    useEffect(() => {
        const timer = setTimeout(() => {
            setVisible(false);
            onDone?.();
        }, 2500);
        return () => clearTimeout(timer);
    }, [onDone]);

    if (!visible || amount <= 0) return null;

    return (
        <div
            className={`fixed bottom-24 end-6 z-50 flex items-center gap-2.5 px-4 py-2.5
                        bg-[var(--color-surface)] border border-[var(--color-border)]
                        text-[var(--color-text-primary)] rounded-full
                        shadow-xl shadow-black/10 backdrop-blur-xl
                        animate-xp-toast pointer-events-none`}
        >
            <div className="w-6 h-6 rounded-full bg-emerald-500/15 flex items-center justify-center">
                <TrendingUp className="w-3.5 h-3.5 text-emerald-500" />
            </div>
            <span className="font-bold text-sm text-emerald-500">+{amount} XP</span>
            {action && (
                <span className="text-xs text-[var(--color-text-muted)] hidden sm:inline">
                    {action}
                </span>
            )}
        </div>
    );
}
