/**
 * Whisper Transcription Route
 * ----------------------------
 * Receives an audio file from the browser via FormData,
 * proxies it to OpenAI Whisper, and returns the transcript.
 * Keeps OPENAI_API_KEY server-side, never exposed to the client.
 */

import { NextRequest, NextResponse } from 'next/server';
import OpenAI, { toFile } from 'openai';

const MAX_BYTES = 25 * 1024 * 1024; // Whisper hard limit: 25 MB

export async function POST(request: NextRequest): Promise<NextResponse> {
  if (!process.env.OPENAI_API_KEY) {
    console.warn('[Transcribe] OPENAI_API_KEY is not configured.');
    return NextResponse.json(
      { error: 'Transcription service not configured.' },
      { status: 503 }
    );
  }

  let formData: FormData;
  try {
    formData = await request.formData();
  } catch {
    return NextResponse.json({ error: 'Invalid request body.' }, { status: 400 });
  }

  const audioFile = formData.get('audio') as File | null;
  const language = (formData.get('language') as string | null) ?? '';

  if (!audioFile || audioFile.size === 0) {
    return NextResponse.json({ error: 'No audio file provided.' }, { status: 400 });
  }

  if (audioFile.size > MAX_BYTES) {
    return NextResponse.json(
      { error: 'Audio file too large (max 25 MB).' },
      { status: 413 }
    );
  }

  const buffer = Buffer.from(await audioFile.arrayBuffer());
  const ext = audioFile.name.split('.').pop() ?? 'webm';

  const openai = new OpenAI({ apiKey: process.env.OPENAI_API_KEY });

  try {
    const whisperFile = await toFile(buffer, `audio.${ext}`, { type: audioFile.type });

    const transcription = await openai.audio.transcriptions.create({
      file: whisperFile,
      model: 'whisper-1',
      // undefined = Whisper multilingual auto-detect (handles Franco-Arab mixed speech)
      language: language || undefined,
      response_format: 'json',
    });

    return NextResponse.json({ text: transcription.text });
  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : 'Transcription failed.';
    console.error('[Transcribe] Whisper API error:', message);
    return NextResponse.json({ error: message }, { status: 502 });
  }
}
