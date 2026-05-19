'use client';

import React, { useState, useEffect, useRef, useCallback, useMemo } from 'react';
import { useSearchParams, useRouter as useNextRouter } from 'next/navigation';
import { motion, AnimatePresence, LayoutGroup, useReducedMotion } from 'framer-motion';
import {
  Sparkles, X, ChevronRight,
  BarChart2, Shield, Search, TrendingUp,
  History, Plus, MessageSquare, Lock,
} from 'lucide-react';
import Link from 'next/link';
import api from '@/lib/api';
import { streamChat } from '@/lib/api';
import { useAuth } from '@/contexts/AuthContext';
import { useGamification } from '@/contexts/GamificationContext';
import { Scale } from 'lucide-react';
import { toggleFavorite } from '@/lib/gamification';
import type { SuggestionChipItem } from '@/components/SuggestionChips';
import OnboardingFlow from '@/components/chat/OnboardingFlow';
import { getSmartEmptyStateSuggestions } from '@/lib/suggestions';
import ChatInsightsShell from '@/components/chat/ChatInsightsShell';
import MarketPulseSidebar from '@/components/MarketPulseSidebar';
import MessageSkeleton from '@/components/chat/MessageSkeleton';
import { useVoiceRecording } from '@/hooks/useVoiceRecording';
import { useVoicePlayback } from '@/hooks/useVoicePlayback';
import NeuralBackground from '@/components/NeuralBackground';
import OrchestratorSignalPanel from '@/components/chat/OrchestratorSignalPanel';

/* ── Decomposed components ── */
import ChatMessage from '@/components/chat/ChatMessage';
import { AgentAvatar } from '@/components/chat/ChatMessage';
import ChatInputBar from '@/components/chat/ChatInputBar';
import ThinkingSteps from '@/components/chat/ThinkingSteps';
import {
  composeSignalLabel,
  completeSignalLabel,
  errorSignalLabel,
  inferPhaseFromSignal,
  initialSignalLabel,
  labelForTool,
  responseTypeToRouteLabel,
  type NeuralPhase,
  type NeuralSignalSnapshot,
  type NeuralSignalStep,
  type NeuralStepStatus,
} from '@/components/chat/neural-signals';

import {
  isArabic,
  mapChatPropertyToProperty,
  getTimeAgo,
  guessConversationTag,
  getErrorMessage,
  STORAGE_KEYS,
  loadFromStorage,
  saveToStorage,
  getOrCreateSessionId,
  type Message,
  type Property,
  type Artifacts,
  type ChatPropertyPayload,
  type UiAction,
  type AnalyticsContext,
  type PastSession,
} from '@/lib/chat-utils';

/* ─── Constants ──────────────────────────────── */
const FREE_MESSAGE_LIMIT = 3;
type ChatMode = 'compare' | 'market' | 'advisor';

interface ChatResponsePayload {
  properties?: ChatPropertyPayload[];
  ui_actions?: UiAction[];
  suggestions?: string[];
  lead_score?: number;
  readiness_score?: number;
  detected_language?: string;
  showing_strategy?: string;
  analytics_context?: AnalyticsContext | null;
  response?: string;
  message?: string;
}

interface ChatHistoryMessagePayload {
  id?: number;
  role?: string;
  content?: string;
  properties?: Property[];
}

const getChatModeTabs = (language: string) => {
  const isAr = language === 'ar';
  return [
    {
      id: 'compare' as const,
      icon: Scale,
      label: isAr ? 'مقارنة الأسعار' : 'Price Compare',
      hint: isAr ? 'مطور مقابل resale' : 'Dev vs resale',
    },
    {
      id: 'market' as const,
      icon: BarChart2,
      label: isAr ? 'نبض السوق' : 'Market Pulse',
      hint: isAr ? 'اتجاهات وسيولة' : 'Trends and liquidity',
    },
    {
      id: 'advisor' as const,
      icon: Shield,
      label: isAr ? 'قرار الاستثمار' : 'Investment Fit',
      hint: isAr ? 'مخاطر وثقة' : 'Risk and confidence',
    },
  ];
};

const getModePlaceholder = (mode: ChatMode, language: string) => {
  const isAr = language === 'ar';
  if (mode === 'compare') {
    return isAr
      ? 'اكتب 2 أو 3 كمبوندات للمقارنة بين سعر المطور والـ resale...'
      : 'Name 2 or 3 compounds to compare developer price vs resale...';
  }
  if (mode === 'market') {
    return isAr
      ? 'اسأل عن اتجاه السعر أو السيولة في منطقة محددة...'
      : 'Ask about price trends or liquidity in a specific area...';
  }
  return isAr
    ? 'اسأل عن مطور أو مشروع قبل قرار الشراء...'
    : 'Ask about a developer or project before making a decision...';
};

function ChatModeTabs({
  activeMode,
  onChange,
  language,
  compact = false,
}: {
  activeMode: ChatMode;
  onChange: (mode: ChatMode) => void;
  language: string;
  compact?: boolean;
}) {
  const reduceMotion = useReducedMotion();
  const tabs = getChatModeTabs(language);

  return (
    <div
      className={`relative grid grid-cols-3 gap-1 rounded-[20px] border border-[var(--color-border)]/70 bg-[var(--color-surface)]/72 p-1 shadow-[0_18px_56px_-42px_rgba(15,23,42,0.72)] backdrop-blur-xl ${compact ? 'w-full' : 'mx-auto w-full max-w-2xl'}`}
      role="tablist"
      aria-label={language === 'ar' ? 'أنماط المحادثة' : 'Chat modes'}
    >
      {tabs.map((tab) => {
        const Icon = tab.icon;
        const isActive = activeMode === tab.id;
        return (
          <button
            key={tab.id}
            type="button"
            role="tab"
            aria-selected={isActive}
            onClick={() => onChange(tab.id)}
            className={`relative isolate flex min-h-11 items-center justify-center gap-2 overflow-hidden rounded-2xl px-2.5 py-2 text-center transition-colors ${isActive ? 'text-[var(--color-text-primary)]' : 'text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)]'}`}
          >
            {isActive && (
              <motion.span
                layoutId="chat-mode-active-tab"
                className="absolute inset-0 -z-10 rounded-2xl border border-emerald-500/20 bg-emerald-500/10 shadow-[inset_0_1px_0_rgba(255,255,255,0.18)]"
                transition={reduceMotion ? { duration: 0 } : { type: 'spring', damping: 28, stiffness: 360 }}
              />
            )}
            <Icon className={`h-4 w-4 flex-shrink-0 ${isActive ? 'text-emerald-600 dark:text-emerald-400' : 'text-[var(--color-text-muted)]'}`} strokeWidth={2} />
            <span className="min-w-0">
              <span className="block truncate text-[11px] font-semibold leading-tight sm:text-[12px]">{tab.label}</span>
              {!compact && <span className="mt-0.5 hidden truncate text-[10px] font-medium text-[var(--color-text-muted)] sm:block">{tab.hint}</span>}
            </span>
          </button>
        );
      })}
    </div>
  );
}

/* ─── Anonymous Gate ─────────────────────────── */
const AnonymousChatGate = ({ language }: { language: string }) => {
  const isAr = language === 'ar';
  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      className="mx-auto max-w-lg text-center py-10 px-6"
      dir={isAr ? 'rtl' : 'ltr'}
    >
      <div className="mx-auto mb-5 flex h-14 w-14 items-center justify-center rounded-2xl bg-emerald-500/10 border border-emerald-500/20">
        <Lock className="h-6 w-6 text-emerald-500" />
      </div>
      <h3 className="text-xl font-semibold text-[var(--color-text-primary)] mb-2">
        {isAr ? 'عجبك اللي شوفته؟' : "Liked what you've seen?"}
      </h3>
      <p className="text-sm text-[var(--color-text-secondary)] mb-6 leading-relaxed">
        {isAr
          ? 'سجّل دلوقتي عشان تكمّل المحادثة وتحفظ تحليلاتك — وده مجاني تماماً.'
          : 'Sign up to continue the conversation, save your analyses, and unlock full access — completely free.'}
      </p>
      <div className="flex flex-col sm:flex-row items-center justify-center gap-3">
        <Link
          href="/signup"
          className="px-6 py-3 bg-emerald-600 hover:bg-emerald-700 text-white rounded-full text-sm font-semibold transition-colors shadow-lg shadow-emerald-500/20"
        >
          {isAr ? 'إنشاء حساب' : 'Create Account'}
        </Link>
        <Link
          href="/login"
          className="px-6 py-3 border border-[var(--color-border)] hover:border-emerald-500/40 rounded-full text-sm font-medium text-[var(--color-text-primary)] transition-colors"
        >
          {isAr ? 'تسجيل الدخول' : 'Sign In'}
        </Link>
      </div>
    </motion.div>
  );
};

/* ═══════════════════════════════════════════════
   AgentInterface — Chat layout orchestrator
   ═══════════════════════════════════════════════ */
export default function AgentInterface() {
  const { user } = useAuth();
  const { profile, triggerXP } = useGamification();
  const searchParams = useSearchParams();
  const nextRouter = useNextRouter();

  /* ── State ── */
  const [transcriptHighlight, setTranscriptHighlight] = useState(false);
  const [messages, setMessages] = useState<Message[]>(() => loadFromStorage(STORAGE_KEYS.MESSAGES, []));
  const [inputValue, setInputValue] = useState('');
  const [isTyping, setIsTyping] = useState(false);
  const [contextPaneOpen, setContextPaneOpen] = useState(false);
  const [activeContext, setActiveContext] = useState<Artifacts | null>(null);
  const [recentQueries, setRecentQueries] = useState<string[]>([]);
  const [conversationLeadScore, setConversationLeadScore] = useState(0);
  const [conversationReadiness, setConversationReadiness] = useState(0);
  const [conversationLanguage, setConversationLanguage] = useState('ar');
  const [neuralPhase, setNeuralPhase] = useState<NeuralPhase>('idle');
  const [signalSteps, setSignalSteps] = useState<NeuralSignalStep[]>([]);
  const [signalRouteLabel, setSignalRouteLabel] = useState('Intelligence path');
  const [lastSignalStatus, setLastSignalStatus] = useState('');
  const [isLocalSignalPath, setIsLocalSignalPath] = useState(false);
  const [lastAiMsgId, setLastAiMsgId] = useState<number | null>(null);
  const [pastSessions, setPastSessions] = useState<PastSession[]>([]);
  const [historyOpen, setHistoryOpen] = useState(false);
  const [anonGateShown, setAnonGateShown] = useState(false);
  const [savedPropertyIds, setSavedPropertyIds] = useState<Set<string>>(new Set());
  const [isPinnedToBottom, setIsPinnedToBottom] = useState(true);
  const [showNewMessagesCue, setShowNewMessagesCue] = useState(false);
  const [activeMode, setActiveMode] = useState<ChatMode>('compare');

  const messagesEndRef = useRef<HTMLDivElement>(null);
  const scrollViewportRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  const sessionIdRef = useRef<string>(getOrCreateSessionId());
  const hasFetchedHistory = useRef(false);
  const seededPromptRef = useRef<string | null>(null);
  const signalStepCounterRef = useRef(0);
  const signalResetTimerRef = useRef<number | null>(null);

  const userName = user?.full_name || user?.email?.split('@')[0] || (conversationLanguage === 'ar' ? 'مستثمر' : 'there');
  const hasStarted = messages.length > 0;
  const userMessageCount = messages.filter(m => m.role === 'user').length;
  const isAnonymous = !user;
  const isGated = isAnonymous && userMessageCount >= FREE_MESSAGE_LIMIT;

  const latestAgentMessage = useMemo(
    () => [...messages].reverse().find((message) => message.role === 'agent'),
    [messages]
  );

  const latestRoute = useMemo(
    () => responseTypeToRouteLabel(latestAgentMessage?.responseType, conversationLanguage),
    [latestAgentMessage?.responseType, conversationLanguage]
  );

  const isConsultantHandoff = useMemo(() => {
    if (!latestAgentMessage) return false;

    const hasCta = Array.isArray(latestAgentMessage.ctaActions) && latestAgentMessage.ctaActions.length > 0;
    const upsellSignal = latestAgentMessage.showUpsell || hasCta;
    if (upsellSignal) return true;

    const reason = (latestAgentMessage.upsellReason || '').toLowerCase();
    return /complex|forecast|macro|inflation|hedge|consult|roi/i.test(reason);
  }, [latestAgentMessage]);

  const inputPlaceholder = useMemo(
    () => getModePlaceholder(activeMode, conversationLanguage),
    [activeMode, conversationLanguage]
  );

  const businessMode: 'free' | 'consultant' | 'premium' = useMemo(() => {
    if (isConsultantHandoff) return 'consultant';
    if (latestRoute.isLocalPath || isLocalSignalPath) return 'free';
    return 'premium';
  }, [isConsultantHandoff, latestRoute.isLocalPath, isLocalSignalPath]);

  const businessModeCopy = useMemo(() => {
    const isAr = conversationLanguage === 'ar';

    if (businessMode === 'consultant') {
      return {
        chip: isAr ? 'تحويل إلى الاستشاري' : 'Consultant Handoff',
        title: isAr
          ? 'هذا السؤال يحتاج تحليل تنبؤي عميق'
          : 'This question needs predictive deep analysis',
        description: isAr
          ? 'أنت الآن على مسار التحويل: إمّا التحدث مع مستشار أول أو فتح Osool Premium للتحليل المتقدم.'
          : 'You are now on the monetization handoff path: talk to a senior consultant or unlock Osool Premium.',
      };
    }

    if (businessMode === 'premium') {
      return {
        chip: isAr ? 'مسار الذكاء الكامل' : 'Full Intelligence Path',
        title: isAr ? 'التحليل يتم عبر محرك أصول المتقدم' : 'Analysis is running on Osool advanced intelligence',
        description: isAr
          ? 'هذا المسار يدعم التحليلات العميقة متعددة العوامل وحالات السوق المعقدة.'
          : 'This path supports deep multi-factor analytics and complex market scenarios.',
      };
    }

    return {
      chip: isAr ? 'المسار المجاني بدون توكن' : 'Zero-Token Free Path',
      title: isAr ? 'تحليل فوري من المحرك المحلي' : 'Instant response from local analytical engine',
      description: isAr
        ? 'أنت على المسار المجاني: استخراج نية محلي + SQL + تقييم سعري دون استهلاك توكنات.'
        : 'You are on the free path: local intent parsing + SQL retrieval + deterministic pricing without token spend.',
    };
  }, [businessMode, conversationLanguage]);

  const clearSignalResetTimer = useCallback(() => {
    if (signalResetTimerRef.current !== null) {
      window.clearTimeout(signalResetTimerRef.current);
      signalResetTimerRef.current = null;
    }
  }, []);

  const completeActiveSignalStep = useCallback((status: NeuralStepStatus = 'complete') => {
    setSignalSteps((prev): NeuralSignalStep[] => prev.map((step): NeuralSignalStep => (
      step.status === 'active' ? { ...step, status } : step
    )));
  }, []);

  const pushSignalStep = useCallback((label: string, phase: NeuralPhase, source: NeuralSignalStep['source'] = 'stream') => {
    const normalized = label.trim();
    if (!normalized) return;

    const id = `signal_${Date.now()}_${signalStepCounterRef.current += 1}`;
    setNeuralPhase(phase);
    setLastSignalStatus(normalized);
    setSignalSteps((prev): NeuralSignalStep[] => {
      const completed = prev.map((step): NeuralSignalStep => (
        step.status === 'active' ? { ...step, status: 'complete' as const } : step
      ));
      const previous = completed[completed.length - 1];
      if (previous?.label.toLowerCase() === normalized.toLowerCase()) return completed;
      const nextStep: NeuralSignalStep = { id, label: normalized, phase, status: 'active', source, timestamp: Date.now() };
      return [...completed, nextStep].slice(-8);
    });
  }, []);

  const beginNeuralSignal = useCallback(() => {
    clearSignalResetTimer();
    signalStepCounterRef.current = 0;
    const initialLabel = initialSignalLabel(conversationLanguage);
    const route = responseTypeToRouteLabel(undefined, conversationLanguage);

    setNeuralPhase('routing');
    setSignalRouteLabel(route.label);
    setIsLocalSignalPath(false);
    setLastSignalStatus(initialLabel);
    setSignalSteps([{
      id: `signal_${Date.now()}_0`,
      label: initialLabel,
      phase: 'routing',
      status: 'active',
      source: 'system',
      timestamp: Date.now(),
    }]);
  }, [clearSignalResetTimer, conversationLanguage]);

  const settleNeuralSignal = useCallback((phase: 'complete' | 'error', label: string, responseType?: string) => {
    clearSignalResetTimer();
    const route = responseTypeToRouteLabel(responseType, conversationLanguage);
    const status: NeuralStepStatus = phase === 'error' ? 'error' : 'complete';

    setNeuralPhase(phase);
    setSignalRouteLabel(route.label);
    setIsLocalSignalPath(route.isLocalPath);
    setLastSignalStatus(label);
    setSignalSteps((prev): NeuralSignalStep[] => {
      const source: NeuralSignalStep['source'] = route.isLocalPath ? 'local' : 'stream';
      const completed = prev.map((step): NeuralSignalStep => (
        step.status === 'active' ? { ...step, status } : step
      ));
      return [...completed, {
        id: `signal_${Date.now()}_${signalStepCounterRef.current += 1}`,
        label,
        phase,
        status,
        source,
        timestamp: Date.now(),
      }].slice(-8);
    });

    signalResetTimerRef.current = window.setTimeout(() => {
      setNeuralPhase('idle');
      setLastSignalStatus('');
    }, phase === 'error' ? 4500 : 3200);
  }, [clearSignalResetTimer, conversationLanguage]);

  const resetNeuralSignal = useCallback(() => {
    clearSignalResetTimer();
    setNeuralPhase('idle');
    setSignalSteps([]);
    setSignalRouteLabel(responseTypeToRouteLabel(undefined, conversationLanguage).label);
    setLastSignalStatus('');
    setIsLocalSignalPath(false);
  }, [clearSignalResetTimer, conversationLanguage]);

  const neuralIntensity = useMemo(() => {
    if (neuralPhase === 'idle') return 0.18;
    if (neuralPhase === 'routing') return 0.48;
    if (neuralPhase === 'searching') return 0.72;
    if (neuralPhase === 'analyzing') return 0.86;
    if (neuralPhase === 'responding') return 0.78;
    if (neuralPhase === 'complete') return 0.42;
    return 0.62;
  }, [neuralPhase]);

  const neuralSnapshot = useMemo<NeuralSignalSnapshot>(() => ({
    phase: neuralPhase,
    steps: signalSteps,
    routeLabel: signalRouteLabel || responseTypeToRouteLabel(undefined, conversationLanguage).label,
    lastStatus: lastSignalStatus,
    intensity: neuralIntensity,
    isLocalPath: isLocalSignalPath,
  }), [conversationLanguage, isLocalSignalPath, lastSignalStatus, neuralIntensity, neuralPhase, signalRouteLabel, signalSteps]);

  const signalPanelVisible = hasStarted && neuralPhase !== 'idle';

  useEffect(() => () => clearSignalResetTimer(), [clearSignalResetTimer]);

  /* ── Voice ── */
  const { status: voiceStatus, isListening, amplitude, startRecording, stopRecording } = useVoiceRecording({
    language: conversationLanguage === 'ar' ? 'ar-EG' : 'auto',
    silenceThresholdMs: 2000,
    onTranscript: (text) => {
      setInputValue(text);
      inputRef.current?.focus();
      setTranscriptHighlight(true);
      setTimeout(() => setTranscriptHighlight(false), 600);
    },
    onError: (msg) => console.warn('[Voice]', msg),
  });
  const { playbackStatus, speak: speakTTS, pause: pauseTTS, resume: resumeTTS, stop: stopTTS } = useVoicePlayback();

  const handleVoiceToggle = useCallback(() => {
    if (isListening || voiceStatus === 'processing') {
      stopRecording();
    } else {
      stopTTS();
      startRecording();
    }
  }, [isListening, voiceStatus, startRecording, stopRecording, stopTTS]);

  const handleSpeakerClick = useCallback((text: string, lang: string) => {
    if (playbackStatus === 'playing') pauseTTS();
    else if (playbackStatus === 'paused') resumeTTS();
    else speakTTS(text, lang);
  }, [playbackStatus, speakTTS, pauseTTS, resumeTTS]);

  /* ── Persistence ── */
  useEffect(() => {
    if (messages.length > 0) saveToStorage(STORAGE_KEYS.MESSAGES, messages);
  }, [messages]);

  /* ── Fetch past sessions ── */
  useEffect(() => {
    if (!user) return;
    if (hasFetchedHistory.current) return;
    hasFetchedHistory.current = true;
    api.get('/api/chat/history').then(res => {
      const sessions: PastSession[] = (res.data?.sessions || []).filter(
        (s: PastSession) => s.session_id !== sessionIdRef.current
      );
      setPastSessions(sessions);
    }).catch(() => {});
  }, [user]);

  /* ── Scroll management ── */
  const scrollToBottom = useCallback((behavior: ScrollBehavior = 'smooth') => {
    const viewport = scrollViewportRef.current;
    if (!viewport) return;
    viewport.scrollTo({ top: viewport.scrollHeight, behavior });
    setIsPinnedToBottom(true);
    setShowNewMessagesCue(false);
  }, []);

  const handleScroll = useCallback(() => {
    const viewport = scrollViewportRef.current;
    if (!viewport) return;
    const distanceFromBottom = viewport.scrollHeight - viewport.scrollTop - viewport.clientHeight;
    const nearBottom = distanceFromBottom < 120;
    setIsPinnedToBottom(nearBottom);
    if (nearBottom) setShowNewMessagesCue(false);
  }, []);

  useEffect(() => {
    if (!hasStarted) return;
    if (isPinnedToBottom) {
      const frame = window.requestAnimationFrame(() => {
        scrollToBottom(isTyping ? 'auto' : 'smooth');
      });
      return () => window.cancelAnimationFrame(frame);
    }
    setShowNewMessagesCue(true);
  }, [messages, isTyping, hasStarted, isPinnedToBottom, scrollToBottom]);

  useEffect(() => {
    const timer = setTimeout(() => { inputRef.current?.focus(); }, 500);
    return () => clearTimeout(timer);
  }, [hasStarted]);

  /* ── Smart suggestions ── */
  const emptyStateSuggestions = useMemo(
    () => getSmartEmptyStateSuggestions(
      conversationLanguage,
      typeof profile?.level === 'string' ? profile.level : 'curious',
      savedPropertyIds.size
    ),
    [conversationLanguage, profile?.level, savedPropertyIds.size]
  );
  const minimalEmptySuggestions = useMemo(() => emptyStateSuggestions.slice(0, 4), [emptyStateSuggestions]);

  /* ── Send message ── */
  const handleSendMessage = useCallback(async (text?: string) => {
    const content = text || inputValue;
    if (!content.trim() || isTyping) return;

    if (!user) {
      const currentUserMsgCount = messages.filter(m => m.role === 'user').length;
      if (currentUserMsgCount >= FREE_MESSAGE_LIMIT) {
        setAnonGateShown(true);
        return;
      }
    }

    setRecentQueries(prev => {
      const updated = [content.slice(0, 40), ...prev.filter(q => q !== content.slice(0, 40))];
      return updated.slice(0, 5);
    });

    const userMsg: Message = { id: Date.now(), role: 'user', content };
    setMessages(prev => [...prev, userMsg]);
    setInputValue('');
    setIsTyping(true);
    beginNeuralSignal();

    const aiMsgId = Date.now() + 1;
    let accumulatedText = '';
    let streamingStarted = false;

    try {
      await streamChat(
        content,
        sessionIdRef.current,
        {
          onToken: (token) => {
            accumulatedText += (typeof token === 'string' ? token : '');
            if (!streamingStarted) {
              streamingStarted = true;
              pushSignalStep(composeSignalLabel(conversationLanguage), 'responding', 'stream');
              setIsTyping(false);
              setMessages(prev => [...prev, { id: aiMsgId, role: 'agent', content: accumulatedText }]);
            } else {
              const currentText = accumulatedText;
              setMessages(prev => prev.map(m => m.id === aiMsgId ? { ...m, content: currentText } : m));
            }
          },
          onToolStart: (tool) => {
            const label = labelForTool(tool, conversationLanguage);
            pushSignalStep(label, inferPhaseFromSignal(`${tool} ${label}`), 'tool');
          },
          onToolEnd: () => {
            completeActiveSignalStep('complete');
          },
          onStatus: (message) => {
            const phase = inferPhaseFromSignal(message);
            const source = /local|free|zero|deterministic/i.test(message) ? 'local' : 'stream';
            pushSignalStep(message, phase, source);
          },
          onComplete: (data) => {
            settleNeuralSignal('complete', completeSignalLabel(conversationLanguage), data.response_type);
            const allProps = Array.isArray(data.properties) ? data.properties.map(mapChatPropertyToProperty) : [];
            const uiActions = Array.isArray(data.ui_actions) ? (data.ui_actions as UiAction[]) : [];
            const artifacts: Artifacts | null = allProps.length > 0 ? { property: allProps[0] } : null;
            const finalContent = accumulatedText || (conversationLanguage === 'ar'
              ? 'أنا Osool Advisor، مستشار الاستثمار العقاري الخاص بك. كيف أقدر أساعدك النهارده؟'
              : "I'm Osool Advisor, your real estate intelligence guide. How can I assist you today?");

            setMessages(prev => {
              const hasMsg = prev.some(m => m.id === aiMsgId);
              const msgData: Message = {
                id: aiMsgId,
                role: 'agent',
                content: finalContent,
                artifacts,
                uiActions,
                allProperties: allProps,
                suggestions: data.suggestions || [],
                leadScore: data.lead_score || 0,
                readinessScore: data.readiness_score || 0,
                detectedLanguage: data.detected_language || 'ar',
                showingStrategy: data.showing_strategy || 'NONE',
                responseType: data.response_type,
                showUpsell: data.show_upsell,
                upsellReason: data.upsell_reason,
                quotaRemaining: data.quota_remaining,
                ctaActions: data.cta_actions || [],
              };
              if (!hasMsg) return [...prev, msgData];
              return prev.map(m => m.id === aiMsgId ? { ...m, ...msgData } : m);
            });

            setConversationLeadScore(data.lead_score || 0);
            setConversationReadiness(data.readiness_score || 0);
            if (data.detected_language) setConversationLanguage(data.detected_language);
            setIsTyping(false);
            triggerXP(5, 'Asked a question');
            if (data.ui_actions && data.ui_actions.length > 0) triggerXP(15, 'Used analysis tool');
            if (artifacts) setActiveContext(artifacts);
          },
          onError: (error) => {
            console.error('[Osool Advisor] Stream Error:', error);
            settleNeuralSignal('error', errorSignalLabel(conversationLanguage));
            const errorContent = conversationLanguage === 'ar'
              ? 'حصل مشكلة بسيطة في التحليل. ممكن تعيد السؤال تاني؟'
              : 'A brief analysis issue occurred. Could you try again?';
            setMessages(prev => {
              const hasMsg = prev.some(m => m.id === aiMsgId);
              if (!hasMsg) return [...prev, { id: aiMsgId, role: 'agent' as const, content: errorContent, artifacts: null }];
              return prev.map(m => m.id === aiMsgId ? { ...m, content: errorContent } : m);
            });
            setIsTyping(false);
          },
        },
        'auto'
      );
    } catch (error: unknown) {
      console.warn('[Osool Advisor] SSE failed, falling back to POST:', getErrorMessage(error, 'Unknown'));
      try {
        pushSignalStep(conversationLanguage === 'ar' ? 'تشغيل الرد البديل' : 'Using fallback response', 'analyzing', 'stream');
        const response = await api.post('/api/chat', {
          message: content,
          session_id: sessionIdRef.current,
          language: 'auto',
        }, { timeout: 120000 });
        const data = response.data as ChatResponsePayload;
        const allProps = Array.isArray(data.properties) ? data.properties.map(mapChatPropertyToProperty) : [];
        const uiActions = Array.isArray(data.ui_actions) ? data.ui_actions : [];

        setMessages(prev => [...prev, {
          id: aiMsgId,
          role: 'agent',
          content: data.response || data.message || '',
          artifacts: allProps.length > 0 ? { property: allProps[0] } : null,
          uiActions,
          allProperties: allProps,
          suggestions: data.suggestions || [],
          leadScore: data.lead_score || 0,
          readinessScore: data.readiness_score || 0,
          detectedLanguage: data.detected_language || 'ar',
          showingStrategy: data.showing_strategy || 'NONE',
          analyticsContext: data.analytics_context || null,
        }]);
        setLastAiMsgId(aiMsgId);
        setConversationLeadScore(data.lead_score || 0);
        setConversationReadiness(data.readiness_score || 0);
        if (data.detected_language) setConversationLanguage(data.detected_language);
        settleNeuralSignal('complete', completeSignalLabel(conversationLanguage), undefined);
        triggerXP(5, 'Asked a question');
        if (allProps.length > 0) setActiveContext({ property: allProps[0] });
      } catch (fallbackErr: unknown) {
        console.error('[Osool Advisor] Fallback POST failed:', fallbackErr);
        settleNeuralSignal('error', errorSignalLabel(conversationLanguage));
        const errorMsg = conversationLanguage === 'ar'
          ? 'حصل مشكلة بسيطة في التحليل. ممكن تعيد السؤال تاني؟'
          : 'A brief analysis issue occurred. Could you try again?';
        setMessages(prev => [...prev, { id: aiMsgId, role: 'agent' as const, content: errorMsg, artifacts: null }]);
      }
    } finally {
      setIsTyping(false);
    }
  }, [beginNeuralSignal, completeActiveSignalStep, conversationLanguage, inputValue, isTyping, messages, pushSignalStep, settleNeuralSignal, triggerXP, user]);

  /* ── New chat ── */
  const handleNewChat = useCallback(() => {
    setMessages([]);
    setContextPaneOpen(false);
    setActiveContext(null);
    setInputValue('');
    setIsPinnedToBottom(true);
    setShowNewMessagesCue(false);
    setConversationLeadScore(0);
    setConversationReadiness(0);
    setConversationLanguage('ar');
    setActiveMode('compare');
    setLastAiMsgId(null);
    resetNeuralSignal();
    seededPromptRef.current = null;
    const newId = `session_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`;
    sessionIdRef.current = newId;
    sessionStorage.setItem(STORAGE_KEYS.SESSION_ID, newId);
    sessionStorage.removeItem(STORAGE_KEYS.MESSAGES);
  }, [resetNeuralSignal]);

  /* ── URL prompt seeding ── */
  useEffect(() => {
    const prompt = searchParams.get('prompt');
    if (!prompt || isTyping || seededPromptRef.current === prompt) return;

    const autostart = searchParams.get('autostart') === '1';
    seededPromptRef.current = prompt;
    nextRouter.replace('/chat', { scroll: false });

    if (messages.length > 0) handleNewChat();

    if (autostart) {
      const timer = window.setTimeout(() => { void handleSendMessage(prompt); }, 80);
      return () => window.clearTimeout(timer);
    }
    setInputValue(prompt);
    const focusTimer = window.setTimeout(() => { inputRef.current?.focus(); }, 60);
    return () => window.clearTimeout(focusTimer);
  }, [searchParams, messages.length, isTyping, handleNewChat, handleSendMessage, nextRouter]);

  /* ── Load past session ── */
  const loadSession = useCallback(async (sessionId: string) => {
    try {
      const res = await api.get(`/api/chat/history/${sessionId}`);
      const msgs: Message[] = ((res.data?.messages || []) as ChatHistoryMessagePayload[]).map((m, i: number) => ({
        id: m.id || Date.now() + i,
        role: m.role === 'user' ? 'user' : 'agent',
        content: m.content || '',
        artifacts: null,
        allProperties: Array.isArray(m.properties) ? m.properties.map(mapChatPropertyToProperty) : [],
      }));
      setMessages(msgs);
      sessionIdRef.current = sessionId;
      sessionStorage.setItem(STORAGE_KEYS.SESSION_ID, sessionId);
      saveToStorage(STORAGE_KEYS.MESSAGES, msgs);
      setIsPinnedToBottom(true);
      setShowNewMessagesCue(false);
      setLastAiMsgId(null);
      resetNeuralSignal();
      setHistoryOpen(false);
    } catch (err) {
      console.error('[History] Failed to load session', err);
    }
  }, [resetNeuralSignal]);

  /* ── Retry ── */
  const handleRetry = useCallback(async (msgIndex: number) => {
    const prevUserMsg = messages.slice(0, msgIndex).reverse().find(m => m.role === 'user');
    if (!prevUserMsg) return;
    setMessages(prev => prev.filter((_, i) => i !== msgIndex));
    await handleSendMessage(prevUserMsg.content);
  }, [messages, handleSendMessage]);

  /* ── Property actions ── */
  const handleSaveProperty = useCallback(async (prop: Property, e: React.MouseEvent) => {
    e.stopPropagation();
    if (!user) return;
    const propId = parseInt(String(prop.id), 10);
    if (isNaN(propId)) return;
    try {
      await toggleFavorite(propId);
      setSavedPropertyIds(prev => {
        const next = new Set(prev);
        if (next.has(String(prop.id))) next.delete(String(prop.id));
        else { next.add(String(prop.id)); triggerXP(10, 'Saved a property'); }
        return next;
      });
    } catch (err) {
      console.warn('[Chat] Failed to toggle favorite:', err);
    }
  }, [user, triggerXP]);

  const handleInlineValuation = useCallback((prop: Property, e: React.MouseEvent) => {
    e.stopPropagation();
    const prompt = conversationLanguage === 'ar'
      ? `شغّل تقييم AI على "${prop.title}" في ${prop.location} - سعره ${(prop.price / 1000000).toFixed(1)} مليون جنيه`
      : `Run AI valuation on "${prop.title}" in ${prop.location} - listed at ${(prop.price / 1000000).toFixed(1)}M EGP`;
    void handleSendMessage(prompt);
  }, [conversationLanguage, handleSendMessage]);

  const handleInlineCompare = useCallback((prop: Property, e: React.MouseEvent) => {
    e.stopPropagation();
    const prompt = conversationLanguage === 'ar'
      ? `قارن "${prop.title}" مع وحدات مشابهة في ${prop.location} في نفس النطاق السعري`
      : `Compare "${prop.title}" with similar units in ${prop.location} in the same price range`;
    void handleSendMessage(prompt);
  }, [conversationLanguage, handleSendMessage]);

  /* ── Onboarding ── */
  const [showOnboarding, setShowOnboarding] = useState(false);
  useEffect(() => {
    if (profile?.properties_analyzed === 0 && !localStorage.getItem('onboarding_skipped') && messages.length === 0) {
      setShowOnboarding(true);
    }
  }, [profile, messages.length]);

  const handleOnboardingComplete = (data: { goal: string; regions: string[]; budget: string }) => {
    localStorage.setItem('onboarding_skipped', 'true');
    setShowOnboarding(false);
    const prompt = `I am looking for ${data.goal} properties. ` +
      (data.regions.length > 0 ? `I prefer these regions: ${data.regions.join(', ')}. ` : '') +
      `My budget is ${data.budget}. Please recommend some options.`;
    handleSendMessage(prompt);
  };

  /* ── Suggestion enrichment (passed to ChatMessage) ── */
  const enrichSuggestion = useCallback((prompt: string, lang: string): SuggestionChipItem => {
    const lower = prompt.toLowerCase();
    const isAr = lang === 'ar' || isArabic(prompt);

    if (lower.includes('roi') || lower.includes('عائد') || lower.includes('invest') || lower.includes('استثمار'))
      return { icon: BarChart2, label: prompt, prompt, snippet: 'Returns, downside, and market fit', snippetAr: 'العائد والمخاطر وملاءمة السوق', trend: 'up' };
    if (lower.includes('developer') || lower.includes('مطور') || lower.includes('delivery') || lower.includes('تسليم'))
      return { icon: Shield, label: prompt, prompt, snippet: 'Track record, delays, and risk flags', snippetAr: 'سجل التنفيذ والتأخير وعلامات المخاطر', trend: 'neutral' };
    if (lower.includes('payment') || lower.includes('installment') || lower.includes('أقساط') || lower.includes('سداد'))
      return { icon: Sparkles, label: prompt, prompt, snippet: 'Down payment, tenure, and flexibility', snippetAr: 'المقدم ومدة السداد والمرونة', trend: 'neutral' };
    if (lower.includes('compare') || lower.includes('قارن') || lower.includes('similar') || lower.includes('مشابه'))
      return { icon: TrendingUp, label: prompt, prompt, snippet: 'Side-by-side shortlist with trade-offs', snippetAr: 'مقارنة سريعة مع إبراز الفروقات', trend: 'up' };
    return {
      icon: Search, label: prompt, prompt,
      snippet: isAr ? undefined : 'Fast follow-up from the current context',
      snippetAr: isAr ? 'متابعة سريعة من نفس سياق الحوار' : undefined,
      trend: 'neutral',
    };
  }, []);

  const generateSuggestions = useCallback((msg: Message): SuggestionChipItem[] => {
    const content = msg.content.toLowerCase();
    const hasProperties = msg.allProperties && msg.allProperties.length > 0;
    const hasAnalytics = msg.analyticsContext?.has_analytics;
    const lang = msg.detectedLanguage || conversationLanguage || 'ar';
    const isAr = lang === 'ar';
    const hash = content.split('').reduce((acc, c) => acc + c.charCodeAt(0), 0);

    if (content.includes('تضخم') || content.includes('inflation') || content.includes('فلوس'))
      return (isAr ? ['إزاي أحمي فلوسي؟', 'عقار ولا شهادات بنك؟', 'حلل العائد بعد التضخم'] : ['How to protect my money?', 'Property vs bank CDs?', 'Real return after inflation']).map(p => enrichSuggestion(p, lang));
    if (content.includes('مطور') || content.includes('developer') || content.includes('تسليم') || content.includes('delivery')) {
      const opts = isAr ? ['سجل التسليم بتاعهم', 'هل فيه مطور أضمن؟', 'ورّيني التقييمات', 'مواعيد التسليم', 'المشاريع المتأخرة'] : ['Their delivery track record', 'More reliable developer?', 'Show me ratings', 'Delivery timeline', 'Delayed projects'];
      return [opts[hash % opts.length], opts[(hash + 2) % opts.length], opts[(hash + 4) % opts.length]].map(p => enrichSuggestion(p, lang));
    }
    if (content.includes('ساحل') || content.includes('coast') || content.includes('سوخنة') || content.includes('sokhna'))
      return (isAr ? ['ساحل ولا سوخنة أحسن؟', 'العائد الإيجاري كام؟', 'أحسن كمبوند هناك؟'] : ['Coast vs Sokhna?', 'Rental yield there?', 'Best compound there?']).map(p => enrichSuggestion(p, lang));
    if (content.includes('أقساط') || content.includes('سداد') || content.includes('installment') || content.includes('payment'))
      return (isAr ? ['أطول خطة سداد؟', 'سداد بدون فوايد؟', 'قارن خطط السداد'] : ['Longest payment plan?', 'Interest-free options?', 'Compare payment plans']).map(p => enrichSuggestion(p, lang));

    if (hasProperties) {
      const opts = isAr ? ['قارن العقارات دي', 'تحليل العائد', 'خطة السداد؟', 'تفاصيل أكتر عن الوحدة', 'وحدات مشابهة أرخص', 'مخاطر القرار'] : ['Compare these properties', 'Show ROI analysis', 'Payment plan options?', 'More details on this unit', 'Similar but cheaper?', 'Decision risks'];
      return [opts[hash % opts.length], opts[(hash + 2) % opts.length], opts[(hash + 4) % opts.length]].map(p => enrichSuggestion(p, lang));
    }
    if (hasAnalytics) {
      const opts = isAr ? ['اتجاهات الأسعار', 'أفضل مناطق النمو', 'قارن البدائل', 'تحليل ضد التضخم', 'هل ده وقت مناسب؟'] : ['Show price trends', 'Best growth areas?', 'Compare alternatives', 'Inflation analysis', 'Is this a good time?'];
      return [opts[hash % opts.length], opts[(hash + 2) % opts.length], opts[(hash + 4) % opts.length]].map(p => enrichSuggestion(p, lang));
    }
    const opts = isAr ? ['أفضل العقارات', 'نظرة على السوق', 'حدد ميزانيتي', 'أفضل منطقة للاستثمار', 'إيه المطورين الموثوقين؟', 'فيه عروض حالياً؟', 'عايز أفهم العائد'] : ['Top properties', 'Market overview', 'Set my budget', 'Best area for investment', 'Reliable developers?', 'Any current deals?', 'Explain ROI to me'];
    return [opts[hash % opts.length], opts[(hash + 2) % opts.length], opts[(hash + 4) % opts.length]].map(p => enrichSuggestion(p, lang));
  }, [conversationLanguage, enrichSuggestion]);

  /* ════════════════════════════════════════════
     RENDER
     ════════════════════════════════════════════ */
  return (
    <LayoutGroup>
      <div className="flex h-full min-h-0 w-full bg-[var(--color-background)] text-[var(--color-text-primary)] overflow-hidden selection:bg-emerald-500/15 relative">
        <NeuralBackground phase={neuralPhase} intensity={neuralIntensity} />
        <main className="flex-1 flex flex-col relative min-w-0 h-full w-full min-h-0 z-10">

          {/* ── Top bar (in-conversation) ── */}
          {hasStarted && (
            <div className="sticky top-0 start-0 end-0 z-30 border-b border-[var(--color-border)]/40 bg-[var(--color-background)]/90 backdrop-blur-xl">
              <div className="max-w-full lg:max-w-[980px] mx-auto px-3 sm:px-4 md:px-6">
                <div className="flex flex-col gap-2 py-2.5">
                  <div className="flex items-center justify-between gap-3">
                    <div className="flex min-w-0 items-center gap-2.5">
                      <div className="flex h-9 w-9 flex-shrink-0 items-center justify-center rounded-2xl border border-emerald-500/20 bg-emerald-500/10 text-emerald-600 dark:text-emerald-400">
                        <Sparkles className="h-4 w-4" />
                      </div>
                      <div className="min-w-0">
                        <p className="truncate text-[13px] font-semibold tracking-tight text-[var(--color-text-primary)]">
                          Osool AI
                        </p>
                        <p className="truncate text-[11px] font-medium text-[var(--color-text-muted)]">
                          {conversationLanguage === 'ar' ? 'جلسة استثمار نشطة' : 'Live investment workspace'}
                        </p>
                      </div>
                    </div>
                    <div className="hidden min-w-[360px] max-w-[470px] flex-1 lg:block">
                      <ChatModeTabs activeMode={activeMode} onChange={setActiveMode} language={conversationLanguage} compact />
                    </div>
                  <div className="flex items-center gap-1 md:gap-2">
                    <button
                      onClick={() => setHistoryOpen(true)}
                      aria-label={conversationLanguage === 'ar' ? 'المحادثات السابقة' : 'Past conversations'}
                      className="inline-flex h-11 w-11 items-center justify-center rounded-2xl text-[var(--color-text-muted)] transition-all hover:bg-[var(--color-surface)] hover:text-[var(--color-text-primary)] active:scale-95"
                      title={conversationLanguage === 'ar' ? 'المحادثات السابقة' : 'Past Conversations'}
                    >
                      <History className="w-4 h-4" strokeWidth={2} />
                    </button>
                    <button
                      onClick={handleNewChat}
                      aria-label={conversationLanguage === 'ar' ? 'محادثة جديدة' : 'New chat'}
                      className="inline-flex h-11 w-11 items-center justify-center rounded-2xl text-[var(--color-text-muted)] transition-all hover:bg-[var(--color-surface)] hover:text-[var(--color-text-primary)] active:scale-95"
                      title={conversationLanguage === 'ar' ? 'محادثة جديدة' : 'New Chat'}
                    >
                      <Plus className="w-4 h-4" strokeWidth={2} />
                    </button>
                    </div>
                  </div>
                  <div className="lg:hidden">
                    <ChatModeTabs activeMode={activeMode} onChange={setActiveMode} language={conversationLanguage} compact />
                  </div>
                </div>
              </div>
            </div>
          )}

          {/* ── Scrollable content ── */}
          <div ref={scrollViewportRef} onScroll={handleScroll} className="flex-1 overflow-y-auto scroll-smooth">
            <div className="max-w-full lg:max-w-[980px] mx-auto h-full w-full">

              {/* ── Empty state / Greeting ── */}
              {!hasStarted && (
                <div className="flex flex-col min-h-[calc(100dvh-6.5rem)] sm:min-h-[calc(100vh-8rem)] justify-start sm:justify-center px-3 sm:px-4 pt-6 sm:py-6 pb-4 sm:pb-6">

                  <div className="text-center w-full max-w-3xl mx-auto">
                    <div className="flex items-center justify-center gap-3 mb-3">
                      <AgentAvatar />
                      <span className="text-[12px] font-semibold text-[var(--color-text-muted)] uppercase tracking-[0.18em]">Osool AI</span>
                    </div>
                    <h1 className="text-[1.6rem] sm:text-[2rem] md:text-[2.35rem] font-semibold tracking-tight leading-[1.15] mb-2 text-[var(--color-text-primary)]" dir="auto">
                      {conversationLanguage === 'ar' ? `أهلاً، ${userName}` : `Hello, ${userName}`}
                    </h1>
                    <p className="text-[0.92rem] sm:text-[0.98rem] md:text-[1rem] text-[var(--color-text-secondary)] font-normal max-w-xl mx-auto leading-relaxed px-2 sm:px-4 md:px-0" dir="auto">
                      {conversationLanguage === 'ar' ? 'ابدأ بمقارنة محددة، قراءة للسوق، أو فحص قرار الاستثمار.' : 'Start with a focused comparison, market read, or investment decision check.'}
                    </p>
                  </div>

                  <div className="mx-auto mt-5 w-full px-1 sm:px-4">
                    <ChatModeTabs activeMode={activeMode} onChange={setActiveMode} language={conversationLanguage} />
                  </div>

                  {/* Input */}
                  <div className="w-full max-w-[800px] mx-auto mt-4 sm:mt-6 px-1 sm:px-4">
                    <ChatInputBar
                      value={inputValue}
                      onChange={setInputValue}
                      onSend={() => handleSendMessage()}
                      disabled={isTyping}
                      language={conversationLanguage}
                      voiceStatus={voiceStatus}
                      amplitude={amplitude}
                      isListening={isListening}
                      transcriptHighlight={transcriptHighlight}
                      onVoiceToggle={handleVoiceToggle}
                      inputRef={inputRef}
                      placeholder={inputPlaceholder}
                    />
                  </div>

                  {/* Suggestion cards — 2×2 grid on all breakpoints */}
                  <div className="w-full max-w-[600px] mx-auto mt-4 px-3">
                    <div className="grid grid-cols-2 gap-2.5">
                      {minimalEmptySuggestions.slice(0, 4).map((s, i) => {
                        const Icon = s.icon;
                        return (
                          <button
                            key={i}
                            onMouseDown={(e) => e.preventDefault()}
                            onClick={() => { handleSendMessage(s.prompt); setTimeout(() => inputRef.current?.focus(), 100); }}
                            className="flex flex-col items-start rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)] p-3.5 text-start transition-all hover:border-emerald-500/30 hover:bg-[var(--color-surface-elevated)] focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500/40 active:scale-[0.98] group"
                          >
                            <div className="flex items-center gap-2 mb-1">
                              {Icon && <Icon className="w-3.5 h-3.5 text-emerald-500 flex-shrink-0" />}
                              <span dir="auto" className="text-[12px] font-semibold text-[var(--color-text-primary)] leading-snug line-clamp-1">
                                {s.label}
                              </span>
                            </div>
                            {(conversationLanguage === 'ar' ? s.snippetAr : s.snippet) && (
                              <span className="text-[11px] text-[var(--color-text-muted)] leading-relaxed line-clamp-2">
                                {conversationLanguage === 'ar' ? s.snippetAr : s.snippet}
                              </span>
                            )}
                          </button>
                        );
                      })}
                    </div>
                  </div>

                  {/* Past sessions */}
                  {pastSessions.length > 0 && (
                    <div className="hidden md:block w-full max-w-2xl mx-auto mt-8 px-4">
                      <button
                        onClick={() => setHistoryOpen(true)}
                        className="flex items-center gap-2 text-[13px] font-medium text-[var(--color-text-secondary)] hover:text-[var(--color-text-primary)] mx-auto mb-3 transition-colors"
                      >
                        <History className="w-3.5 h-3.5" />
                        {conversationLanguage === 'ar' ? 'المحادثات السابقة' : 'Recent conversations'}
                      </button>
                      <div className="space-y-1.5">
                        {pastSessions.slice(0, 3).map(s => {
                          const timeAgo = s.last_message_at ? getTimeAgo(s.last_message_at, conversationLanguage) : null;
                          const tag = guessConversationTag(s.preview);
                          return (
                            <button
                              key={s.session_id}
                              onClick={() => loadSession(s.session_id)}
                              className="w-full flex items-center gap-3 p-3 rounded-2xl bg-[var(--color-surface)]/50 hover:bg-[var(--color-surface)] border border-[var(--color-border)]/50 hover:border-[var(--color-border)] transition-all text-start group"
                            >
                              <div className="w-8 h-8 rounded-full bg-[var(--color-surface-elevated)] flex items-center justify-center flex-shrink-0">
                                <MessageSquare className="w-3.5 h-3.5 text-[var(--color-text-secondary)]" />
                              </div>
                              <div className="flex-1 min-w-0">
                                <div className="flex items-center gap-2">
                                  <p className="text-[13px] font-medium text-[var(--color-text-primary)] truncate" dir="auto">{s.preview || 'Conversation'}</p>
                                  {tag && <span className={`flex-shrink-0 text-[9px] font-bold px-1.5 py-0.5 rounded-full ${tag.color}`}>{tag.label}</span>}
                                </div>
                                <div className="flex items-center gap-2 mt-0.5">
                                  <span className="text-[11px] text-[var(--color-text-secondary)]">{s.message_count} {conversationLanguage === 'ar' ? 'رسالة' : 'messages'}</span>
                                  {timeAgo && <span className="text-[10px] text-[var(--color-text-muted)]">· {timeAgo}</span>}
                                </div>
                              </div>
                              <ChevronRight className="w-4 h-4 text-[var(--color-text-muted)] group-hover:text-[var(--color-text-secondary)] flex-shrink-0 transition-colors" />
                            </button>
                          );
                        })}
                      </div>
                    </div>
                  )}
                </div>
              )}

              {/* ── Messages ── */}
              {hasStarted && (
                <div className="px-2.5 sm:px-4 pt-4 sm:pt-6 pb-28 sm:pb-10" role="log" aria-live="polite" aria-label={conversationLanguage === 'ar' ? 'رسائل المحادثة' : 'Chat messages'}>
                  <motion.div
                    initial={{ opacity: 0, y: 8 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.25 }}
                    className="mb-4 rounded-2xl border border-[var(--color-border)] bg-[var(--color-surface)]/90 p-3.5 sm:p-4"
                    dir={conversationLanguage === 'ar' ? 'rtl' : 'ltr'}
                  >
                    <div className="flex flex-wrap items-center gap-2">
                      <span className={`rounded-full px-2.5 py-1 text-[10px] font-semibold uppercase tracking-[0.14em] ${businessMode === 'consultant'
                        ? 'bg-amber-500/15 text-amber-700 dark:text-amber-300'
                        : businessMode === 'premium'
                          ? 'bg-sky-500/15 text-sky-700 dark:text-sky-300'
                          : 'bg-emerald-500/15 text-emerald-700 dark:text-emerald-300'}`}>
                        {businessModeCopy.chip}
                      </span>
                      {typeof latestAgentMessage?.quotaRemaining === 'number' && businessMode !== 'premium' && (
                        <span className="text-[11px] font-medium text-[var(--color-text-muted)]">
                          {conversationLanguage === 'ar'
                            ? `المتبقي في المسار المجاني: ${latestAgentMessage.quotaRemaining}`
                            : `Free-path remaining: ${latestAgentMessage.quotaRemaining}`}
                        </span>
                      )}
                    </div>

                    <p className="mt-2 text-[13px] font-semibold text-[var(--color-text-primary)]" dir="auto">
                      {businessModeCopy.title}
                    </p>
                    <p className="mt-1 text-[12px] leading-relaxed text-[var(--color-text-secondary)]" dir="auto">
                      {businessModeCopy.description}
                    </p>

                    {businessMode === 'consultant' && (
                      <div className="mt-3 flex flex-col gap-2 sm:flex-row">
                        <button
                          type="button"
                          onClick={() => handleSendMessage(conversationLanguage === 'ar'
                            ? 'أريد التحدث مع مستشار أول الآن'
                            : 'I want to talk to a senior consultant now')}
                          className="rounded-xl border border-[var(--color-border)] bg-[var(--color-surface-elevated)] px-4 py-2.5 text-[12px] font-medium text-[var(--color-text-primary)] transition-colors hover:border-emerald-500/40"
                        >
                          {conversationLanguage === 'ar' ? 'التحدث مع مستشار أول (مجاني)' : 'Talk to a Senior Consultant (Free)'}
                        </button>
                        <button
                          type="button"
                          onClick={() => handleSendMessage(conversationLanguage === 'ar'
                            ? 'أريد تفعيل Osool Premium للتحليلات التنبؤية'
                            : 'I want to unlock Osool Premium for predictive analysis')}
                          className="rounded-xl bg-emerald-600 px-4 py-2.5 text-[12px] font-semibold text-white transition-colors hover:bg-emerald-700"
                        >
                          {conversationLanguage === 'ar' ? 'فتح Osool Premium' : 'Unlock Osool Premium'}
                        </button>
                      </div>
                    )}
                  </motion.div>

                  {messages.map((msg, index) => (
                    <ChatMessage
                      key={msg.id}
                      msg={msg}
                      index={index}
                      isLast={index === messages.length - 1}
                      isTyping={isTyping}
                      lastAiMsgId={lastAiMsgId}
                      conversationLanguage={conversationLanguage}
                      savedPropertyIds={savedPropertyIds}
                      playbackStatus={playbackStatus}
                      onRetry={handleRetry}
                      onSpeakerClick={handleSpeakerClick}
                      onSendMessage={handleSendMessage}
                      onOpenDetails={(prop) => { setActiveContext({ property: prop }); setContextPaneOpen(true); }}
                      onSave={handleSaveProperty}
                      onValuation={handleInlineValuation}
                      onCompare={handleInlineCompare}
                      enrichSuggestion={enrichSuggestion}
                      generateSuggestions={generateSuggestions}
                    />
                  ))}

                  <OrchestratorSignalPanel
                    snapshot={neuralSnapshot}
                    language={conversationLanguage}
                    visible={signalPanelVisible}
                  />

                  {/* Thinking steps */}
                  {isTyping && (
                    <>
                      <div className="sr-only" role="status" aria-live="assertive">
                        {conversationLanguage === 'ar' ? 'أصول يحلل طلبك...' : 'Osool is analyzing your request...'}
                      </div>
                      <ThinkingSteps
                        lastUserMessage={messages.length > 0 ? messages[messages.length - 1].content : ''}
                        signalSteps={signalSteps}
                        phase={neuralPhase}
                      />
                    </>
                  )}

                  {/* Context-aware skeleton */}
                  {isTyping && (() => {
                    const lastUserMsg = [...messages].reverse().find(m => m.role === 'user');
                    if (!lastUserMsg) return null;
                    const c = lastUserMsg.content.toLowerCase();
                    if (/property|عقار|شقة|villa|فيلا|show|find|compare|unit|فرصة|شراء|apartment/.test(c))
                      return <MessageSkeleton key="skel-prop" variant="property" />;
                    if (/market|سوق|price|سعر|roi|trend|yield|growth|analytics/.test(c))
                      return <MessageSkeleton key="skel-ana" variant="analytics" />;
                    return null;
                  })()}

                  {/* Anonymous gate */}
                  {(isGated || anonGateShown) && <AnonymousChatGate language={conversationLanguage} />}

                  <div ref={messagesEndRef} />
                </div>
              )}
            </div>
          </div>

          {/* New messages cue */}
          {showNewMessagesCue && hasStarted && (
            <div className="pointer-events-none absolute inset-x-0 bottom-24 md:bottom-32 z-30 flex justify-center px-4">
              <motion.button
                initial={{ opacity: 0, y: 10 }}
                animate={{ opacity: 1, y: 0 }}
                exit={{ opacity: 0, y: 10 }}
                onClick={() => scrollToBottom('smooth')}
                className="pointer-events-auto rounded-full border border-[var(--color-border)] bg-[var(--color-surface)] px-4 py-2 text-[12px] font-medium text-[var(--color-text-primary)] transition-colors"
              >
                {conversationLanguage === 'ar' ? 'رسائل جديدة' : 'New messages'}
              </motion.button>
            </div>
          )}

          {/* Floating input (in-conversation) */}
          {hasStarted && !isGated && !anonGateShown && (
            <div className="sticky bottom-0 start-0 end-0 z-40 px-2 sm:px-6 pb-[calc(0.5rem+env(safe-area-inset-bottom))] sm:pb-6 pt-2 bg-[var(--color-background)]/88 backdrop-blur-xl pointer-events-none border-t border-[var(--color-border)]/30">
              <div className="max-w-[800px] mx-auto relative pointer-events-auto">
                <ChatInputBar
                  value={inputValue}
                  onChange={setInputValue}
                  onSend={() => handleSendMessage()}
                  disabled={isTyping}
                  language={conversationLanguage}
                  voiceStatus={voiceStatus}
                  amplitude={amplitude}
                  isListening={isListening}
                  transcriptHighlight={transcriptHighlight}
                  onVoiceToggle={handleVoiceToggle}
                  inputRef={inputRef}
                  placeholder={inputPlaceholder}
                />
                <div className="text-center mt-1.5 md:mt-3">
                  <p className="text-[10px] md:text-[11px] font-medium text-[var(--color-text-muted)]/60" dir="auto">
                    {conversationLanguage === 'ar' ? 'Osool Advisor أداة ذكاء اصطناعي. يرجى التحقق من بيانات الاستثمار المهمة بشكل مستقل.' : 'Osool Advisor is an AI agent. Please verify critical investment data independently.'}
                  </p>
                </div>
              </div>
            </div>
          )}
        </main>

        {/* ── Insights pane ── */}
        <ChatInsightsShell
          property={activeContext?.property ?? null}
          isOpen={contextPaneOpen}
          onClose={() => setContextPaneOpen(false)}
          language={conversationLanguage}
          onPrompt={handleSendMessage}
        />

        {/* ── Market sidebar ── */}
        <MarketPulseSidebar language={conversationLanguage} onPrompt={handleSendMessage} />

        {/* ── History overlay ── */}
        <AnimatePresence>
          {historyOpen && (
            <>
              <motion.div
                initial={{ opacity: 0 }}
                animate={{ opacity: 1 }}
                exit={{ opacity: 0 }}
                className="fixed inset-0 bg-black/30 backdrop-blur-sm z-50"
                onClick={() => setHistoryOpen(false)}
              />
              <motion.aside
                initial={{ x: -320, opacity: 0 }}
                animate={{ x: 0, opacity: 1 }}
                exit={{ x: -320, opacity: 0 }}
                transition={{ type: 'spring', damping: 28, stiffness: 350 }}
                className="fixed start-0 top-0 bottom-0 w-[320px] bg-[var(--color-surface)] border-e border-[var(--color-border)] z-50 flex flex-col shadow-2xl"
              >
                <div className="flex items-center justify-between px-5 py-4 border-b border-[var(--color-border)]">
                  <span className="text-[15px] font-semibold text-[var(--color-text-primary)]">
                    {conversationLanguage === 'ar' ? 'المحادثات السابقة' : 'Past Conversations'}
                  </span>
                  <button
                    onClick={() => setHistoryOpen(false)}
                    aria-label="Close"
                    className="p-1.5 hover:bg-[var(--color-surface-elevated)] rounded-lg transition-colors"
                  >
                    <X className="w-4 h-4 text-[var(--color-text-muted)]" />
                  </button>
                </div>
                <div className="flex-1 overflow-y-auto p-3 space-y-1">
                  {pastSessions.length === 0 ? (
                    <div className="text-center py-12 text-[var(--color-text-muted)]">
                      <History className="w-10 h-10 mx-auto mb-3 opacity-30" />
                      <p className="text-sm font-medium text-[var(--color-text-primary)] mb-1">{conversationLanguage === 'ar' ? 'لا توجد محادثات سابقة' : 'No past conversations'}</p>
                      <p className="text-xs text-[var(--color-text-muted)] mb-4 max-w-[200px] mx-auto">{conversationLanguage === 'ar' ? 'ابدأ أول محادثة وستظهر هنا' : 'Start your first analysis and it will appear here'}</p>
                      <button
                        onClick={() => { handleNewChat(); setHistoryOpen(false); }}
                        className="inline-flex items-center gap-1.5 px-4 py-2 text-[12px] font-semibold text-emerald-500 border border-emerald-500/30 rounded-full hover:bg-emerald-500/10 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-emerald-500/40 transition-colors"
                      >
                        <Sparkles className="w-3.5 h-3.5" />
                        {conversationLanguage === 'ar' ? 'ابدأ محادثة' : 'Start a conversation'}
                      </button>
                    </div>
                  ) : (
                    pastSessions.map(s => (
                      <button
                        key={s.session_id}
                        onClick={() => loadSession(s.session_id)}
                        className={`w-full text-start p-3 rounded-xl hover:bg-[var(--color-surface-elevated)] transition-colors group ${s.session_id === sessionIdRef.current ? 'bg-emerald-500/10 border border-emerald-500/20' : ''}`}
                      >
                        <p className="text-[13px] font-medium text-[var(--color-text-primary)] truncate" dir="auto">
                          {s.preview || 'Conversation'}
                        </p>
                        <div className="flex items-center gap-2 mt-1">
                          <span className="text-[11px] text-[var(--color-text-muted)]">
                            {s.message_count} {conversationLanguage === 'ar' ? 'رسالة' : 'messages'}
                          </span>
                          {s.last_message_at && (
                            <span className="text-[11px] text-[var(--color-text-muted)]">
                              · {new Date(s.last_message_at).toLocaleDateString()}
                            </span>
                          )}
                        </div>
                      </button>
                    ))
                  )}
                </div>
                <div className="p-3 border-t border-[var(--color-border)]">
                  <button
                    onClick={() => { handleNewChat(); setHistoryOpen(false); }}
                    className="w-full py-2.5 bg-[var(--color-text-primary)] text-[var(--color-background)] rounded-xl text-[13px] font-semibold hover:opacity-90 transition-all flex items-center justify-center gap-2"
                  >
                    <Plus className="w-4 h-4" />
                    {conversationLanguage === 'ar' ? 'محادثة جديدة' : 'New Conversation'}
                  </button>
                </div>
              </motion.aside>
            </>
          )}
        </AnimatePresence>
      </div>
    </LayoutGroup>
  );
}
