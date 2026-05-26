import { NextRequest, NextResponse } from 'next/server';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

/**
 * Proxy login to the backend and set httpOnly cookies.
 * Client calls POST /api/auth/login with { email, password }.
 * We forward to the backend, then set the tokens as httpOnly cookies.
 */
export async function POST(request: NextRequest) {
  try {
    const body = await request.json();
    const { email, password } = body;

    if (!email || !password) {
      return NextResponse.json(
        { error: 'Email and password required' },
        { status: 400 }
      );
    }

    // Forward to backend auth endpoint
    const backendRes = await fetch(`${API_URL}/api/auth/login`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: new URLSearchParams({ username: email, password }),
    });

    const data = await backendRes.json();

    if (!backendRes.ok) {
      return NextResponse.json(data, { status: backendRes.status });
    }

    const { access_token, refresh_token, ...rest } = data;

    const response = NextResponse.json({
      ...rest,
      access_token,  // Still returned for localStorage backward compat
      refresh_token,
    });

    // Set httpOnly cookies (secure in production)
    const isProduction = process.env.NODE_ENV === 'production';
    const cookieOptions = {
      httpOnly: true,
      secure: isProduction,
      sameSite: 'lax' as const,
      path: '/',
    };

    response.cookies.set('access_token', access_token, {
      ...cookieOptions,
      maxAge: 30 * 60, // 30 minutes (matches backend)
    });

    if (refresh_token) {
      response.cookies.set('refresh_token', refresh_token, {
        ...cookieOptions,
        maxAge: 30 * 24 * 60 * 60, // 30 days
      });
    }

    // Non-httpOnly cookie for middleware auth check
    response.cookies.set('osool_auth_active', '1', {
      httpOnly: false,
      secure: isProduction,
      sameSite: 'lax' as const,
      path: '/',
      maxAge: 30 * 24 * 60 * 60,
    });

    return response;
  } catch (error) {
    console.error('Auth proxy error:', error);
    return NextResponse.json(
      { error: 'Authentication service unavailable' },
      { status: 503 }
    );
  }
}
