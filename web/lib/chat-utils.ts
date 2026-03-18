/* ═══════════════════════════════════════════════════════════════
   Shared Chat Utilities
   Types, helpers, and storage used across all chat components.
   ═══════════════════════════════════════════════════════════════ */
import type { ElementType } from 'react';

/* ─── Core Types ─────────────────────────────── */

export interface PropertyMetrics {
  size: number;
  bedrooms: number;
  bathrooms: number;
  wolf_score: number;
  roi: number;
  price_per_sqm: number;
  liquidity_rating: string;
}

export interface Property {
  id: string;
  title: string;
  location: string;
  price: number;
  currency: string;
  metrics: PropertyMetrics;
  image: string;
  developer: string;
  tags: string[];
  status: string;
}

export interface ChatPropertyPayload {
  id?: string | number;
  title?: string;
  name?: string;
  location?: string;
  address?: string;
  price?: number;
  size_sqm?: number;
  size?: number;
  bedrooms?: number;
  bathrooms?: number;
  wolf_score?: number;
  projected_roi?: number;
  roi?: number;
  price_per_sqm?: number;
  liquidity_rating?: string;
  image_url?: string;
  image?: string;
  developer?: string;
  tags?: string[];
  status?: string;
}

export interface UiActionArea {
  name?: string;
  avg_price_sqm?: number;
  avg_price_per_sqm?: number;
}

export interface UiActionData {
  area?: UiActionArea;
  areas?: UiActionArea[];
  projections?: unknown[];
  data_points?: unknown[];
  summary?: { cash_final?: number };
  final_values?: { cash_real_value?: number };
  area_context?: { avg_price_sqm?: number };
  avg_price_sqm?: number;
  [key: string]: unknown;
}

export interface UiAction {
  type: string;
  data?: UiActionData;
  [key: string]: unknown;
}

export interface AnalyticsContext {
  has_analytics?: boolean;
  avg_price_sqm?: number;
  growth_rate?: number;
  rental_yield?: number;
  [key: string]: unknown;
}

export interface Artifacts {
  property?: Property;
  chart?: { type: string; data: unknown };
}

export interface Message {
  id: number;
  role: 'user' | 'agent';
  content: string;
  artifacts?: Artifacts | null;
  uiActions?: UiAction[];
  analyticsContext?: AnalyticsContext | null;
  showingStrategy?: string;
  allProperties?: Property[];
  leadScore?: number;
  readinessScore?: number;
  suggestions?: string[];
  detectedLanguage?: string;
}

export interface PastSession {
  session_id: string;
  preview: string | null;
  message_count: number;
  last_message_at: string | null;
}

/* ─── RTL Detection ──────────────────────────── */

export function isArabic(text: string): boolean {
  if (!text) return false;
  const arabicChars = text.match(/[\u0600-\u06FF]/g);
  return !!arabicChars && arabicChars.length > text.length * 0.3;
}

/* ─── Markdown Table Repair ──────────────────── */

export function fixMarkdownTables(text: string): string {
  const lines = text.split('\n');
  const result: string[] = [];
  let i = 0;

  while (i < lines.length) {
    const line = lines[i];
    if (/^\s*\|/.test(line)) {
      const tableLines: string[] = [];
      while (i < lines.length && /^\s*\|/.test(lines[i])) {
        tableLines.push(lines[i]);
        i++;
      }

      if (tableLines.length >= 2) {
        const headerCols = (tableLines[0].match(/\|/g) || []).length - 1;
        const isSeparator = (l: string) => /^\s*\|[\s\-:|]+\|\s*$/.test(l);

        if (isSeparator(tableLines[1])) {
          const sepCols = (tableLines[1].match(/\|/g) || []).length - 1;
          if (sepCols !== headerCols) {
            tableLines[1] = '| ' + Array(headerCols).fill('---').join(' | ') + ' |';
          }
        } else if (headerCols >= 2) {
          tableLines.splice(1, 0, '| ' + Array(headerCols).fill('---').join(' | ') + ' |');
        }

        for (let r = 2; r < tableLines.length; r++) {
          if (isSeparator(tableLines[r])) continue;
          const rowCols = (tableLines[r].match(/\|/g) || []).length - 1;
          if (rowCols < headerCols) {
            tableLines[r] = tableLines[r].trimEnd().replace(/\|$/, '') + '| '.repeat(headerCols - rowCols) + '|';
          }
        }
        result.push(...tableLines);
      } else {
        result.push(...tableLines);
      }
    } else {
      result.push(line);
      i++;
    }
  }
  return result.join('\n');
}

/* ─── Content Sanitizers ─────────────────────── */

export function sanitizeAgentContent(text: string): string {
  if (!text) return text;
  return text
    .replace(/^\s*\[[^\n\]]+\]\s*$/gm, '')
    .replace(/\n{3,}/g, '\n\n')
    .trim();
}

export function normalizeMarkdown(content: string): string {
  return fixMarkdownTables(
    content
      .replace(/\r\n/g, '\n')
      .replace(/\n{3,}/g, '\n\n')
      .replace(/(?<!\n)\n(?!\n)/gm, (match, offset, str) => {
        const before = str.lastIndexOf('\n', offset - 1);
        const after = str.indexOf('\n', offset + 1);
        const prevLine = str.slice(before + 1, offset);
        const nextLine = str.slice(offset + 1, after === -1 ? undefined : after);
        if (/^\s*\|/.test(prevLine) || /^\s*\|/.test(nextLine)) return match;
        return '\n\n';
      })
  );
}

/* ─── Property Mapper ────────────────────────── */

export function mapChatPropertyToProperty(prop: ChatPropertyPayload): Property {
  return {
    id: prop.id?.toString() || `prop_${Date.now()}_${Math.random()}`,
    title: prop.title || prop.name || 'Property',
    location: prop.location || prop.address || 'Location',
    price: prop.price || 0,
    currency: 'EGP',
    metrics: {
      size: prop.size_sqm || prop.size || 0,
      bedrooms: prop.bedrooms || 0,
      bathrooms: prop.bathrooms || 0,
      wolf_score: prop.wolf_score || 0,
      roi: prop.projected_roi || prop.roi || 0,
      price_per_sqm: prop.price_per_sqm || 0,
      liquidity_rating: prop.liquidity_rating || 'Medium',
    },
    image: prop.image_url || prop.image || 'https://images.unsplash.com/photo-1613977257363-707ba9348227?auto=format&fit=crop&q=80&w=800',
    developer: prop.developer || 'Developer',
    tags: Array.isArray(prop.tags) ? prop.tags.filter((tag): tag is string => typeof tag === 'string') : [],
    status: prop.status || 'Available',
  };
}

/* ─── UI Action Filter ───────────────────────── */

export function shouldRenderUiAction(action: UiAction): boolean {
  if (action.type === 'property_cards') return false;
  if (!action.data) return false;

  const data = action.data;
  if (action.type === 'area_analysis') {
    const area = data.area || data.areas?.[0];
    if (!area?.name || (area.avg_price_sqm || area.avg_price_per_sqm || 0) === 0) return false;
  }
  if (action.type === 'inflation_killer') {
    const hasProjections = (data.projections?.length || 0) > 0 || (data.data_points?.length || 0) > 0;
    const hasSummary = (data.summary?.cash_final || 0) > 0 || (data.final_values?.cash_real_value || 0) > 0;
    if (!hasProjections && !hasSummary) return false;
  }
  if (action.type === 'market_benchmark' && !data.avg_price_sqm && !data.area_context?.avg_price_sqm) return false;
  if (action.type === 'price_growth_chart' && (!data.data_points?.length || data.data_points.length < 2)) return false;
  return true;
}

/* ─── Session Storage ────────────────────────── */

export const STORAGE_KEYS = {
  MESSAGES: 'osool_chat_messages',
  SESSION_ID: 'osool_chat_session_id',
  SESSIONS_LIST: 'osool_chat_sessions',
} as const;

export function loadFromStorage<T>(key: string, fallback: T): T {
  if (typeof window === 'undefined') return fallback;
  try {
    const raw = sessionStorage.getItem(key);
    return raw ? JSON.parse(raw) : fallback;
  } catch { return fallback; }
}

export function saveToStorage(key: string, value: unknown) {
  if (typeof window === 'undefined') return;
  try { sessionStorage.setItem(key, JSON.stringify(value)); } catch { /* quota exceeded */ }
}

export function getOrCreateSessionId(): string {
  if (typeof window === 'undefined') return `session_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`;
  const existing = sessionStorage.getItem(STORAGE_KEYS.SESSION_ID);
  if (existing) return existing;
  const id = `session_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`;
  sessionStorage.setItem(STORAGE_KEYS.SESSION_ID, id);
  return id;
}

/* ─── Misc Helpers ───────────────────────────── */

export function getTimeAgo(dateStr: string, lang: string): string {
  const diff = Date.now() - new Date(dateStr).getTime();
  const mins = Math.floor(diff / 60000);
  if (mins < 1) return lang === 'ar' ? 'الآن' : 'just now';
  if (mins < 60) return lang === 'ar' ? `منذ ${mins} د` : `${mins}m ago`;
  const hrs = Math.floor(mins / 60);
  if (hrs < 24) return lang === 'ar' ? `منذ ${hrs} س` : `${hrs}h ago`;
  const days = Math.floor(hrs / 24);
  if (days < 7) return lang === 'ar' ? `منذ ${days} ي` : `${days}d ago`;
  return lang === 'ar' ? `منذ ${Math.floor(days / 7)} أسبوع` : `${Math.floor(days / 7)}w ago`;
}

export function guessConversationTag(preview: string | null): { label: string; color: string } | null {
  if (!preview) return null;
  const lower = preview.toLowerCase();
  if (lower.includes('market') || lower.includes('trend') || lower.includes('سوق') || lower.includes('اتجاه'))
    return { label: 'Market', color: 'bg-blue-500/15 text-blue-400' };
  if (lower.includes('invest') || lower.includes('roi') || lower.includes('استثمار') || lower.includes('عائد'))
    return { label: 'Investment', color: 'bg-emerald-500/15 text-emerald-400' };
  if (lower.includes('developer') || lower.includes('delivery') || lower.includes('audit') || lower.includes('مطور') || lower.includes('تسليم'))
    return { label: 'Developer', color: 'bg-purple-500/15 text-purple-400' };
  if (lower.includes('compare') || lower.includes('price') || lower.includes('قارن') || lower.includes('سعر'))
    return { label: 'Pricing', color: 'bg-amber-500/15 text-amber-400' };
  return null;
}

export function getErrorMessage(error: unknown, fallback: string): string {
  if (error instanceof Error && error.message) return error.message;
  return fallback;
}
