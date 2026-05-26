import { NextResponse } from 'next/server';
import type { NextRequest } from 'next/server';

/**
 * Next.js Edge Middleware — runs before every matched route.
 *
 * Responsibilities:
 *  1. Server-side auth gating for protected routes (redirect to /login)
 *  2. Security headers that apply to all responses
 *  3. Rate-limit header forwarding from backend
 */

// Routes that require authentication (redirect to /login if no token)
const PROTECTED_ROUTES = [
  '/dashboard',
  '/favorites',
  '/settings',
  '/admin',
];

// Routes that authenticated users should NOT see (redirect to /dashboard)
const AUTH_ROUTES = ['/login', '/signup'];

export function proxy(request: NextRequest) {
  const { pathname } = request.nextUrl;

  // Check for auth token in cookies (preferred) or fallback to localStorage indicator
  const accessToken = request.cookies.get('access_token')?.value;
  // Also check for the legacy localStorage-based auth via a thin cookie set by the client
  const hasLegacyAuth = request.cookies.get('osool_auth_active')?.value === '1';
  const isAuthenticated = !!accessToken || hasLegacyAuth;

  // 1. Protect authenticated routes
  const isProtectedRoute = PROTECTED_ROUTES.some(
    (route) => pathname === route || pathname.startsWith(route + '/')
  );

  if (isProtectedRoute && !isAuthenticated) {
    const loginUrl = new URL('/login', request.url);
    loginUrl.searchParams.set('redirect', pathname);
    return NextResponse.redirect(loginUrl);
  }

  // 2. Redirect logged-in users away from auth pages
  if (AUTH_ROUTES.includes(pathname) && isAuthenticated) {
    return NextResponse.redirect(new URL('/dashboard', request.url));
  }

  // 3. Add security headers to all responses
  const response = NextResponse.next();

  // Prevent clickjacking
  response.headers.set('X-Frame-Options', 'DENY');
  // Prevent MIME type sniffing
  response.headers.set('X-Content-Type-Options', 'nosniff');
  // Control referrer information
  response.headers.set('Referrer-Policy', 'strict-origin-when-cross-origin');

  return response;
}

export const config = {
  // Match all routes except static files, images, and API routes
  matcher: [
    '/((?!_next/static|_next/image|favicon.ico|api/|.*\\.(?:svg|png|jpg|jpeg|gif|webp|ico|css|js)$).*)',
  ],
};
