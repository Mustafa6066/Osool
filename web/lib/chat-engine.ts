'use client';

import { useState, useRef, useCallback, useEffect } from 'react';
import { useStreamingChat } from '@/hooks/useStreamingChat';
import { useVoiceRecording, type RecordingStatus } from '@/hooks/useVoiceRecording';
import { type Property } from '@/stores/useChatStore';
import { PropertyContext, UIActionData } from '@/components/chat/ContextualPane';

// ─── Utilities (pure functions, no React) ────────────────

type UIAction = UIActionData;

export function isArabic(text: string): boolean {
  return /[\u0600-\u06FF\u0750-\u077F]/.test(text);
}

export function formatPrice(price: number): string {
  if (price >= 1_000_000) return `${(price / 1_000_000).toFixed(1)}M EGP`;
  return `${(price / 1_000).toFixed(0)}K EGP`;
}

export function getGreeting(isRTL: boolean): string {
  const hour = new Date().getHours();
  if (isRTL) {
    if (hour < 12) return 'صباح الخير! ☀️';
    if (hour < 18) return 'مساء الخير! 🌤️';
    return 'مساء النور! 🌙';
  }
  if (hour < 12) return 'Good morning! ☀️';
  if (hour < 18) return 'Good afternoon! 🌤️';
  return 'Good evening! 🌙';
}

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
        const isSep = (l: string) => /^\s*\|[\s\-:|]+\|\s*$/.test(l);
        if (isSep(tableLines[1])) {
          const sepCols = (tableLines[1].match(/\|/g) || []).length - 1;
          if (sepCols !== headerCols) {
            tableLines[1] = '| ' + Array(headerCols).fill('---').join(' | ') + ' |';
          }
        } else if (headerCols >= 2) {
          tableLines.splice(1, 0, '| ' + Array(headerCols).fill('---').join(' | ') + ' |');
        }
        for (let r = 2; r < tableLines.length; r++) {
          if (isSep(tableLines[r])) continue;
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

export function cleanMessageContent(text: string): string {
  return fixMarkdownTables(
    text
      .replace(/\[[\u0600-\u06FF\u0621-\u064A\w\s،,.:()\/-]+\]/g, '')
      .replace(/\[\s*[a-zA-Z\s_]+\s*\]/g, '')
      .replace(/\n{3,}/g, '\n\n')
      .trim(),
  );
}

export const SUGGESTION_CARDS = [
  {
    titleEn: 'Market Analysis',
    titleAr: 'تحليل السوق',
    descEn: 'Get insights on current market trends',
    descAr: 'احصل على رؤى حول اتجاهات السوق',
    query: 'Show me the current market analysis for New Cairo',
  },
  {
    titleEn: 'ROI Calculator',
    titleAr: 'حاسبة العائد',
    descEn: 'Calculate potential returns',
    descAr: 'احسب العوائد المحتملة',
    query: 'Calculate ROI for a 2M EGP investment',
  },
  {
    titleEn: 'Top Properties',
    titleAr: 'أفضل العقارات',
    descEn: 'Discover high-performing listings',
    descAr: 'اكتشف أفضل العقارات',
    query: 'Show me top investment properties',
  },
  {
    titleEn: 'Area Comparison',
    titleAr: 'مقارنة المناطق',
    descEn: 'Compare different locations',
    descAr: 'قارن بين المناطق المختلفة',
    query: 'Compare New Cairo vs Sheikh Zayed',
  },
] as const;

// ─── Property selection mapper ───────────────────────────

export function mapPropertyToContext(
  property: Property,
  uiActions: UIAction[] | undefined,
  isRTL: boolean,
): PropertyContext {
  let wolfScore = property.wolf_score || 75;
  let roi = 12.5;
  let marketTrend = 'Growing 📊';
  let priceVerdict = 'Fair';

  if (uiActions) {
    const scorecard = uiActions.find((a) => a.type === 'investment_scorecard');
    if (scorecard?.data?.analysis) {
      const analysis = scorecard.data.analysis as Record<string, unknown>;
      wolfScore = (analysis.match_score as number) || wolfScore;
      roi = (analysis.roi_projection as number) || roi;
      marketTrend = (analysis.market_trend as string) || marketTrend;
      priceVerdict = (analysis.price_verdict as string) || priceVerdict;
    }
  }

  return {
    title: property.title,
    address: property.location,
    price: formatPrice(property.price),
    metrics: {
      size: property.size_sqm,
      bedrooms: property.bedrooms,
      pricePerSqFt: `${Math.round(property.price / property.size_sqm).toLocaleString()}`,
      wolfScore,
      roi,
      marketTrend,
      priceVerdict,
    },
    tags: property.developer ? [property.developer] : [],
    aiRecommendation:
      property.wolf_score && property.wolf_score >= 80
        ? 'High investment potential based on Osool Score analysis'
        : undefined,
  };
}

// ─── ChatEngine hook ─────────────────────────────────────

export interface ChatEngineOptions {
  isRTL?: boolean;
  onPropertySelect?: (property: PropertyContext, uiActions?: UIAction[]) => void;
}

export function useChatEngine({ isRTL = false, onPropertySelect }: ChatEngineOptions) {
  // ─── Streaming chat (Zustand store) ───
  const streaming = useStreamingChat({ isRTL });

  // ─── Local UI state ───
  const [input, setInput] = useState('');
  const [showScrollButton, setShowScrollButton] = useState(false);
  const [showWhatsApp, setShowWhatsApp] = useState(false);
  const [transcriptHighlight, setTranscriptHighlight] = useState(false);

  // ─── Voice ───
  const voice = useVoiceRecording({
    language: isRTL ? 'ar-EG' : 'auto',
    silenceThresholdMs: 2000,
    onTranscript: (text) => {
      setInput(text);
      setTranscriptHighlight(true);
      setTimeout(() => setTranscriptHighlight(false), 600);
    },
    onError: (msg) => console.warn('[Voice]', msg),
  });

  // ─── Refs ───
  const scrollRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);

  // ─── Sidebar trigger event listener ───
  useEffect(() => {
    const handler = (event: CustomEvent<{ message: string }>) => {
      if (event.detail?.message && !streaming.isStreaming) {
        handleSend(event.detail.message);
      }
    };
    window.addEventListener('triggerChatMessage', handler as EventListener);
    return () => window.removeEventListener('triggerChatMessage', handler as EventListener);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [streaming.isStreaming]);

  // ─── Auto-scroll ───
  useEffect(() => {
    if (scrollRef.current && streaming.hasMessages) {
      scrollRef.current.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' });
    }
  }, [streaming.messages, streaming.isStreaming, streaming.hasMessages]);

  // ─── Scroll awareness ───
  const handleScroll = useCallback(() => {
    if (scrollRef.current) {
      const { scrollTop, scrollHeight, clientHeight } = scrollRef.current;
      setShowScrollButton(scrollHeight - scrollTop - clientHeight > 100);
    }
  }, []);

  const scrollToBottom = useCallback(() => {
    scrollRef.current?.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' });
  }, []);

  // ─── Voice toggle ───
  const handleVoiceInput = useCallback(() => {
    if (voice.isListening || voice.status === 'processing') {
      voice.stopRecording();
    } else {
      voice.startRecording();
    }
  }, [voice]);

  // ─── Property selection ───
  const handlePropertySelect = useCallback(
    (property: Property, uiActions?: UIAction[]) => {
      if (!onPropertySelect) return;
      onPropertySelect(mapPropertyToContext(property, uiActions, streaming.effectiveRTL));
    },
    [onPropertySelect, streaming.effectiveRTL],
  );

  // ─── Send ───
  const handleSend = useCallback(
    async (text?: string) => {
      const messageText = text || input.trim();
      if (!messageText || streaming.isStreaming) return;
      setInput('');
      if (inputRef.current) inputRef.current.style.height = 'auto';
      await streaming.send(messageText);
    },
    [input, streaming],
  );

  // ─── Keyboard ───
  const handleKeyDown = useCallback(
    (e: React.KeyboardEvent) => {
      if (e.key === 'Enter' && !e.shiftKey) {
        e.preventDefault();
        handleSend();
      }
    },
    [handleSend],
  );

  // ─── Input auto-resize ───
  const handleInputChange = useCallback((e: React.ChangeEvent<HTMLTextAreaElement>) => {
    setInput(e.target.value);
    e.target.style.height = 'auto';
    e.target.style.height = Math.min(e.target.scrollHeight, 200) + 'px';
  }, []);

  // ─── Status label ───
  const streamStatusLabel = streaming.activeTool
    ? streaming.effectiveRTL
      ? `🔧 ${streaming.activeTool}...`
      : `🔧 Running ${streaming.activeTool}...`
    : streaming.streamStatus === 'connecting'
      ? streaming.effectiveRTL
        ? 'جاري الاتصال...'
        : 'Connecting...'
      : null;

  return {
    // Streaming state (passthrough)
    ...streaming,

    // Local UI state
    input,
    showScrollButton,
    showWhatsApp,
    setShowWhatsApp,
    transcriptHighlight,

    // Voice
    voiceStatus: voice.status as RecordingStatus,
    isListening: voice.isListening,
    amplitude: voice.amplitude,

    // Refs
    scrollRef,
    inputRef,

    // Derived
    streamStatusLabel,

    // Actions
    handleSend,
    handleKeyDown,
    handleInputChange,
    handleScroll,
    scrollToBottom,
    handleVoiceInput,
    handlePropertySelect,
  };
}
