export default function MarketLoading() {
  return (
    <div className="min-h-dvh bg-[var(--color-background)] px-4 py-8 animate-pulse">
      <div className="mx-auto max-w-5xl space-y-4">
        <div className="h-32 rounded-2xl bg-[var(--color-surface-elevated)]" />
        <div className="grid grid-cols-3 gap-4">
          {[...Array(3)].map((_, i) => (
            <div key={i} className="h-24 rounded-2xl bg-[var(--color-surface-elevated)]" />
          ))}
        </div>
        <div className="h-64 rounded-2xl bg-[var(--color-surface-elevated)]" />
        <div className="h-48 rounded-2xl bg-[var(--color-surface-elevated)]" />
      </div>
    </div>
  );
}
