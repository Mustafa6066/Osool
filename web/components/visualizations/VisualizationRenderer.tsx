"use client";

import { Suspense, useState, useEffect } from "react";
import { createPortal } from "react-dom";
import { Maximize2, X } from "lucide-react";
import { getVisualization } from "./registry";

// Loading skeleton
function VisualizationSkeleton() {
    return (
        <div className="animate-pulse bg-[var(--color-surface)] rounded-2xl p-6 border border-[var(--color-border)]">
            <div className="h-4 bg-[var(--color-surface-hover)] rounded w-1/3 mb-4"></div>
            <div className="h-32 bg-[var(--color-surface-hover)] rounded mb-4"></div>
            <div className="h-4 bg-[var(--color-surface-hover)] rounded w-2/3"></div>
        </div>
    );
}

export interface VisualizationRendererProps {
    type: string;
    data: Record<string, unknown>;
    isRTL?: boolean;
}

/**
 * Registry-based Visualization Router
 *
 * Resolves visualization type → component via the registry.
 * Each entry handles its own validation and prop transformation.
 */
function InnerVisualizationRenderer({ type, data, isRTL = true }: VisualizationRendererProps) {
    if (!data) return null;

    const entry = getVisualization(type);
    if (!entry) return null;
    if (!entry.validate(data)) return null;

    const Component = entry.component;
    const props = entry.transformProps ? entry.transformProps(data, isRTL) : data;

    return (
        <Suspense fallback={<VisualizationSkeleton />}>
            <Component {...props} />
        </Suspense>
    );
}

export default function VisualizationRenderer(props: VisualizationRendererProps) {
    const [isMaximized, setIsMaximized] = useState(false);
    const [isClient, setIsClient] = useState(false);

    useEffect(() => {
        setIsClient(true);
    }, []);

    useEffect(() => {
        if (!isClient || !isMaximized) return;

        const previousOverflow = document.body.style.overflow;
        document.body.style.overflow = "hidden";

        return () => {
            document.body.style.overflow = previousOverflow;
        };
    }, [isClient, isMaximized]);

    useEffect(() => {
        if (!isClient || !isMaximized) return;

        const onKeyDown = (event: KeyboardEvent) => {
            if (event.key === "Escape") {
                setIsMaximized(false);
            }
        };

        window.addEventListener("keydown", onKeyDown);
        return () => {
            window.removeEventListener("keydown", onKeyDown);
        };
    }, [isClient, isMaximized]);
    
    const inlineContent = InnerVisualizationRenderer(props);
    if (!inlineContent) return null;

    const modal =
        isClient && isMaximized
            ? createPortal(
                <div className="fixed inset-0 z-[220] flex flex-col bg-black/90 backdrop-blur-sm p-2 sm:p-6" onClick={() => setIsMaximized(false)}>
                    <div className="flex justify-end p-2 md:pb-4">
                        <button
                            onClick={(event) => {
                                event.stopPropagation();
                                setIsMaximized(false);
                            }}
                            className="p-3 bg-white/10 hover:bg-white/20 rounded-full transition-colors backdrop-blur-md border border-white/20 text-white"
                            aria-label="Close"
                            data-testid="viz-fullscreen-close"
                        >
                            <X size={24} />
                        </button>
                    </div>
                    <div
                        className="flex-1 w-full max-w-full mx-auto bg-[var(--color-surface)] rounded-2xl md:rounded-3xl p-3 sm:p-4 md:p-8 overflow-y-auto no-scrollbar shadow-2xl relative flex flex-col"
                        onClick={(event) => event.stopPropagation()}
                    >
                        <div className="flex-1 min-h-[400px]">
                            {InnerVisualizationRenderer(props)}
                        </div>
                    </div>
                </div>,
                document.body
            )
            : null;

    return (
        <>
            {/* Mobile-first chart wrapper: full width on phones without forced min-width clipping */}
            <div className="relative group overflow-hidden rounded-2xl border border-[var(--color-border)]/35 bg-[var(--color-surface)]/55 backdrop-blur-sm">
                <div className="w-full relative">
                    <div className="w-full max-w-full min-w-0 p-2 sm:p-3">
                        {inlineContent}
                    </div>
                </div>
                
                {/* Maximize Button - shows on hover across devices */}
                <button 
                    onClick={() => setIsMaximized(true)} 
                    className="absolute top-2.5 right-2.5 sm:top-3 sm:right-3 sm:opacity-0 group-hover:opacity-100 transition-opacity p-1.5 sm:p-2 rounded-xl bg-white/85 dark:bg-black/60 backdrop-blur-sm border border-black/10 dark:border-white/10 shadow-sm z-10 hover:bg-white dark:hover:bg-black text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)]"
                    aria-label="Maximize chart"
                    data-testid="viz-maximize"
                >
                    <Maximize2 size={16} />
                </button>
            </div>
            {modal}
        </>
    );
}
