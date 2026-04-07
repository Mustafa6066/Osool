import { create } from 'zustand';

// ─── Feature Flags ───────────────────────────────────────
export interface FeatureFlags {
  enableSSEStreaming: boolean;
  enableVirtualScroll: boolean;
  enableVoiceInput: boolean;
  enableGamification: boolean;
  enableLeadScoring: boolean;
  enableCommandPalette: boolean;
}

const DEFAULT_FLAGS: FeatureFlags = {
  enableSSEStreaming: true,
  enableVirtualScroll: true,
  enableVoiceInput: true,
  enableGamification: true,
  enableLeadScoring: true,
  enableCommandPalette: true,
};

// ─── App Store ───────────────────────────────────────────
interface AppState {
  // Feature flags
  flags: FeatureFlags;
  setFlag: (key: keyof FeatureFlags, value: boolean) => void;

  // UI State
  sidebarOpen: boolean;
  setSidebarOpen: (open: boolean) => void;
  toggleSidebar: () => void;

  // Active panels
  activePanel: 'chat' | 'properties' | 'insights' | 'settings' | null;
  setActivePanel: (panel: AppState['activePanel']) => void;

  // Cost tracking (inspired by src/cost-tracker.ts)
  sessionCost: {
    totalUSD: number;
    inputTokens: number;
    outputTokens: number;
    requestCount: number;
  };
  addCost: (cost: { usd: number; input: number; output: number }) => void;
  resetCost: () => void;

  // Performance metrics
  lastResponseMs: number | null;
  setLastResponseMs: (ms: number) => void;
}

export const useAppStore = create<AppState>((set) => ({
  // ─── Feature Flags ───
  flags: DEFAULT_FLAGS,
  setFlag: (key, value) =>
    set((s) => ({ flags: { ...s.flags, [key]: value } })),

  // ─── UI State ───
  sidebarOpen: false,
  setSidebarOpen: (open) => set({ sidebarOpen: open }),
  toggleSidebar: () => set((s) => ({ sidebarOpen: !s.sidebarOpen })),

  // ─── Active Panel ───
  activePanel: 'chat',
  setActivePanel: (panel) => set({ activePanel: panel }),

  // ─── Cost Tracking ───
  sessionCost: { totalUSD: 0, inputTokens: 0, outputTokens: 0, requestCount: 0 },
  addCost: (cost) =>
    set((s) => ({
      sessionCost: {
        totalUSD: s.sessionCost.totalUSD + cost.usd,
        inputTokens: s.sessionCost.inputTokens + cost.input,
        outputTokens: s.sessionCost.outputTokens + cost.output,
        requestCount: s.sessionCost.requestCount + 1,
      },
    })),
  resetCost: () =>
    set({ sessionCost: { totalUSD: 0, inputTokens: 0, outputTokens: 0, requestCount: 0 } }),

  // ─── Performance ───
  lastResponseMs: null,
  setLastResponseMs: (ms) => set({ lastResponseMs: ms }),
}));
