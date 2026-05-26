export default function DashboardLoading() {
  return (
    <div className="min-h-dvh bg-[var(--color-background)] px-4 py-8 animate-pulse">
      <div className="mx-auto max-w-5xl space-y-5">
        {/* Header skeleton */}
        <div className="space-y-2">
          <div className="h-4 w-24 rounded-full bg-[var(--color-surface-elevated)]" />
          <div className="h-8 w-56 rounded-xl bg-[var(--color-surface-elevated)]" />
          <div className="h-4 w-72 rounded-full bg-[var(--color-surface-elevated)]" />
        </div>
        {/* Card skeleton */}
        <div className="h-36 rounded-2xl bg-[var(--color-surface-elevated)]" />
        {/* 2-col grid */}
        <div className="grid grid-cols-2 gap-4">
          <div className="h-32 rounded-2xl bg-[var(--color-surface-elevated)]" />
          <div className="h-32 rounded-2xl bg-[var(--color-surface-elevated)]" />
          <div className="h-32 rounded-2xl bg-[var(--color-surface-elevated)]" />
          <div className="h-32 rounded-2xl bg-[var(--color-surface-elevated)]" />
        </div>
        {/* Wide card */}
        <div className="h-48 rounded-2xl bg-[var(--color-surface-elevated)]" />
      </div>
    </div>
  );
}
