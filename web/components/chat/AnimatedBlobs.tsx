'use client';

export default function AnimatedBlobs() {
    return (
        <div className="absolute inset-0 overflow-hidden pointer-events-none z-0">
            {/* Teal blob - top left */}
            <div
                className="absolute -top-[10%] -left-[10%] w-[500px] h-[500px] rounded-full blur-[100px] animate-blob-1"
                style={{ background: 'radial-gradient(circle, var(--blob-teal) 0%, transparent 70%)' }}
            />

            {/* Violet blob - bottom right */}
            <div
                className="absolute -bottom-[10%] -right-[10%] w-[600px] h-[600px] rounded-full blur-[120px] animate-blob-2"
                style={{ background: 'radial-gradient(circle, var(--blob-violet) 0%, transparent 70%)' }}
            />

            {/* Primary blob - center */}
            <div
                className="absolute top-[40%] left-[40%] w-[400px] h-[400px] rounded-full blur-[80px] animate-blob-3"
                style={{ background: 'radial-gradient(circle, var(--blob-primary) 0%, transparent 70%)' }}
            />
        </div>
    );
}
