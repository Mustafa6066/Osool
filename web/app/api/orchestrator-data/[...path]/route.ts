/**
 * Orchestrator Data Proxy Route
 * -------------------
 * Proxies data requests from the browser to the Orchestrator, adding the
 * API_KEY server-side so it is never exposed to the client.
 *
 * Pattern: GET /api/orchestrator-data/trending  →  GET {ORCHESTRATOR_URL}/data/trending
 */

import { NextRequest, NextResponse } from 'next/server';

const ORCHESTRATOR_URL = (
  process.env.NEXT_PUBLIC_ORCHESTRATOR_URL || ''
).replace(/\/$/, '');

const API_KEY = process.env.ORCHESTRATOR_API_KEY || '';

export async function GET(
  request: NextRequest,
  { params }: { params: Promise<{ path: string[] }> }
) {
  if (!ORCHESTRATOR_URL) {
    return NextResponse.json({}, { status: 202 });
  }

  const { path: pathSegments } = await params;
  const path = pathSegments.join('/');
  const targetUrl = `${ORCHESTRATOR_URL}/data/${path}`;

  if (!API_KEY) {
    console.warn(`[OrchestratorData] ORCHESTRATOR_API_KEY not set for ${path} — data proxy is disabled.`);
    return NextResponse.json({ disabled: 'missing_orchestrator_api_key' }, { status: 202 });
  }

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };
  headers['x-api-key'] = API_KEY;

  try {
    const response = await fetch(targetUrl, {
      method: 'GET',
      headers,
      next: { revalidate: 60 }, // Cache for 60 seconds
    });

    if (response.status === 401 || response.status === 403) {
      const responseBody = await response.text();
      console.error(`[OrchestratorData] Orchestrator rejected ${path} with ${response.status}. Check ORCHESTRATOR_API_KEY parity between Vercel and Orchestrator. Response: ${responseBody}`);
      return NextResponse.json({ disabled: 'orchestrator_auth_failed' }, { status: 202 });
    }

    const responseBody = await response.text();
    return new NextResponse(responseBody, {
      status: response.status,
      headers: { 'Content-Type': 'application/json' },
    });
  } catch (err) {
    console.error(`[OrchestratorData] Orchestrator unreachable at ${targetUrl}:`, err instanceof Error ? err.message : err);
    return NextResponse.json(
      { error: 'orchestrator_unreachable', target: path },
      { status: 502 }
    );
  }
}
