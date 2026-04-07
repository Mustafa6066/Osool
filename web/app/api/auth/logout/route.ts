import { NextResponse } from 'next/server';

/**
 * Clear all auth cookies on logout.
 */
export async function POST() {
  const response = NextResponse.json({ status: 'logged_out' });

  response.cookies.delete('access_token');
  response.cookies.delete('refresh_token');
  response.cookies.delete('osool_auth_active');

  return response;
}
