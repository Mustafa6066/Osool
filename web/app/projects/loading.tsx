export default function ProjectsLoading() {
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
              {/* Badges */}
              <div className="flex gap-2">
                <div className="h-6 w-16 rounded-full bg-[var(--color-background)]" />
                <div className="h-6 w-20 rounded-full bg-[var(--color-background)]" />
              </div>
              {/* Title */}
              <div className="h-6 w-3/4 rounded bg-[var(--color-background)]" />
              {/* Description box */}
              <div className="rounded-xl bg-[var(--color-background)] p-3 space-y-2">
                <div className="h-4 w-full rounded bg-[var(--color-surface-elevated)]" />
                <div className="h-4 w-5/6 rounded bg-[var(--color-surface-elevated)]" />
              </div>
              {/* Metrics row */}
              <div className="grid grid-cols-2 gap-3">
                <div className="h-12 rounded-xl bg-[var(--color-background)]" />
                <div className="h-12 rounded-xl bg-[var(--color-background)]" />
                <div className="h-12 rounded-xl bg-[var(--color-background)]" />
                <div className="h-12 rounded-xl bg-[var(--color-background)]" />
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
