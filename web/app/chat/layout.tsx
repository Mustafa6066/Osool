"use client";

import { ReactNode } from "react";

export default function ChatLayout({ children }: { children: ReactNode }) {
    return (
        <div className="flex h-screen bg-[var(--color-background)] text-[var(--color-text-primary)] font-sans overflow-hidden">
            {/* Main Content Area - Full width (sidebar managed by ChatInterface) */}
            <main className="flex-1 flex flex-col relative min-w-0">
                {children}
            </main>
        </div>
    );
}
