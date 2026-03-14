/**
 * Secure Cookie-Based API Client
 * -------------------------------
 * Replaces localStorage JWT storage with httpOnly cookies.
 * 
 * Security Improvements:
 * - No JavaScript access to tokens (httpOnly)
 * - CSRF protection with X-CSRF-Token header
 * - Automatic cookie handling by browser
 * - SameSite=Strict protection
 * 
 * Migration from localStorage version:
 * - Tokens now stored in httpOnly cookies (backend sets them)
 * - Frontend must include credentials in requests
 * - CSRF token must be included in state-changing requests
 */

import axios, { AxiosError, InternalAxiosRequestConfig } from 'axios';

// Base URL from environment
const BASE_URL = (process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000').replace(/\/$/, '');

// Create axios instance with credentials
const api = axios.create({
  baseURL: BASE_URL,
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true, // CRITICAL: Include cookies in requests
});

/**
 * CSRF Token Management
 * ---------------------
 * Extract CSRF token from response headers and include in requests.
 */
let csrfToken: string | null = null;

function getCsrfToken(): string | null {
  return csrfToken;
}

function setCsrfToken(token: string) {
  csrfToken = token;
  // Also store in sessionStorage as backup (not security-critical, just UX)
  if (typeof window !== 'undefined') {
    sessionStorage.setItem('csrf_token', token);
  }
}

// Initialize CSRF token from sessionStorage
if (typeof window !== 'undefined') {
  const storedToken = sessionStorage.getItem('csrf_token');
  if (storedToken) {
    csrfToken = storedToken;
  }
}

/**
 * Request Interceptor: Add CSRF Token
 * ------------------------------------
 * Attaches CSRF token to all state-changing requests.
 */
api.interceptors.request.use(
  (config: InternalAxiosRequestConfig) => {
    // Add CSRF token to state-changing methods
    const methodsRequiringCsrf = ['POST', 'PUT', 'DELETE', 'PATCH'];
    
    if (config.method && methodsRequiringCsrf.includes(config.method.toUpperCase())) {
      const token = getCsrfToken();
      if (token && config.headers) {
        config.headers['X-CSRF-Token'] = token;
      }
    }
    
    return config;
  },
  (error) => {
    return Promise.reject(error);
  }
);

/**
 * Response Interceptor: Extract CSRF Token and Handle Errors
 * -----------------------------------------------------------
 * Updates CSRF token from response headers.
 * Handles 401 (unauthorized) and 403 (CSRF) errors.
 */
api.interceptors.response.use(
  (response) => {
    // Extract CSRF token from response headers
    const newCsrfToken = response.headers['x-csrf-token'];
    if (newCsrfToken) {
      setCsrfToken(newCsrfToken);
    }
    
    return response;
  },
  async (error: AxiosError) => {
    const originalRequest = error.config as InternalAxiosRequestConfig & { _retry?: boolean };
    
    // Handle 401 Unauthorized - try to refresh
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true;
      
      try {
        // Call refresh endpoint (uses refresh token cookie)
        const { data } = await axios.post(
          `${BASE_URL}/api/auth/refresh`,
          {},
          { withCredentials: true }
        );
        
        // Extract new CSRF token from refresh response
        const newCsrfToken = data.csrf_token;
        if (newCsrfToken) {
          setCsrfToken(newCsrfToken);
        }
        
        // Retry original request
        return api(originalRequest);
      } catch (refreshError) {
        // Refresh failed - redirect to login
        if (typeof window !== 'undefined') {
          window.location.href = '/login';
        }
        return Promise.reject(refreshError);
      }
    }
    
    // Handle 403 CSRF error - fetch new token
    if (error.response?.status === 403) {
      const errorData = error.response.data as any;
      
      if (errorData?.error === 'CSRF token missing or invalid' || errorData?.error === 'CSRF token mismatch') {
        // Fetch new CSRF token
        try {
          const { data } = await axios.get(`${BASE_URL}/api/auth/csrf-token`, {
            withCredentials: true
          });
          
          if (data.csrf_token) {
            setCsrfToken(data.csrf_token);
            
            // Retry original request with new token
            if (originalRequest.headers) {
              originalRequest.headers['X-CSRF-Token'] = data.csrf_token;
            }
            
            return api(originalRequest);
          }
        } catch (csrfError) {
          console.error('Failed to fetch CSRF token:', csrfError);
        }
      }
    }
    
    return Promise.reject(error);
  }
);

/**
 * Helper: Check if user is authenticated
 * ---------------------------------------
 * Since cookies are httpOnly, we can't check them directly.
 * Instead, make a lightweight API call to check session.
 */
export const isAuthenticated = async (): Promise<boolean> => {
  try {
    const response = await api.get('/api/auth/me');
    return response.status === 200;
  } catch {
    return false;
  }
};

/**
 * Helper: Get current user
 * ------------------------
 * Fetch user data from API (cookies are automatically sent).
 */
export const getCurrentUser = async (): Promise<any | null> => {
  try {
    const response = await api.get('/api/auth/me');
    return response.data;
  } catch {
    return null;
  }
};

/**
 * Helper: Login
 * -------------
 * Server will set httpOnly cookies on successful login.
 */
export const login = async (email: string, password: string): Promise<any> => {
  const formData = new URLSearchParams();
  formData.append('username', email);
  formData.append('password', password);
  
  const response = await api.post('/api/auth/login', formData, {
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
    },
  });
  
  // Extract CSRF token from response
  const csrfTokenFromHeader = response.headers['x-csrf-token'];
  if (csrfTokenFromHeader) {
    setCsrfToken(csrfTokenFromHeader);
  }
  
  return response.data;
};

/**
 * Helper: Logout
 * --------------
 * Server will clear httpOnly cookies.
 */
export const logout = async (): Promise<void> => {
  try {
    await api.post('/api/auth/logout');
  } catch (error) {
    console.error('Logout failed:', error);
  } finally {
    // Clear CSRF token
    csrfToken = null;
    if (typeof window !== 'undefined') {
      sessionStorage.removeItem('csrf_token');
      window.location.href = '/login';
    }
  }
};

/**
 * Helper: Signup
 * --------------
 */
export const signup = async (userData: {
  full_name: string;
  email: string;
  password: string;
  phone_number: string;
  national_id: string;
}): Promise<any> => {
  const response = await api.post('/api/auth/signup', userData);
  
  // Extract CSRF token
  const csrfTokenFromHeader = response.headers['x-csrf-token'];
  if (csrfTokenFromHeader) {
    setCsrfToken(csrfTokenFromHeader);
  }
  
  return response.data;
};

/**
 * Helper: Refresh access token
 * ----------------------------
 * Uses refresh token cookie to get new access token.
 */
export const refreshToken = async (): Promise<boolean> => {
  try {
    const response = await api.post('/api/auth/refresh', {});
    
    // Extract new CSRF token
    const newCsrfToken = response.headers['x-csrf-token'];
    if (newCsrfToken) {
      setCsrfToken(newCsrfToken);
    }
    
    return true;
  } catch {
    return false;
  }
};

/**
 * Initialize CSRF Token on App Load
 * ----------------------------------
 * Call this when app initializes to get CSRF token.
 */
export const initializeCsrfToken = async () => {
  try {
    const response = await api.get('/api/auth/csrf-token');
    const token = response.headers['x-csrf-token'];
    if (token) {
      setCsrfToken(token);
    }
  } catch (error) {
    console.error('Failed to initialize CSRF token:', error);
  }
};

// Auto-initialize CSRF token
if (typeof window !== 'undefined') {
  initializeCsrfToken();
}

export default api;
export { getCsrfToken };
