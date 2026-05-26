'use client';

/**
 * MessageSkeleton — reserves space while the AI is composing a response.
 * Prevents layout jumps when property cards, analytics, or charts mount.
 * Shows a shimmer placeholder that approximates the shape of the likely result.
 */

type SkeletonVariant = 'text' | 'property' | 'analytics' | 'chart';

function Shimmer({ className }: { className: string }) {
    return (
        <div className={`relative overflow-hidden rounded-xl bg-gray-100 dark:bg-gray-800/60 ${className}`}>
            <div className="absolute inset-0 -translate-x-full animate-[shimmer_1.6s_infinite] bg-gradient-to-r from-transparent via-white/30 dark:via-white/5 to-transparent" />
        </div>
    );
}

function PropertySkeleton() {
    return (
        <div className="mt-5 grid grid-cols-1 md:grid-cols-[1fr_180px] gap-3">
            {/* Hero */}
            <div className="rounded-[18px] overflow-hidden border border-[var(--color-border)]/30 bg-[var(--color-surface)]/40">
                <Shimmer className="aspect-[16/9] rounded-none" />
                <div className="p-4 space-y-2.5">
                    <Shimmer className="h-4 w-3/4" />
                    <Shimmer className="h-3 w-1/2" />
                    <Shimmer className="h-1.5 w-full rounded-full" />
                    <div className="flex gap-2">
                        <Shimmer className="h-5 w-14" />
                        <Shimmer className="h-5 w-14" />
                    </div>
                </div>
            </div>
            {/* Side tiles */}
            <div className="hidden md:flex flex-col gap-2.5">
                <Shimmer className="h-20" />
                <Shimmer className="h-20" />
                <Shimmer className="h-20" />
            </div>
        </div>
    );
}

function AnalyticsSkeleton() {
    return (
        <div className="mt-5 rounded-[20px] border border-[var(--color-border)]/30 bg-[var(--color-surface)]/40 p-5 space-y-4">
            <div className="flex items-center gap-2">
                <Shimmer className="w-7 h-7" />
                <Shimmer className="h-3 w-36" />
            </div>
            <div className="grid grid-cols-3 gap-4">
                <Shimmer className="h-10" />
                <Shimmer className="h-10" />
                <Shimmer className="h-10" />
            </div>
        </div>
    );
}

function ChartSkeleton() {
    return (
        <div className="mt-5 rounded-[20px] border border-[var(--color-border)]/30 bg-[var(--color-surface)]/40 p-4">
            <Shimmer className="h-3 w-32 mb-4" />
            <Shimmer className="h-[160px] rounded-xl" />
        </div>
    );
}

export default function MessageSkeleton({ variant = 'property' }: { variant?: SkeletonVariant }) {
    if (variant === 'chart') return <ChartSkeleton />;
    if (variant === 'analytics') return <AnalyticsSkeleton />;
    if (variant === 'property') return <PropertySkeleton />;
    return null;
}
