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
const BASE_URL = (process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000').replace(/\/$/, '');

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
 */
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

      // Get refresh token from localStorage
      const refreshToken = typeof window !== 'undefined'
        ? localStorage.getItem('refresh_token')
        : null;

      if (!refreshToken) {
        // No refresh token available - redirect to login
        if (typeof window !== 'undefined') {
          localStorage.clear();
          window.location.href = '/login';
        }
        return Promise.reject(error);
      }

      try {
        // Call refresh endpoint to get new access token
        const { data } = await axios.post(`${BASE_URL}/auth/refresh`, {
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

        // Retry original request with new token
        if (originalRequest.headers) {
          originalRequest.headers.Authorization = `Bearer ${data.access_token}`;
        }

        return api(originalRequest);
      } catch (refreshError) {
        // Refresh failed - clear tokens and redirect to login
        if (typeof window !== 'undefined') {
          localStorage.clear();
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
    return decoded;
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
    localStorage.removeItem('access_token');
    localStorage.removeItem('refresh_token');
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
  onComplete: (data: { properties: any[]; ui_actions: any[]; psychology?: any }) => void;
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
              if (data.content) callbacks.onToken(data.content);
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

export default api;
