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
  { params }: { params: Promise<{ path: string[] }> }
) {
  if (!ORCHESTRATOR_URL) {
    // Orchestrator not configured — silently accept so the frontend never errors
    console.warn('⚠️ NEXT_PUBLIC_ORCHESTRATOR_URL not set — webhooks are disabled. Set this env var to enable orchestrator integration.');
    return NextResponse.json({}, { status: 202 });
  }

  const { path: pathSegments } = await params;
  const path = pathSegments.join('/');
  const targetUrl = `${ORCHESTRATOR_URL}/webhooks/${path}`;

  if (!WEBHOOK_SECRET) {
    console.warn(`[Webhook] ORCHESTRATOR_WEBHOOK_SECRET not set for ${path} — webhook forwarding is disabled.`);
    return NextResponse.json({ accepted: false, disabled: 'missing_webhook_secret' }, { status: 202 });
  }

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };
  headers['x-webhook-secret'] = WEBHOOK_SECRET;

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

    if (response.status === 401 || response.status === 403) {
      const responseBody = await response.text();
      console.error(`[Webhook] Orchestrator rejected ${path} with ${response.status}. Check ORCHESTRATOR_WEBHOOK_SECRET parity between Vercel and Orchestrator. Response: ${responseBody}`);
      return NextResponse.json({ accepted: false, disabled: 'webhook_auth_failed' }, { status: 202 });
    }

    // Return the Orchestrator's response status (202, 400, etc.)
    const responseBody = await response.text();
    return new NextResponse(responseBody, { status: response.status });
  } catch (err) {
    // Orchestrator unreachable — log for monitoring, but don't fail the client
    console.error(`[Webhook] Orchestrator unreachable at ${targetUrl}:`, err instanceof Error ? err.message : err);
    return NextResponse.json(
      { error: 'orchestrator_unreachable', target: path },
      { status: 502 }
    );
  }
}
