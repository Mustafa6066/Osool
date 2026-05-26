'use client';

import React from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import {
  Activity,
  AlertTriangle,
  Brain,
  CheckCircle2,
  Cpu,
  Database,
  MessageSquare,
  Radar,
  Route,
  Zap,
} from 'lucide-react';
import type { NeuralPhase, NeuralSignalSnapshot, NeuralSignalStep } from '@/components/chat/neural-signals';

interface OrchestratorSignalPanelProps {
  snapshot: NeuralSignalSnapshot;
  language: string;
  visible: boolean;
}

const PHASE_META: Record<NeuralPhase, { icon: React.ComponentType<{ className?: string }>; en: string; ar: string }> = {
  idle: { icon: Activity, en: 'Standby', ar: 'جاهز' },
  routing: { icon: Route, en: 'Routing', ar: 'توجيه' },
  searching: { icon: Database, en: 'Searching', ar: 'بحث' },
  analyzing: { icon: Brain, en: 'Analyzing', ar: 'تحليل' },
  responding: { icon: MessageSquare, en: 'Responding', ar: 'رد' },
  complete: { icon: CheckCircle2, en: 'Complete', ar: 'اكتمل' },
  error: { icon: AlertTriangle, en: 'Interrupted', ar: 'تعذر' },
};

function phaseText(phase: NeuralPhase, language: string) {
  const meta = PHASE_META[phase];
  return language === 'ar' ? meta.ar : meta.en;
}

function stepIcon(step: NeuralSignalStep) {
  if (step.status === 'complete') return CheckCircle2;
  if (step.status === 'error') return AlertTriangle;
  return PHASE_META[step.phase].icon;
}

export default function OrchestratorSignalPanel({ snapshot, language, visible }: OrchestratorSignalPanelProps) {
  const isAr = language === 'ar';
  const PhaseIcon = PHASE_META[snapshot.phase].icon;
  const signalLevel = Math.round(snapshot.intensity * 100);
  const visibleSteps = snapshot.steps.slice(-4);
  const activeCopy = snapshot.lastStatus || phaseText(snapshot.phase, language);

  return (
    <AnimatePresence>
      {visible && (
        <motion.section
          initial={{ opacity: 0, y: 12, scale: 0.98 }}
          animate={{ opacity: 1, y: 0, scale: 1 }}
          exit={{ opacity: 0, y: 8, scale: 0.98 }}
          transition={{ duration: 0.28, ease: [0.16, 1, 0.3, 1] }}
          className="neural-panel mb-5 overflow-hidden rounded-lg border border-[var(--neural-border)] bg-[var(--neural-panel-bg)] shadow-[var(--neural-shadow)] backdrop-blur-xl"
          dir={isAr ? 'rtl' : 'ltr'}
          aria-live="polite"
        >
          <div className="relative p-3 sm:p-4">
            <div className="pointer-events-none absolute inset-0 neural-panel-sheen" />

            <div className="relative flex items-start gap-3">
              <div className="relative flex h-10 w-10 shrink-0 items-center justify-center rounded-lg border border-[var(--neural-node-border)] bg-[var(--neural-node-bg)] text-[var(--neural-primary)]">
                <span className="absolute inset-1 rounded-md border border-[var(--neural-primary-soft)] animate-neural-node" />
                <PhaseIcon className="relative h-4.5 w-4.5" />
              </div>

              <div className="min-w-0 flex-1">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="text-[11px] font-semibold uppercase tracking-[0.16em] text-[var(--neural-primary)]">
                    {isAr ? 'إشارة أصول' : 'Osool Signal'}
                  </span>
                  <span className="h-1 w-1 rounded-full bg-[var(--color-text-muted)]/50" />
                  <span className="truncate text-[11px] font-medium text-[var(--color-text-secondary)]">
                    {snapshot.routeLabel}
                  </span>
                </div>
                <div className="mt-1 flex min-w-0 flex-wrap items-center gap-2">
                  <p className="truncate text-[13px] font-semibold text-[var(--color-text-primary)]" dir="auto">
                    {activeCopy}
                  </p>
                  {snapshot.isLocalPath && (
                    <span className="rounded-md border border-[var(--neural-primary-soft)] bg-[var(--neural-primary-faint)] px-1.5 py-0.5 text-[10px] font-semibold text-[var(--neural-primary)]">
                      {isAr ? 'محلي' : 'Local'}
                    </span>
                  )}
                </div>
              </div>

              <div className="hidden shrink-0 items-center gap-1.5 rounded-lg border border-[var(--neural-border)] bg-[var(--neural-metric-bg)] px-2.5 py-1.5 sm:flex">
                <Zap className="h-3.5 w-3.5 text-[var(--neural-primary)]" />
                <span className="text-[11px] font-semibold text-[var(--color-text-primary)] tabular-nums">{signalLevel}%</span>
              </div>
            </div>

            <div className="relative mt-3 h-12 overflow-hidden rounded-lg border border-[var(--neural-border)] bg-[var(--neural-graph-bg)]">
              <div className="absolute inset-0 neural-graph-grid" />
              <motion.div
                className="absolute inset-y-0 w-1/3 bg-gradient-to-r from-transparent via-[var(--neural-primary-soft)] to-transparent"
                animate={{ x: ['-120%', '320%'] }}
                transition={{ duration: snapshot.phase === 'responding' ? 1.7 : 2.4, repeat: Infinity, ease: 'linear' }}
              />
              <div className="relative flex h-full items-end gap-1.5 px-3 pb-2">
                {[0.28, 0.52, 0.38, 0.76, 0.44, 0.68, 0.34, 0.58].map((bar, index) => (
                  <motion.span
                    key={index}
                    className="w-full rounded-t-sm bg-[var(--neural-primary)]/45"
                    style={{ height: `${Math.max(14, bar * signalLevel)}%` }}
                    animate={{ opacity: [0.35, 0.85, 0.35], scaleY: [0.85, 1, 0.85] }}
                    transition={{ duration: 1.2 + index * 0.06, repeat: Infinity, ease: 'easeInOut', delay: index * 0.05 }}
                  />
                ))}
              </div>
            </div>

            {visibleSteps.length > 0 && (
              <div className="relative mt-3 grid gap-1.5">
                {visibleSteps.map((step) => {
                  const StepIcon = stepIcon(step);
                  const isActive = step.status === 'active';
                  const isError = step.status === 'error';

                  return (
                    <div
                      key={step.id}
                      className={`flex min-w-0 items-center gap-2 rounded-lg px-2 py-1.5 text-[12px] ${
                        isActive ? 'bg-[var(--neural-active-bg)] text-[var(--color-text-primary)]' : 'text-[var(--color-text-muted)]'
                      }`}
                    >
                      <span className={`flex h-5 w-5 shrink-0 items-center justify-center rounded-md ${isError ? 'text-red-500' : isActive ? 'text-[var(--neural-primary)]' : 'text-emerald-500/80'}`}>
                        {isActive && snapshot.phase !== 'complete' ? (
                          <span className="h-3.5 w-3.5 rounded-full border-2 border-[var(--neural-primary-soft)] border-t-[var(--neural-primary)] animate-spin" />
                        ) : (
                          <StepIcon className="h-3.5 w-3.5" />
                        )}
                      </span>
                      <span className="truncate" dir="auto">{step.label}</span>
                      {isActive && (
                        <Radar className="ms-auto h-3.5 w-3.5 shrink-0 text-[var(--neural-primary)]" />
                      )}
                    </div>
                  );
                })}
              </div>
            )}

            <div className="relative mt-3 flex items-center gap-2 text-[10px] font-medium uppercase tracking-[0.16em] text-[var(--color-text-muted)]">
              <Cpu className="h-3 w-3" />
              <span>{phaseText(snapshot.phase, language)}</span>
            </div>
          </div>
        </motion.section>
      )}
    </AnimatePresence>
  );
}
