import { NextRequest, NextResponse } from 'next/server';

const API_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

/**
 * Proxy token refresh to backend and update httpOnly cookies.
 */
export async function POST(request: NextRequest) {
  try {
    // Try httpOnly cookie first, then fallback to body
    const refreshToken =
      request.cookies.get('refresh_token')?.value ||
      (await request.json().catch(() => ({}))).refresh_token;

    if (!refreshToken) {
      return NextResponse.json(
        { error: 'No refresh token' },
        { status: 401 }
      );
    }

    const backendRes = await fetch(`${API_URL}/api/auth/refresh`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ refresh_token: refreshToken }),
    });

    const data = await backendRes.json();

    if (!backendRes.ok) {
      // Clear cookies on refresh failure
      const response = NextResponse.json(data, { status: backendRes.status });
      response.cookies.delete('access_token');
      response.cookies.delete('refresh_token');
      response.cookies.delete('osool_auth_active');
      return response;
    }

    const { access_token, refresh_token: newRefreshToken } = data;

    const response = NextResponse.json(data);

    const isProduction = process.env.NODE_ENV === 'production';
    const cookieOptions = {
      httpOnly: true,
      secure: isProduction,
      sameSite: 'lax' as const,
      path: '/',
    };

    response.cookies.set('access_token', access_token, {
      ...cookieOptions,
      maxAge: 30 * 60,
    });

    if (newRefreshToken) {
      response.cookies.set('refresh_token', newRefreshToken, {
        ...cookieOptions,
        maxAge: 30 * 24 * 60 * 60,
      });
    }

    return response;
  } catch (error) {
    console.error('Token refresh proxy error:', error);
    return NextResponse.json(
      { error: 'Refresh service unavailable' },
      { status: 503 }
    );
  }
}
