export default function ExploreLoading() {
  return (
    <div className="min-h-dvh bg-[var(--color-background)] px-4 py-8 animate-pulse">
      <div className="mx-auto max-w-4xl space-y-6">
        <div className="h-52 rounded-2xl bg-[var(--color-surface-elevated)]" />
        <div className="grid grid-cols-2 gap-4">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="h-40 rounded-2xl bg-[var(--color-surface-elevated)]" />
          ))}
        </div>
        <div className="h-36 rounded-2xl bg-[var(--color-surface-elevated)]" />
      </div>
    </div>
  );
}
