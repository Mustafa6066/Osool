import { create } from 'zustand';
import { streamChat, type StreamChatCallbacks } from '@/lib/api';

// ─── Types ───────────────────────────────────────────────
export type UIAction = {
  type: string;
  priority: number;
  data: Record<string, unknown>;
  trigger_reason?: string;
  chart_reference?: string;
};

export type Property = {
  id: number;
  title: string;
  price: number;
  location: string;
  size_sqm: number;
  bedrooms: number;
  wolf_score?: number;
  developer?: string;
  [key: string]: unknown;
};

export type Message = {
  id: string;
  role: 'user' | 'coinvestor';
  content: string;
  visualizations?: UIAction[];
  properties?: Property[];
  timestamp: Date;
  copied?: boolean;
  isError?: boolean;
  isStreaming?: boolean;
  feedback?: 'up' | 'down' | null;
};

type StreamStatus = 'idle' | 'connecting' | 'streaming' | 'tool-running' | 'done' | 'error';

interface ChatState {
  // ─── Core State ───
  messages: Message[];
  sessionId: string;
  streamStatus: StreamStatus;
  streamingMessageId: string | null;
  activeTool: string | null;
  detectedRTL: boolean;
  suggestions: string[];
  abortController: AbortController | null;

  // ─── Actions ───
  addUserMessage: (content: string) => void;
  sendMessage: (content: string, language: 'ar' | 'en' | 'auto') => Promise<void>;
  stopGeneration: () => void;
  clearMessages: () => void;
  setSessionId: (id: string) => void;
  copyMessage: (messageId: string) => void;
  setFeedback: (messageId: string, type: 'up' | 'down') => void;
  removeMessage: (messageId: string) => void;
  setDetectedRTL: (rtl: boolean) => void;
}

function generateId(prefix: string): string {
  return `${prefix}-${Date.now()}-${Math.random().toString(36).slice(2, 7)}`;
}

function generateSessionId(): string {
  if (typeof window !== 'undefined') {
    const existing = sessionStorage.getItem('osool_chat_session');
    if (existing) return existing;
    const id = `session_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`;
    sessionStorage.setItem('osool_chat_session', id);
    return id;
  }
  return `session_${Date.now()}`;
}

export const useChatStore = create<ChatState>((set, get) => ({
  // ─── Initial State ───
  messages: [],
  sessionId: generateSessionId(),
  streamStatus: 'idle',
  streamingMessageId: null,
  activeTool: null,
  detectedRTL: false,
  suggestions: [],
  abortController: null,

  // ─── Actions ───
  addUserMessage: (content: string) => {
    const msg: Message = {
      id: generateId('user'),
      role: 'user',
      content,
      timestamp: new Date(),
    };
    set((s) => ({ messages: [...s.messages, msg] }));
  },

  sendMessage: async (content: string, language: 'ar' | 'en' | 'auto' = 'auto') => {
    const { sessionId } = get();

    // Add user message
    const userMsg: Message = {
      id: generateId('user'),
      role: 'user',
      content,
      timestamp: new Date(),
    };

    // Create placeholder AI message for streaming
    const aiMsgId = generateId('coinvestor');
    const aiMsg: Message = {
      id: aiMsgId,
      role: 'coinvestor',
      content: '',
      timestamp: new Date(),
      isStreaming: true,
    };

    set((s) => ({
      messages: [...s.messages, userMsg, aiMsg],
      streamStatus: 'connecting',
      streamingMessageId: aiMsgId,
      activeTool: null,
      suggestions: [],
    }));

    const callbacks: StreamChatCallbacks = {
      onToken: (token: string) => {
        set((s) => ({
          streamStatus: 'streaming',
          messages: s.messages.map((m) =>
            m.id === aiMsgId ? { ...m, content: m.content + token } : m
          ),
        }));
      },

      onToolStart: (tool: string) => {
        set({ streamStatus: 'tool-running', activeTool: tool });
      },

      onToolEnd: (_tool: string) => {
        set({ streamStatus: 'streaming', activeTool: null });
      },

      onComplete: (data) => {
        set((s) => ({
          streamStatus: 'done',
          streamingMessageId: null,
          activeTool: null,
          suggestions: data.suggestions || [],
          abortController: null,
          messages: s.messages.map((m) =>
            m.id === aiMsgId
              ? {
                  ...m,
                  isStreaming: false,
                  properties: (data.properties as unknown as Property[]) || [],
                  visualizations: ((data.ui_actions || []) as unknown as Array<Partial<UIAction> & { type: string }>).map(
                    (a) => ({ priority: 0, data: {}, ...a }) as UIAction
                  ),
                }
              : m
          ),
        }));

        // Detect RTL from response language
        if (data.detected_language === 'ar') {
          set({ detectedRTL: true });
        }
      },

      onFollowUp: (followUp) => {
        if (followUp && typeof followUp === 'object' && 'text' in followUp) {
          set((s) => ({
            suggestions: [...s.suggestions, String(followUp.text)],
          }));
        }
      },

      onError: (error: string) => {
        set((s) => ({
          streamStatus: 'error',
          streamingMessageId: null,
          activeTool: null,
          abortController: null,
          messages: s.messages.map((m) =>
            m.id === aiMsgId
              ? { ...m, content: error, isStreaming: false, isError: true }
              : m
          ),
        }));
      },

      onStatus: (message: string) => {
        set((s) => ({
          messages: s.messages.map((m) =>
            m.id === aiMsgId && m.isStreaming
              ? { ...m, content: m.content || message }
              : m
          ),
        }));
      },

      onCorrection: (correctedText: string) => {
        // Update the last user message with the corrected text
        set((s) => {
          const msgs = [...s.messages];
          for (let i = msgs.length - 1; i >= 0; i--) {
            if (msgs[i].role === 'user') {
              msgs[i] = { ...msgs[i], content: correctedText };
              break;
            }
          }
          return { messages: msgs };
        });
      },
    };

    try {
      const controller = await streamChat(content, sessionId, callbacks, language);
      set({ abortController: controller });
    } catch {
      // streamChat handles its own errors via callbacks.onError
    } finally {
      // Reset status if still connecting (edge case)
      const { streamStatus } = get();
      if (streamStatus === 'connecting') {
        set({ streamStatus: 'idle', streamingMessageId: null, abortController: null });
      }
    }
  },

  stopGeneration: () => {
    const { abortController, streamingMessageId } = get();
    abortController?.abort();
    set((s) => ({
      streamStatus: 'idle',
      streamingMessageId: null,
      activeTool: null,
      abortController: null,
      messages: s.messages.map((m) =>
        m.id === streamingMessageId
          ? { ...m, isStreaming: false, content: m.content || (s.detectedRTL ? 'تم إيقاف التوليد.' : 'Generation stopped.') }
          : m
      ),
    }));
  },

  clearMessages: () => {
    const newId = `session_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`;
    if (typeof window !== 'undefined') {
      sessionStorage.setItem('osool_chat_session', newId);
    }
    set({
      messages: [],
      sessionId: newId,
      streamStatus: 'idle',
      streamingMessageId: null,
      activeTool: null,
      suggestions: [],
      abortController: null,
    });
  },

  setSessionId: (id: string) => set({ sessionId: id }),

  copyMessage: (messageId: string) => {
    const msg = get().messages.find((m) => m.id === messageId);
    if (msg) {
      navigator.clipboard.writeText(msg.content);
      set((s) => ({
        messages: s.messages.map((m) =>
          m.id === messageId ? { ...m, copied: true } : m
        ),
      }));
      setTimeout(() => {
        set((s) => ({
          messages: s.messages.map((m) =>
            m.id === messageId ? { ...m, copied: false } : m
          ),
        }));
      }, 2000);
    }
  },

  setFeedback: (messageId: string, type: 'up' | 'down') => {
    set((s) => ({
      messages: s.messages.map((m) =>
        m.id === messageId
          ? { ...m, feedback: m.feedback === type ? null : type }
          : m
      ),
    }));
  },

  removeMessage: (messageId: string) => {
    set((s) => ({
      messages: s.messages.filter((m) => m.id !== messageId),
    }));
  },

  setDetectedRTL: (rtl: boolean) => set({ detectedRTL: rtl }),
}));
