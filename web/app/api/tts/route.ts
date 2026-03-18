/**
 * Text-to-Speech Route
 * --------------------
 * Receives text + language, proxies to OpenAI TTS API,
 * returns an audio/ogg stream for direct browser playback.
 * OPENAI_API_KEY stays server-side.
 */

import { NextRequest, NextResponse } from 'next/server';
import OpenAI from 'openai';

const MAX_CHARS = 4096; // OpenAI TTS hard limit

export async function POST(request: NextRequest): Promise<NextResponse> {
  if (!process.env.OPENAI_API_KEY) {
    return NextResponse.json(
      { error: 'TTS service not configured.' },
      { status: 503 }
    );
  }

  let body: { text?: string; language?: string };
  try {
    body = await request.json();
  } catch {
    return NextResponse.json({ error: 'Invalid JSON body.' }, { status: 400 });
  }

  const { text, language } = body;

  if (!text || typeof text !== 'string' || text.trim().length === 0) {
    return NextResponse.json({ error: 'No text provided.' }, { status: 400 });
  }

  // Truncate to API limit
  const input = text.slice(0, MAX_CHARS);

  const openai = new OpenAI({ apiKey: process.env.OPENAI_API_KEY });

  try {
    const response = await openai.audio.speech.create({
      model: 'tts-1',
      voice: 'nova',
      input,
      response_format: 'opus',
    });

    // Stream the audio bytes back to the client
    const arrayBuffer = await response.arrayBuffer();

    return new NextResponse(arrayBuffer, {
      status: 200,
      headers: {
        'Content-Type': 'audio/ogg',
        'Cache-Control': 'private, max-age=3600',
      },
    });
  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : 'TTS generation failed.';
    console.error('[TTS] OpenAI error:', message);
    return NextResponse.json({ error: message }, { status: 502 });
  }
}
