/**
 * Text-to-Speech Route
 * --------------------
 * Egyptian real-estate context: handles mixed Egyptian Arabic + English,
 * expands RE abbreviations, picks the right voice per language,
 * and returns audio/ogg for browser playback.
 * OPENAI_API_KEY stays server-side.
 */

import { NextRequest, NextResponse } from 'next/server';
import OpenAI from 'openai';

const MAX_CHARS = 4096; // OpenAI TTS hard limit

// ---------- language-aware voice selection ----------
type Voice = 'alloy' | 'echo' | 'fable' | 'onyx' | 'nova' | 'shimmer';

function pickVoice(lang: string | undefined): Voice {
  // 'shimmer' handles Arabic pronunciation best among current OpenAI voices;
  // 'nova' is the default for English / unknown.
  if (lang && (lang.startsWith('ar') || lang === 'arabic')) return 'shimmer';
  return 'nova';
}

function pickSpeed(lang: string | undefined): number {
  // Slightly slower for Arabic to keep clarity on real-estate numbers & terms
  if (lang && (lang.startsWith('ar') || lang === 'arabic')) return 0.95;
  return 1.0;
}

// ---------- text preprocessing for Egyptian RE context ----------

/** Strip markdown formatting that sounds awkward when read aloud */
function stripMarkdown(text: string): string {
  return text
    .replace(/#{1,6}\s*/g, '')          // headings
    .replace(/\*\*([^*]+)\*\*/g, '$1')  // bold
    .replace(/\*([^*]+)\*/g, '$1')      // italic
    .replace(/`([^`]+)`/g, '$1')        // inline code
    .replace(/\[([^\]]+)\]\([^)]+\)/g, '$1') // links → text only
    .replace(/^[-*]\s+/gm, '')          // bullet markers
    .replace(/\n{3,}/g, '\n\n');         // collapse blank lines
}

/** Expand common Egyptian real-estate abbreviations so TTS reads them naturally */
function expandRealEstateTerms(text: string, lang: string | undefined): string {
  const isArabic = lang && (lang.startsWith('ar') || lang === 'arabic');

  // ---------- currency ----------
  text = text.replace(/EGP\s?([\d,.]+)/gi, (_, n) =>
    isArabic ? `${n} جنيه مصري` : `${n} Egyptian pounds`);
  text = text.replace(/USD\s?([\d,.]+)/gi, (_, n) =>
    isArabic ? `${n} دولار أمريكي` : `${n} US dollars`);

  // ---------- area / units ----------
  text = text.replace(/(\d+)\s*sqm\b/gi, (_, n) =>
    isArabic ? `${n} متر مربع` : `${n} square meters`);
  text = text.replace(/(\d+)\s*sq\.?\s*m\b/gi, (_, n) =>
    isArabic ? `${n} متر مربع` : `${n} square meters`);
  text = text.replace(/(\d+)\s*m²/g, (_, n) =>
    isArabic ? `${n} متر مربع` : `${n} square meters`);
  text = text.replace(/(\d+)\s*sqft\b/gi, (_, n) =>
    isArabic ? `${n} قدم مربع` : `${n} square feet`);

  // ---------- bedrooms / bathrooms ----------
  text = text.replace(/(\d+)\s*BR\b/gi, (_, n) =>
    isArabic ? `${n} غرف نوم` : `${n} bedrooms`);
  text = text.replace(/(\d+)\s*BA\b/gi, (_, n) =>
    isArabic ? `${n} حمامات` : `${n} bathrooms`);
  text = text.replace(/(\d+)\s*BHK\b/gi, (_, n) =>
    isArabic ? `${n} غرف` : `${n} BHK`);

  // ---------- common RE abbreviations ----------
  const reAbbr: Record<string, [string, string]> = {
    'ROI':   ['عائد الاستثمار', 'return on investment'],
    'GFA':   ['المساحة الإجمالية', 'gross floor area'],
    'BUA':   ['المساحة المبنية', 'built-up area'],
    'PMT':   ['القسط الشهري', 'monthly payment'],
    'DP':    ['المقدم', 'down payment'],
  };
  for (const [abbr, [ar, en]] of Object.entries(reAbbr)) {
    const re = new RegExp(`\\b${abbr}\\b`, 'g');
    text = text.replace(re, isArabic ? ar : en);
  }

  // ---------- Egyptian compound names TTS hints ----------
  // Add a tiny pause (comma) before compound names so TTS doesn't rush them
  text = text.replace(/\b(كمبوند|compound)\s+/gi, '$1, ');

  return text;
}

function preprocessForTTS(raw: string, lang: string | undefined): string {
  let text = stripMarkdown(raw);
  text = expandRealEstateTerms(text, lang);
  return text.trim().slice(0, MAX_CHARS);
}

// ---------- route handler ----------

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

  const input = preprocessForTTS(text, language);
  const voice = pickVoice(language);
  const speed = pickSpeed(language);

  const openai = new OpenAI({ apiKey: process.env.OPENAI_API_KEY });

  try {
    const response = await openai.audio.speech.create({
      model: 'tts-1',
      voice,
      speed,
      input,
      response_format: 'opus',
    });

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
