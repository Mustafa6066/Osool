import { NextRequest, NextResponse } from 'next/server';

const API_URL = (process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000').replace(/\/$/, '');
const DEFAULT_APP_ORIGIN = process.env.NEXT_PUBLIC_APP_URL || 'https://osool-ten.vercel.app';
const LOCAL_BACKEND_ORIGIN = process.env.NEXT_PUBLIC_LOCAL_APP_ORIGIN || 'http://localhost:3000';

function isLocalHost(hostname: string): boolean {
  return hostname === 'localhost' || hostname === '127.0.0.1';
}

function isLocalApiTarget(): boolean {
  try {
    return isLocalHost(new URL(API_URL).hostname);
  } catch {
    return false;
  }
}

function getBackendSafeOrigin(request: NextRequest): string {
  const origin = request.headers.get('origin') || DEFAULT_APP_ORIGIN;

  try {
    const url = new URL(origin);
    if (isLocalHost(url.hostname)) {
      return isLocalApiTarget() ? LOCAL_BACKEND_ORIGIN : DEFAULT_APP_ORIGIN;
    }
  } catch {
    return DEFAULT_APP_ORIGIN;
  }

  return origin;
}

function extractCookieValue(setCookieHeader: string, key: string): string | null {
  const pattern = new RegExp(`${key}=([^;]+)`);
  const match = setCookieHeader.match(pattern);
  return match?.[1] ?? null;
}

function extractCookiePairs(setCookieHeader: string): string {
  if (!setCookieHeader) return '';

  // Split combined Set-Cookie header while preserving cookie attributes.
  const cookies = setCookieHeader
    .split(/,(?=\s*[^;,\s]+=)/)
    .map((chunk) => chunk.trim())
    .map((cookie) => cookie.split(';')[0])
    .filter(Boolean);

  return cookies.join('; ');
}

/**
 * Same-origin stream proxy:
 * - Bootstraps backend CSRF cookie + token
 * - Forwards chat stream request server-side
 * - Avoids browser-side CSRF/CORS issues
 */
export async function POST(request: NextRequest) {
  try {
    const body = await request.text();
    const origin = getBackendSafeOrigin(request);
    const referer = `${origin}/`;

    const bootstrap = await fetch(`${API_URL}/api/seo/projects`, {
      method: 'GET',
      headers: {
        Origin: origin,
        Referer: referer,
      },
      cache: 'no-store',
    });

    const csrfHeaderToken = bootstrap.headers.get('x-csrf-token') || '';
    const setCookie = bootstrap.headers.get('set-cookie') || '';
    const cookieHeader = extractCookiePairs(setCookie);
    const csrfCookie = extractCookieValue(setCookie, 'csrf_token');
    const csrfToken = csrfHeaderToken || csrfCookie || '';

    const authHeader = request.headers.get('authorization');
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      Origin: origin,
      Referer: referer,
    };

    if (csrfToken) {
      headers['X-CSRF-Token'] = csrfToken;
    }
    if (cookieHeader) {
      headers['Cookie'] = cookieHeader;
    }
    if (authHeader) {
      headers['Authorization'] = authHeader;
    }

    const upstream = await fetch(`${API_URL}/api/chat/stream`, {
      method: 'POST',
      headers,
      body,
      cache: 'no-store',
    });

    const responseHeaders = new Headers();
    responseHeaders.set('Content-Type', upstream.headers.get('content-type') || 'text/event-stream; charset=utf-8');
    responseHeaders.set('Cache-Control', 'no-cache, no-transform');

    return new NextResponse(upstream.body, {
      status: upstream.status,
      headers: responseHeaders,
    });
  } catch (error) {
    console.error('Chat stream proxy error:', error);
    return NextResponse.json(
      { detail: 'Chat stream proxy unavailable' },
      { status: 503 }
    );
  }
}
