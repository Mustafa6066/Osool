/**
 * Orchestrator Data Proxy Route
 * -------------------
 * Proxies GET/PATCH calls from the browser to the Orchestrator data API,
 * adding the OSOOL_API_KEY server-side so it is never exposed to the client.
 *
 * Pattern: GET /api/orchestrator/notifications/123  →  GET {ORCHESTRATOR_URL}/data/notifications/123
 */

import { NextRequest, NextResponse } from 'next/server';

const ORCHESTRATOR_URL = (
  process.env.NEXT_PUBLIC_ORCHESTRATOR_URL || ''
).replace(/\/$/, '');

const API_KEY = process.env.ORCHESTRATOR_API_KEY || '';

async function handler(
  request: NextRequest,
  { params }: { params: Promise<{ path: string[] }> }
) {
  if (!ORCHESTRATOR_URL) {
    return NextResponse.json({}, { status: 202 });
  }

  const { path: pathSegments } = await params;
  const path = pathSegments.join('/');
  const targetUrl = `${ORCHESTRATOR_URL}/data/${path}`;

  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  };
  if (API_KEY) {
    headers['x-api-key'] = API_KEY;
  }

  try {
    const fetchOpts: RequestInit = {
      method: request.method,
      headers,
    };
    if (request.method === 'PATCH' || request.method === 'POST') {
      fetchOpts.body = await request.text();
    }

    const response = await fetch(targetUrl, fetchOpts);
    const data = await response.text();

    return new NextResponse(data, {
      status: response.status,
      headers: { 'Content-Type': 'application/json' },
    });
  } catch {
    return NextResponse.json({ error: 'Orchestrator unreachable' }, { status: 502 });
  }
}

export const GET = handler;
export const PATCH = handler;
