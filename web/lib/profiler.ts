/**
 * Startup Profiler — Lightweight checkpoint-based timing utility.
 *
 * Usage:
 *   import { profiler } from '@/lib/profiler';
 *   profiler.mark('store-init');
 *   // ... do work ...
 *   profiler.mark('sse-connected');
 *   profiler.summary(); // logs all checkpoints with deltas
 *
 * Inspired by src/cost-tracker.ts pattern of instrumenting critical paths.
 */

interface Checkpoint {
  label: string;
  timestamp: number;
  delta: number; // ms since previous checkpoint
}

class StartupProfiler {
  private checkpoints: Checkpoint[] = [];
  private origin: number;
  private enabled: boolean;

  constructor() {
    this.origin = typeof performance !== 'undefined' ? performance.now() : Date.now();
    this.enabled = process.env.NODE_ENV === 'development';
  }

  /** Record a named checkpoint */
  mark(label: string) {
    if (!this.enabled) return;
    const now = typeof performance !== 'undefined' ? performance.now() : Date.now();
    const prev = this.checkpoints.length > 0
      ? this.checkpoints[this.checkpoints.length - 1].timestamp
      : this.origin;
    this.checkpoints.push({ label, timestamp: now, delta: now - prev });
  }

  /** Log all checkpoints to console in a formatted table */
  summary() {
    if (!this.enabled || this.checkpoints.length === 0) return;
    const total = this.checkpoints[this.checkpoints.length - 1].timestamp - this.origin;
    console.groupCollapsed(`[Profiler] Startup: ${total.toFixed(1)}ms (${this.checkpoints.length} checkpoints)`);
    console.table(
      this.checkpoints.map((cp) => ({
        Checkpoint: cp.label,
        'Delta (ms)': cp.delta.toFixed(1),
        'Total (ms)': (cp.timestamp - this.origin).toFixed(1),
      })),
    );
    console.groupEnd();
  }

  /** Reset all checkpoints */
  reset() {
    this.checkpoints = [];
    this.origin = typeof performance !== 'undefined' ? performance.now() : Date.now();
  }

  /** Get raw checkpoint data */
  getCheckpoints(): readonly Checkpoint[] {
    return this.checkpoints;
  }

  /** Get total elapsed ms */
  elapsed(): number {
    if (this.checkpoints.length === 0) return 0;
    return this.checkpoints[this.checkpoints.length - 1].timestamp - this.origin;
  }
}

export const profiler = new StartupProfiler();
