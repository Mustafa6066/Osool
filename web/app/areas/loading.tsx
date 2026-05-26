export default function AreasLoading() {
  return (
    <div className="min-h-dvh bg-[var(--color-background)] px-4 sm:px-6 lg:px-8 py-8 animate-pulse">
      <div className="mx-auto max-w-7xl space-y-6">
        {/* Hero skeleton */}
        <div className="h-44 rounded-[32px] bg-[var(--color-surface-elevated)]" />

        {/* Cards grid */}
        <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-3">
          {[...Array(6)].map((_, i) => (
            <div
              key={i}
              className="rounded-[28px] bg-[var(--color-surface-elevated)] p-5 space-y-4"
            >
              {/* Name + badges */}
              <div className="flex items-center justify-between">
                <div className="space-y-1">
                  <div className="h-6 w-32 rounded bg-[var(--color-background)]" />
                  <div className="h-4 w-20 rounded bg-[var(--color-background)]" />
                </div>
                <div className="h-6 w-16 rounded-full bg-[var(--color-background)]" />
              </div>
              {/* Description box */}
              <div className="rounded-xl bg-[var(--color-background)] p-3 space-y-2">
                <div className="h-4 w-full rounded bg-[var(--color-surface-elevated)]" />
                <div className="h-4 w-4/5 rounded bg-[var(--color-surface-elevated)]" />
              </div>
              {/* 3-column metrics */}
              <div className="grid grid-cols-3 gap-3">
                <div className="rounded-xl bg-[var(--color-background)] p-3 space-y-1">
                  <div className="h-3 w-12 rounded bg-[var(--color-surface-elevated)]" />
                  <div className="h-5 w-16 rounded bg-[var(--color-surface-elevated)]" />
                </div>
                <div className="rounded-xl bg-[var(--color-background)] p-3 space-y-1">
                  <div className="h-3 w-12 rounded bg-[var(--color-surface-elevated)]" />
                  <div className="h-5 w-16 rounded bg-[var(--color-surface-elevated)]" />
                </div>
                <div className="rounded-xl bg-[var(--color-background)] p-3 space-y-1">
                  <div className="h-3 w-12 rounded bg-[var(--color-surface-elevated)]" />
                  <div className="h-5 w-16 rounded bg-[var(--color-surface-elevated)]" />
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
