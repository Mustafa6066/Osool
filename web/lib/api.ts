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

// Base URL from environment or default to localhost
const BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

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

export default api;
