/**
 * Osool API Client with JWT Interceptors
 * ---------------------------------------
 * Axios-based HTTP client with automatic JWT attachment and token refresh.
 *
 * Features:
 * - Auto-attaches JWT access token to all requests
 * - Handles 401 errors with automatic token refresh
 * - Redirects to login on refresh failure
 * - TypeScript support for type safety
 */

import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios';

// Base URL from environment or default to localhost (strip trailing slash)
let BASE_URL = (process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000').replace(/\/$/, '');
// Enforce HTTPS in production to prevent mixed-content errors
if (typeof window !== 'undefined' && window.location.protocol === 'https:') {
  BASE_URL = BASE_URL.replace(/^http:/, 'https:');
}

// Create axios instance
const api = axios.create({
  baseURL: BASE_URL,
  timeout: 30000, // 30 seconds
  headers: {
    'Content-Type': 'application/json',
  },
});

/**
 * Request Interceptor: Attach JWT Access Token
 * Runs before every API request to add Authorization header
 */
api.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    // Get access token from localStorage
    const accessToken = typeof window !== 'undefined'
      ? localStorage.getItem('access_token')
      : null;

    // Attach token if available
    if (accessToken && config.headers) {
      config.headers.Authorization = `Bearer ${accessToken}`;
    }

    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

/**
 * Response Interceptor: Handle 401 and Refresh Token
 * Automatically refreshes access token on 401 Unauthorized
 * Uses a lock to prevent parallel refresh calls
 */
let isRefreshing = false;
let refreshSubscribers: ((token: string) => void)[] = [];

function onTokenRefreshed(token: string) {
  refreshSubscribers.forEach(cb => cb(token));
  refreshSubscribers = [];
}

function addRefreshSubscriber(cb: (token: string) => void) {
  refreshSubscribers.push(cb);
}

api.interceptors.response.use(
  (response) => {
    // Pass through successful responses
    return response;
  },
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean };

    // Check if error is 401 Unauthorized and we haven't retried yet
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;

      // If already refreshing, queue this request to retry after refresh
      if (isRefreshing) {
        return new Promise((resolve) => {
          addRefreshSubscriber((token: string) => {
            if (originalRequest.headers) {
              originalRequest.headers.Authorization = `Bearer ${token}`;
            }
            resolve(api(originalRequest));
          });
        });
      }

      // Get refresh token from localStorage
      const refreshToken = typeof window !== 'undefined'
        ? localStorage.getItem('refresh_token')
        : null;

      if (!refreshToken) {
        // No refresh token available - redirect to login
        if (typeof window !== 'undefined') {
          localStorage.removeItem('access_token');
          localStorage.removeItem('refresh_token');
          window.location.href = '/login';
        }
        return Promise.reject(error);
      }

      isRefreshing = true;

      try {
        // Call refresh endpoint to get new access token
        const { data } = await axios.post(`${BASE_URL}/api/auth/refresh`, {
          refresh_token: refreshToken,
        });

        // Store new access token
        if (typeof window !== 'undefined') {
          localStorage.setItem('access_token', data.access_token);

          // If new refresh token is provided, update it too
          if (data.refresh_token) {
            localStorage.setItem('refresh_token', data.refresh_token);
          }
        }

        isRefreshing = false;
        onTokenRefreshed(data.access_token);

        // Retry original request with new token
        if (originalRequest.headers) {
          originalRequest.headers.Authorization = `Bearer ${data.access_token}`;
        }

        return api(originalRequest);
      } catch (refreshError) {
        isRefreshing = false;
        refreshSubscribers = [];
        // Refresh failed - clear auth tokens only and redirect to login
        if (typeof window !== 'undefined') {
          localStorage.removeItem('access_token');
          localStorage.removeItem('refresh_token');
          window.location.href = '/login';
        }
        return Promise.reject(refreshError);
      }
    }

    // For all other errors, pass through
    return Promise.reject(error);
  }
);

/**
 * Helper: Check if user is authenticated
 */
export const isAuthenticated = (): boolean => {
  if (typeof window === 'undefined') return false;
  return !!localStorage.getItem('access_token');
};

/**
 * Helper: Get current user from JWT (decode without verification)
 * WARNING: This is NOT secure validation - backend must verify token
 */
export const getCurrentUserFromToken = (): any | null => {
  if (typeof window === 'undefined') return null;

  const token = localStorage.getItem('access_token');
  if (!token) return null;

  try {
    // Decode JWT payload (base64)
    const payload = token.split('.')[1];
    const decoded = JSON.parse(atob(payload));
    // Map JWT claims to User interface fields
    const fullName = localStorage.getItem('user_full_name');
    return {
      ...decoded,
      email: decoded.sub || decoded.email,
      full_name: fullName || decoded.full_name,
    };
  } catch (e) {
    console.error('Failed to decode JWT:', e);
    return null;
  }
};

/**
 * Helper: Logout user (clear tokens)
 */
export const logout = (): void => {
  if (typeof window !== 'undefined') {
    const refreshToken = localStorage.getItem('refresh_token');
    if (refreshToken) {
      api.post('/api/auth/logout', { refresh_token: refreshToken }).catch(() => undefined);
    }
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
    localStorage.removeItem('user_full_name');
    window.location.href = '/login';
  }
};

/**
 * Helper: Store authentication tokens
 */
export const storeAuthTokens = (accessToken: string, refreshToken?: string): void => {
  if (typeof window === 'undefined') return;

  localStorage.setItem('access_token', accessToken);

  if (refreshToken) {
    localStorage.setItem('refresh_token', refreshToken);
  }
};

/**
 * V6: Streaming Chat Response Types
 */
export type StreamEventType = 'token' | 'tool_start' | 'tool_end' | 'done' | 'follow_up' | 'error';

export interface StreamEvent {
  type: StreamEventType;
  content?: string | Record<string, any>;
  tool?: string;
  properties?: any[];
  ui_actions?: any[];
  psychology?: any;
  message?: string;
}

export interface StreamChatCallbacks {
  onToken: (token: string) => void;
  onToolStart: (tool: string) => void;
  onToolEnd: (tool: string) => void;
  onComplete: (data: {
    properties: any[];
    ui_actions: any[];
    psychology?: any;
    suggestions?: string[];
    lead_score?: number;
    readiness_score?: number;
    detected_language?: string;
    showing_strategy?: string;
  }) => void;
  onFollowUp?: (followUp: any) => void;
  onError: (error: string) => void;
}

/**
 * V6: Streaming Chat Function
 * Connects to /api/chat/stream endpoint via Server-Sent Events
 *
 * @param message - User message to send
 * @param sessionId - Chat session ID
 * @param callbacks - Event callbacks for streaming updates
 * @param language - User's preferred language ('ar', 'en', or 'auto')
 * @returns AbortController to cancel the stream
 */
export const streamChat = async (
  message: string,
  sessionId: string,
  callbacks: StreamChatCallbacks,
  language: 'ar' | 'en' | 'auto' = 'auto'
): Promise<AbortController> => {
  const controller = new AbortController();

  // Auto-timeout after 2 minutes to prevent hung connections
  const timeoutId = setTimeout(() => controller.abort(), 120000);

  try {
    const accessToken = typeof window !== 'undefined'
      ? localStorage.getItem('access_token')
      : null;

    const response = await fetch(`${BASE_URL}/api/chat/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(accessToken ? { 'Authorization': `Bearer ${accessToken}` } : {}),
      },
      body: JSON.stringify({ message, session_id: sessionId, language }),
      signal: controller.signal,
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const reader = response.body?.getReader();
    const decoder = new TextDecoder();

    if (!reader) {
      throw new Error('Response body is not readable');
    }

    // Read stream
    let buffer = '';

    const processLine = (line: string) => {
      if (line.startsWith('data: ')) {
        try {
          const data: StreamEvent = JSON.parse(line.slice(6));

          switch (data.type) {
            case 'token':
              if (data.content) callbacks.onToken(typeof data.content === 'string' ? data.content : JSON.stringify(data.content));
              break;
            case 'tool_start':
              if (data.tool) callbacks.onToolStart(data.tool);
              break;
            case 'tool_end':
              if (data.tool) callbacks.onToolEnd(data.tool);
              break;
            case 'done':
              callbacks.onComplete({
                properties: data.properties || [],
                ui_actions: data.ui_actions || [],
                psychology: data.psychology,
                suggestions: (data as any).suggestions || [],
                lead_score: (data as any).lead_score || 0,
                readiness_score: (data as any).readiness_score || 0,
                detected_language: (data as any).detected_language || 'ar',
                showing_strategy: (data as any).showing_strategy || 'NONE',
              });
              break;
            case 'follow_up':
              if (callbacks.onFollowUp && data.content) {
                callbacks.onFollowUp(data.content);
              }
              break;
            case 'error':
              callbacks.onError(data.message || 'Unknown error');
              break;
          }
        } catch (e) {
          console.error('Failed to parse SSE data:', e);
        }
      }
    };

    // Process stream
    while (true) {
      const { done, value } = await reader.read();

      if (done) break;

      buffer += decoder.decode(value, { stream: true });

      // Process complete lines
      const lines = buffer.split('\n');
      buffer = lines.pop() || ''; // Keep incomplete line in buffer

      for (const line of lines) {
        if (line.trim()) {
          processLine(line);
        }
      }
    }

    // Process any remaining buffer
    if (buffer.trim()) {
      processLine(buffer);
    }

  } catch (error) {
    if ((error as Error).name === 'AbortError') {
      console.log('Stream cancelled by user');
    } else {
      callbacks.onError((error as Error).message);
    }
  } finally {
    clearTimeout(timeoutId);
  }

  return controller;
};

/**
 * V6: Simple non-streaming chat (wrapper for backwards compatibility)
 *
 * @param message - User message to send
 * @param sessionId - Chat session ID
 * @param language - User's preferred language ('ar', 'en', or 'auto')
 */
export const sendChatMessage = async (
  message: string,
  sessionId: string = 'default',
  language: 'ar' | 'en' | 'auto' = 'auto'
): Promise<{
  response: string;
  properties: any[];
  ui_actions: any[];
  psychology?: any;
}> => {
  const { data } = await api.post('/api/chat', { message, session_id: sessionId, language });
  return data;
};

export interface ChatSession {
  session_id: string;
  message_count: number;
  started_at: string | null;
  last_message_at: string | null;
  preview: string | null;
}

/** Get current user's chat sessions */
export const getUserChatSessions = async (): Promise<ChatSession[]> => {
  const { data } = await api.get('/api/chat/history');
  return data.sessions ?? [];
};

/** Delete a chat session owned by the current user */
export const deleteChatSession = async (sessionId: string): Promise<void> => {
  await api.delete(`/api/chat/history/${sessionId}`);
};

// ═══════════════════════════════════════════════════════════════
// INVITATION SYSTEM API
// ═══════════════════════════════════════════════════════════════

export interface InvitationResponse {
  status: string;
  invitation_code: string;
  invitation_link: string;
  invitations_remaining: number | 'unlimited';
}

export interface MyInvitationsResponse {
  total_invitations: number;
  invitations_remaining: number | 'unlimited';
  invitations: Array<{
    code: string;
    is_used: boolean;
    created_at: string | null;
    used_at: string | null;
  }>;
}

export interface InvitationValidation {
  valid: boolean;
  message: string;
  invited_by?: string;
}

/**
 * Generate a new invitation link
 * Admins can generate unlimited, regular users limited to 2
 */
export const generateInvitation = async (): Promise<InvitationResponse> => {
  const { data } = await api.post('/api/auth/invitation/generate', {});
  return data;
};

/**
 * Get all invitations created by the current user
 */
export const getMyInvitations = async (): Promise<MyInvitationsResponse> => {
  const { data } = await api.get('/api/auth/invitation/my-invitations');
  return data;
};

/**
 * Validate an invitation code (check if it's valid and unused)
 */
export const validateInvitation = async (code: string): Promise<InvitationValidation> => {
  const { data } = await api.get(`/api/auth/invitation/validate/${code}`);
  return data;
};

// ═══════════════════════════════════════════════════════════════
// ADMIN API
// ═══════════════════════════════════════════════════════════════

export interface AdminDashboardData {
  overview: {
    total_users: number;
    total_messages: number;
    total_properties: number;
    active_properties: number;
    total_transactions: number;
    total_sessions: number;
  };
  recent_activity: {
    new_users_7d: number;
    messages_24h: number;
  };
  admin: { email: string; name: string };
}

export interface AdminUser {
  id: number;
  email: string;
  full_name: string;
  role: string;
  created_at: string | null;
  is_verified: boolean;
  kyc_status: string;
  message_count: number;
  last_activity: string | null;
}

export interface AdminConversation {
  session_id: string;
  user_id: number;
  user_email: string;
  user_name: string;
  message_count: number;
  started_at: string | null;
  last_message_at: string | null;
  preview: string | null;
}

export interface AdminMessage {
  id: number;
  role: string;
  content: string;
  created_at: string | null;
  properties: any[] | null;
}

/** Check if current user is admin */
export const checkAdmin = async (): Promise<{ is_admin: boolean; email: string; name: string }> => {
  const { data } = await api.get('/api/admin/check');
  return data;
};

/** Get admin dashboard overview */
export const getAdminDashboard = async (): Promise<AdminDashboardData> => {
  const { data } = await api.get('/api/admin/dashboard');
  return data;
};

/** Get all users (admin) */
export const getAdminUsers = async (limit = 100, offset = 0): Promise<{ total: number; users: AdminUser[] }> => {
  const { data } = await api.get(`/api/admin/users?limit=${limit}&offset=${offset}`);
  return data;
};

/** Get all conversations (admin) */
export const getAdminConversations = async (limit = 50, offset = 0): Promise<{ total: number; sessions: AdminConversation[] }> => {
  const { data } = await api.get(`/api/admin/conversations?limit=${limit}&offset=${offset}`);
  return data;
};

/** Get full conversation thread (admin) */
export const getAdminConversation = async (sessionId: string): Promise<{
  session_id: string;
  user: { id: number; email: string; full_name: string; role: string } | null;
  message_count: number;
  messages: AdminMessage[];
}> => {
  const { data } = await api.get(`/api/admin/conversations/${sessionId}`);
  return data;
};

/** Update a user's role (Mustafa only) */
export const updateUserRole = async (userId: number, role: string): Promise<{ id: number; email: string; role: string }> => {
  const { data } = await api.patch(`/api/admin/users/${userId}/role`, { role });
  return data;
};

/** Block or unblock a user account (Mustafa only) */
export const blockUser = async (userId: number, blocked: boolean): Promise<{ id: number; email: string; blocked: boolean }> => {
  const { data } = await api.patch(`/api/admin/users/${userId}/block`, { blocked });
  return data;
};

/** Get all conversations for a specific user (admin) */
export const getAdminUserConversations = async (userId: number) => {
  const { data } = await api.get(`/api/admin/conversations/user/${userId}`);
  return data;
};

/** Trigger property scraper (admin) */
export const triggerPropertyScraper = async () => {
  const { data } = await api.post('/api/admin/scraper/properties');
  return data;
};

/** Trigger economic scraper (admin) */
export const triggerEconomicScraper = async () => {
  const { data } = await api.post('/api/admin/scraper/economic');
  return data;
};

/** Get market indicators (admin) */
export const getAdminMarketIndicators = async () => {
  const { data } = await api.get('/api/admin/market-indicators');
  return data;
};


// ═══════════════════════════════════════════════════════════════
// TICKET SYSTEM API
// ═══════════════════════════════════════════════════════════════

export interface Ticket {
  id: number;
  subject: string;
  category: string;
  priority: string;
  status: string;
  replies_count: number;
  created_at: string | null;
  updated_at: string | null;
}

export interface TicketReply {
  id: number;
  content: string;
  user_name: string;
  is_admin_reply: boolean;
  created_at: string | null;
}

export interface TicketDetail {
  id: number;
  subject: string;
  description: string;
  category: string;
  priority: string;
  status: string;
  created_at: string | null;
  updated_at: string | null;
  closed_at: string | null;
  replies: TicketReply[];
}

export interface AdminTicket {
  id: number;
  subject: string;
  category: string;
  priority: string;
  status: string;
  user_name: string;
  user_email: string;
  assigned_to_name: string | null;
  replies_count: number;
  created_at: string | null;
  updated_at: string | null;
}

export interface AdminTicketDetail extends TicketDetail {
  user: { name: string; email: string };
  assigned_to_name: string | null;
}

export interface TicketStats {
  open: number;
  in_progress: number;
  resolved: number;
  closed: number;
  total: number;
}

// --- User Ticket Functions ---

/** Create a new support ticket */
export const createTicket = async (data: {
  subject: string;
  description: string;
  category?: string;
  priority?: string;
}): Promise<TicketDetail> => {
  const { data: res } = await api.post('/api/tickets', data);
  return res;
};

/** Get current user's tickets */
export const getMyTickets = async (
  status?: string,
  limit = 20,
  offset = 0
): Promise<{ total: number; tickets: Ticket[] }> => {
  const params = new URLSearchParams();
  if (status) params.append('status', status);
  params.append('limit', String(limit));
  params.append('offset', String(offset));
  const { data } = await api.get(`/api/tickets?${params.toString()}`);
  return data;
};

/** Get ticket detail with replies */
export const getTicketDetail = async (id: number): Promise<TicketDetail> => {
  const { data } = await api.get(`/api/tickets/${id}`);
  return data;
};

/** Add a reply to own ticket */
export const addTicketReply = async (ticketId: number, content: string): Promise<TicketReply> => {
  const { data } = await api.post(`/api/tickets/${ticketId}/replies`, { content });
  return data;
};

// --- Admin Ticket Functions ---

/** Admin: get ticket statistics */
export const getTicketStats = async (): Promise<TicketStats> => {
  const { data } = await api.get('/api/admin/tickets/stats');
  return data;
};

/** Admin: list all tickets */
export const getAdminTickets = async (
  filters: { status?: string; priority?: string; category?: string; search?: string; limit?: number; offset?: number } = {}
): Promise<{ total: number; tickets: AdminTicket[] }> => {
  const params = new URLSearchParams();
  if (filters.status) params.append('status', filters.status);
  if (filters.priority) params.append('priority', filters.priority);
  if (filters.category) params.append('category', filters.category);
  if (filters.search) params.append('search', filters.search);
  params.append('limit', String(filters.limit || 50));
  params.append('offset', String(filters.offset || 0));
  const { data } = await api.get(`/api/admin/tickets?${params.toString()}`);
  return data;
};

/** Admin: get full ticket detail */
export const getAdminTicketDetail = async (id: number): Promise<AdminTicketDetail> => {
  const { data } = await api.get(`/api/admin/tickets/${id}`);
  return data;
};

/** Admin: update ticket status */
export const updateTicketStatus = async (id: number, status: string): Promise<{ id: number; status: string }> => {
  const { data } = await api.patch(`/api/admin/tickets/${id}/status`, { status });
  return data;
};

/** Admin: assign ticket to admin */
export const assignTicket = async (id: number, adminId: number | null): Promise<{ id: number; assigned_to: number | null }> => {
  const { data } = await api.patch(`/api/admin/tickets/${id}/assign`, { admin_id: adminId });
  return data;
};

/** Admin: reply to ticket as admin */
export const addAdminTicketReply = async (ticketId: number, content: string): Promise<TicketReply> => {
  const { data } = await api.post(`/api/admin/tickets/${ticketId}/replies`, { content });
  return data;
};

export default api;
