'use client';

import React, { useEffect, useState } from 'react';
import { TrendingUp } from 'lucide-react';

interface XPToastProps {
    amount: number;
    action?: string;
    onDone?: () => void;
}

/**
 * XP Toast - Subtle "+15 XP" notification
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
            className={`fixed bottom-24 right-6 z-50 flex items-center gap-2 px-4 py-2.5
                        bg-gradient-to-r from-teal-600 to-emerald-600 text-white rounded-full
                        shadow-xl shadow-teal-900/30 animate-xp-toast pointer-events-none`}
        >
            <TrendingUp className="w-4 h-4" />
            <span className="font-bold text-sm">+{amount} XP</span>
            {action && (
                <span className="text-xs text-teal-200 hidden sm:inline">
                    {action}
                </span>
            )}
        </div>
    );
}
