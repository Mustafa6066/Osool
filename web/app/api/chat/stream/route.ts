import { NextRequest, NextResponse } from 'next/server';

const API_URL = (process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000').replace(/\/$/, '');

/**
 * Same-origin stream proxy:
 * - Bootstraps backend CSRF cookie + token
 * - Forwards chat stream request server-side
 * - Avoids browser-side CSRF/CORS issues
 */
export async function POST(request: NextRequest) {
  try {
    const body = await request.text();
    const origin = request.headers.get('origin') || 'https://osool-ten.vercel.app';
    const referer = request.headers.get('referer') || 'https://osool-ten.vercel.app/';

    const bootstrap = await fetch(`${API_URL}/api/seo/projects`, {
      method: 'GET',
      headers: {
        Origin: origin,
        Referer: referer,
      },
      cache: 'no-store',
    });

    const csrfToken = bootstrap.headers.get('x-csrf-token') || '';
    const setCookie = bootstrap.headers.get('set-cookie') || '';

    const authHeader = request.headers.get('authorization');
    const headers: Record<string, string> = {
      'Content-Type': 'application/json',
      Origin: origin,
      Referer: referer,
    };

    if (csrfToken) {
      headers['X-CSRF-Token'] = csrfToken;
    }
    if (setCookie) {
      headers['Cookie'] = setCookie;
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
