export default function DevelopersLoading() {
  return (
    <div className="min-h-dvh bg-[var(--color-background)] px-4 py-8 animate-pulse">
      <div className="mx-auto max-w-4xl space-y-4">
        <div className="h-40 rounded-2xl bg-[var(--color-surface-elevated)]" />
        <div className="h-20 rounded-2xl bg-[var(--color-surface-elevated)]" />
        {[...Array(6)].map((_, i) => (
          <div key={i} className="h-32 rounded-2xl bg-[var(--color-surface-elevated)]" />
        ))}
      </div>
    </div>
  );
}
