"use client";

/**
 * Toast Notification System
 * 
 * Usage:
 * 1. Wrap app with <ToastProvider>
 * 2. Use: const { showToast } = useToast();
 *    showToast("Message", "success");
 */

import { createContext, useContext, useState, ReactNode } from "react";

type ToastType = "success" | "error" | "info" | "warning";

interface Toast {
    id: number;
    message: string;
    type: ToastType;
}

interface ToastContextType {
    showToast: (message: string, type?: ToastType) => void;
}

const ToastContext = createContext<ToastContextType | null>(null);

export function useToast() {
    const context = useContext(ToastContext);
    if (!context) throw new Error("useToast must be used within ToastProvider");
    return context;
}

const colors: Record<ToastType, string> = {
    success: "bg-green-500",
    error: "bg-red-500",
    info: "bg-blue-500",
    warning: "bg-yellow-500 text-black"
};

const icons: Record<ToastType, string> = {
    success: "✅",
    error: "❌",
    info: "💡",
    warning: "⚠️"
};

export function ToastProvider({ children }: { children: ReactNode }) {
    const [toasts, setToasts] = useState<Toast[]>([]);

    const showToast = (message: string, type: ToastType = "info") => {
        const id = Date.now();
        setToasts((prev) => [...prev, { id, message, type }]);

        // Auto-remove after 5s
        setTimeout(() => {
            setToasts((prev) => prev.filter((t) => t.id !== id));
        }, 5000);
    };

    const removeToast = (id: number) => {
        setToasts((prev) => prev.filter((t) => t.id !== id));
    };

    return (
        <ToastContext.Provider value={{ showToast }}>
            {children}

            {/* Toast Container */}
            <div className="fixed top-4 right-4 z-50 flex flex-col gap-2">
                {toasts.map((toast) => (
                    <div
                        key={toast.id}
                        className={`${colors[toast.type]} text-white px-4 py-3 rounded-lg shadow-lg flex items-center gap-3 animate-slide-in`}
                    >
                        <span>{icons[toast.type]}</span>
                        <span>{toast.message}</span>
                        <button
                            onClick={() => removeToast(toast.id)}
                            className="ml-2 opacity-70 hover:opacity-100"
                        >
                            ✕
                        </button>
                    </div>
                ))}
            </div>
        </ToastContext.Provider>
    );
}
