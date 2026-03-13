/**
 * Webhook Proxy Route
 * -------------------
 * Proxies webhook calls from the browser to the Orchestrator, adding the
 * ORCHESTRATOR_WEBHOOK_SECRET server-side so it is never exposed to the client.
 *
 * Pattern: POST /api/webhooks/page-view  →  POST {ORCHESTRATOR_URL}/webhooks/page-view
 */

import { NextRequest, NextResponse } from 'next/server';

const ORCHESTRATOR_URL = (
  process.env.NEXT_PUBLIC_ORCHESTRATOR_URL || ''
).replace(/\/$/, '');

const WEBHOOK_SECRET = process.env.ORCHESTRATOR_WEBHOOK_SECRET || '';

export async function POST(
  request: NextRequest,
  { params }: { params: { path: string[] } }
) {
  if (!ORCHESTRATOR_URL) {
    // Orchestrator not configured — silently accept so the frontend never errors
    return NextResponse.json({}, { status: 202 });
  }

  const path = params.path.join('/');
  const targetUrl = `${ORCHESTRATOR_URL}/webhooks/${path}`;

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };
  if (WEBHOOK_SECRET) {
    headers['x-webhook-secret'] = WEBHOOK_SECRET;
  }

  // Forward client IP for rate limiting on the Orchestrator side
  const forwarded = request.headers.get('x-forwarded-for');
  if (forwarded) headers['x-forwarded-for'] = forwarded;

  try {
    const body = await request.text();
    const response = await fetch(targetUrl, {
      method: 'POST',
      headers,
      body,
    });

    // Return the Orchestrator's response status (202, 400, etc.)
    const responseBody = await response.text();
    return new NextResponse(responseBody, { status: response.status });
  } catch {
    // Orchestrator unreachable — silently accept so the frontend never errors
    return NextResponse.json({}, { status: 202 });
  }
}
