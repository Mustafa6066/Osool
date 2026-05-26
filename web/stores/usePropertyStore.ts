import { create } from 'zustand';

// ─── Types ───────────────────────────────────────────────
export interface PropertyMetrics {
  size?: number;
  bedrooms?: number;
  bathrooms?: number;
  pricePerSqm?: number;
  wolfScore?: number;
  roi?: number;
  marketTrend?: string;
  priceVerdict?: string;
  areaAvgPrice?: number;
}

export interface PropertyContext {
  id?: string | number;
  title: string;
  address: string;
  price: string;
  metrics: PropertyMetrics;
  tags?: string[];
  aiRecommendation?: string;
  developer?: string;
}

// ─── Store ───────────────────────────────────────────────
interface PropertyState {
  // Selected property (for detail panel)
  selectedProperty: PropertyContext | null;
  selectProperty: (property: PropertyContext | null) => void;

  // Saved / favorite properties
  savedIds: Set<string>;
  toggleSaved: (id: string) => void;
  isSaved: (id: string) => boolean;

  // Compare list
  compareIds: string[];
  addToCompare: (id: string) => void;
  removeFromCompare: (id: string) => void;
  clearCompare: () => void;

  // Recent views
  recentViews: PropertyContext[];
  addRecentView: (property: PropertyContext) => void;
}

export const usePropertyStore = create<PropertyState>((set, get) => ({
  // ─── Selected Property ───
  selectedProperty: null,
  selectProperty: (property) => set({ selectedProperty: property }),

  // ─── Saved / Favorites ───
  savedIds: new Set<string>(),
  toggleSaved: (id: string) => {
    set((s) => {
      const next = new Set(s.savedIds);
      if (next.has(id)) {
        next.delete(id);
      } else {
        next.add(id);
      }
      return { savedIds: next };
    });
  },
  isSaved: (id: string) => get().savedIds.has(id),

  // ─── Compare ───
  compareIds: [],
  addToCompare: (id) =>
    set((s) => ({
      compareIds: s.compareIds.includes(id) ? s.compareIds : [...s.compareIds, id].slice(0, 4),
    })),
  removeFromCompare: (id) =>
    set((s) => ({ compareIds: s.compareIds.filter((i) => i !== id) })),
  clearCompare: () => set({ compareIds: [] }),

  // ─── Recent Views ───
  recentViews: [],
  addRecentView: (property) =>
    set((s) => {
      const filtered = s.recentViews.filter(
        (p) => p.title !== property.title || p.address !== property.address
      );
      return { recentViews: [property, ...filtered].slice(0, 20) };
    }),
}));
