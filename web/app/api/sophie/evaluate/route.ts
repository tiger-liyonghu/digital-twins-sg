import { NextRequest, NextResponse } from 'next/server';
import { buildOntologyContext, formatOntologyForPrompt } from '@/lib/sophie-ontology';

export const dynamic = 'force-dynamic';

const DEEPSEEK_API_KEY = process.env.SOPHIE_DEEPSEEK_KEY || process.env.DEEPSEEK_API_KEY || '';
const DEEPSEEK_URL = 'https://api.deepseek.com/v1/chat/completions';

export async function POST(req: NextRequest) {
  let body;
  try {
    body = await req.json();
  } catch {
    return NextResponse.json({ error: 'Invalid JSON body' }, { status: 400 });
  }

  const { industry, question, options, context, locale } = body as {
    industry: string;
    question: string;
    options: string[];
    context?: string;
    locale: 'en' | 'zh';
  };

  if (!question || !options || !Array.isArray(options) || options.length < 2) {
    return NextResponse.json({ error: 'Missing required fields: question, options (min 2)' }, { status: 400 });
  }

  const zh = locale === 'zh';
  const lang = zh ? '中文' : 'English';

  // 1. Check ontology match
  let ontologyText = '';
  let hasOntology = false;
  try {
    const ontology = await buildOntologyContext(industry, 'policy_simulation');
    ontologyText = formatOntologyForPrompt(ontology, zh);
    hasOntology = ontologyText.length > 100;
  } catch {
    // No ontology available
  }

  // 2. LLM evaluation
  const systemPrompt = `You are Sophie, a senior survey research quality auditor at Digital Twin Studio (Singapore).
You are reviewing a client's survey before it runs on 172,000 synthetic AI citizens.

${ontologyText}

Evaluate the survey and respond in EXACTLY this JSON format (no other text):
{
  "pass": true/false,
  "issues": [
    {"type": "question_quality|option_quality|audience|scope", "severity": "warning|error", "message": "...in ${lang}"}
  ],
  "suggestion": "Improved question text if needed, or null",
  "suggestion_options": ["Improved options if needed"] or null,
  "ontology_match": true/false,
  "ontology_note": "1 sentence about knowledge base match, in ${lang}",
  "fit_score": 1-5,
  "fit_reason": "1 sentence why this is/isn't a good fit for population simulation, in ${lang}"
}

EVALUATION CRITERIA:
- Question should be specific enough to get varied responses across demographics
- Options should be mutually exclusive and collectively exhaustive (include neutral/N.A.)
- Questions where demographics strongly influence answers = GREAT fit (score 4-5)
- Questions about pure personal taste with no demographic correlation = POOR fit (score 1-2)
- Check if options are balanced (not leading)
- Check if question is clear and unambiguous

IMPORTANT:
- pass=true if score >= 3 (even with warnings). pass=false only for score 1-2.
- Be concise. Max 2 issues.
- All text in ${lang}.`;

  const userMsg = `Survey to evaluate:
Industry: ${industry}
Question: ${question}
Options: ${options.join(' | ')}
${context ? `Context: ${context}` : '(No context provided)'}`;

  try {
    const res = await fetch(DEEPSEEK_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${DEEPSEEK_API_KEY}` },
      body: JSON.stringify({
        model: 'deepseek-chat',
        messages: [
          { role: 'system', content: systemPrompt },
          { role: 'user', content: userMsg },
        ],
        temperature: 0.3,
        max_tokens: 500,
      }),
    });

    const data = await res.json();
    const raw = data.choices?.[0]?.message?.content?.trim() || '';

    let jsonStr = raw;
    const jsonMatch = raw.match(/```(?:json)?\s*([\s\S]*?)```/);
    if (jsonMatch) jsonStr = jsonMatch[1].trim();

    const evaluation = JSON.parse(jsonStr);

    return NextResponse.json({
      ...evaluation,
      hasOntology,
    });
  } catch (e) {
    console.error('Sophie evaluate error:', e);
    // Silent pass — if evaluation fails, don't block the client
    return NextResponse.json({
      pass: true,
      issues: [],
      suggestion: null,
      suggestion_options: null,
      ontology_match: hasOntology,
      ontology_note: null,
      fit_score: 3,
      fit_reason: null,
      hasOntology,
    });
  }
}
