import { NextRequest, NextResponse } from 'next/server';
import { buildOntologyContext, formatOntologyForPrompt, getAudiencePreset, getTopics } from '@/lib/sophie-ontology';

export const dynamic = 'force-dynamic';

// Use SOPHIE_DEEPSEEK_KEY to avoid shell env override of DEEPSEEK_API_KEY
const DEEPSEEK_API_KEY = process.env.SOPHIE_DEEPSEEK_KEY || process.env.DEEPSEEK_API_KEY || '';
const DEEPSEEK_URL = 'https://api.deepseek.com/v1/chat/completions';

interface ConvMessage {
  role: 'sophie' | 'client' | 'system';
  content: string;
}

// Sophie's conversation: probe client needs, then design survey
export async function POST(req: NextRequest) {
  const body = await req.json();
  const { action, scenarioId, scenarioName, industryId, conversation, locale, fileText } = body as {
    action: 'probe' | 'design_survey' | 'parse_upload';
    scenarioId: string;
    scenarioName: string;
    industryId?: string;
    conversation: ConvMessage[];
    locale: 'en' | 'zh';
    fileText?: string;
  };

  const zh = locale === 'zh';

  if (action === 'probe') {
    return handleProbe(scenarioId, scenarioName, industryId || 'other', conversation, zh);
  } else if (action === 'design_survey') {
    return handleDesignSurvey(scenarioId, scenarioName, industryId || 'other', conversation, zh);
  } else if (action === 'parse_upload') {
    return handleParseUpload(scenarioId, scenarioName, industryId || 'other', fileText || '', zh);
  }

  return NextResponse.json({ error: 'Unknown action' }, { status: 400 });
}

// Sophie asks probing questions to understand the client's needs
async function handleProbe(
  scenarioId: string,
  scenarioName: string,
  industryId: string,
  conversation: ConvMessage[],
  zh: boolean
) {
  const lang = zh ? '中文' : 'English';
  const clientMessages = conversation.filter(m => m.role === 'client');
  const turnCount = clientMessages.length;

  // Load ontology context from database
  let ontologyText = '';
  try {
    const ontology = await buildOntologyContext(industryId, scenarioId);
    ontologyText = formatOntologyForPrompt(ontology, zh);
  } catch (e) {
    console.error('Failed to load ontology:', e);
  }

  const systemPrompt = `You are Sophie, a senior market research consultant at Digital Twin Studio (Singapore).
You speak ${lang} naturally and conversationally — like a smart colleague, not a chatbot.
${zh ? '用口语化的"你"，不用"您"。简洁有力，不要官腔。' : 'Be concise, direct, and professional but warm.'}

The client is from the "${industryId}" industry and selected the "${scenarioName}" scenario category. Your job is to understand EXACTLY what they need through conversation.
${ontologyText}

You have had ${turnCount} exchanges with the client so far.

CONVERSATION STRATEGY:
- Turn 0: Ask what specific TOPIC they want to research (e.g. a policy, product, or issue — NOT a demographic group).
- Turn 1+: If you have BOTH a clear research topic AND understanding of what decision/problem this supports, respond with ready=true. Otherwise, ask ONE more clarifying question about whichever is missing.
- Maximum 3 turns. At turn 2+, you MUST respond with ready=true.
${turnCount >= 2 ? `You have had ${turnCount} exchanges. Respond with EXACTLY this JSON (no other text):
{"ready": true, "summary": "1-sentence summary of what the client wants to research"}` : ''}

${turnCount < 2 ? `RESPONSE FORMAT — you MUST respond with this JSON (no other text):
{
  "reply": "Your conversational message (2-3 sentences max)",
  "quick_replies": ["Option A", "Option B", "Option C", "Other"]
}

QUICK REPLY RULES (critical):
- quick_replies are clickable buttons the client can tap to answer quickly.
- Provide 3-4 options. Each must be under 15 characters in ${lang}.
- Options must be RESEARCH TOPICS or DECISIONS, never demographic groups (wrong: "老年人", "年轻人"; right: "CPF改革", "公积金提取").
- Options should be parallel in nature — all at the same level of specificity.
- The LAST option must always be "${zh ? '其他' : 'Other'}" so the client can type their own answer.
- Do NOT offer options that narrow the research to a single demographic unless the client specifically asked for that.` : ''}

IMPORTANT:
- Do NOT design the survey yet. Just ask questions to understand the need.
- Use the ontology knowledge above to ask informed, specific questions.
- Always respond in ${lang}.
- Keep responses SHORT — 2-3 sentences max.
- Never use emojis.`;

  const messages = [
    { role: 'system' as const, content: systemPrompt },
    ...conversation.map(m => ({
      role: (m.role === 'sophie' ? 'assistant' : 'user') as 'assistant' | 'user',
      content: m.content,
    })),
  ];

  // DeepSeek requires at least one user message
  if (!conversation.some(m => m.role === 'client')) {
    messages.push({
      role: 'user' as const,
      content: zh
        ? `客户选择了「${scenarioName}」场景。请开始提问。`
        : `The client selected the "${scenarioName}" scenario. Start probing.`,
    });
  }

  try {
    const res = await fetch(DEEPSEEK_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${DEEPSEEK_API_KEY}`,
      },
      body: JSON.stringify({
        model: 'deepseek-chat',
        messages,
        temperature: 0.7,
        max_tokens: 300,
      }),
    });

    const data = await res.json();
    const raw = data.choices?.[0]?.message?.content?.trim() || '';

    // Try to parse as JSON (structured reply with quick_replies, or ready signal)
    let reply = raw;
    let ready = false;
    let summary = '';
    let quickReplies: string[] = [];

    try {
      // Extract JSON if wrapped in ```json ... ```
      let jsonStr = raw;
      const jsonMatch = raw.match(/```(?:json)?\s*([\s\S]*?)```/);
      if (jsonMatch) jsonStr = jsonMatch[1].trim();

      const parsed = JSON.parse(jsonStr);
      if (parsed.ready) {
        ready = true;
        summary = parsed.summary || '';
        reply = jsonStr; // Keep raw JSON for ready signal
      } else if (parsed.reply) {
        reply = parsed.reply;
        quickReplies = Array.isArray(parsed.quick_replies) ? parsed.quick_replies : [];
      }
    } catch {
      // Not JSON, it's a plain conversational reply — that's fine
    }

    return NextResponse.json({ reply, ready, summary, quickReplies });
  } catch (e) {
    console.error('Sophie probe error:', e);
    return NextResponse.json({
      reply: zh
        ? '抱歉，我这边出了点问题。你能再说一下你想调研什么吗？'
        : "Sorry, I had a hiccup. Could you tell me again what you'd like to research?",
      ready: false,
      summary: '',
    });
  }
}

// Sophie designs a custom survey based on the conversation
async function handleDesignSurvey(
  scenarioId: string,
  scenarioName: string,
  industryId: string,
  conversation: ConvMessage[],
  zh: boolean
) {
  const lang = zh ? '中文' : 'English';

  // Load ontology for context facts and survey patterns
  let ontologyText = '';
  let defaultAudience = { ageMin: 21, ageMax: 64 };
  try {
    const ontology = await buildOntologyContext(industryId, scenarioId);
    ontologyText = formatOntologyForPrompt(ontology, zh);

    // Try to find matching topic and its audience preset
    const topics = await getTopics(industryId, scenarioId);
    if (topics.length > 0) {
      // Try to match conversation content to a topic
      const convText = conversation.map(m => m.content).join(' ').toLowerCase();
      const matchedTopic = topics.find(t =>
        t.keywords.some(kw => convText.includes(kw.toLowerCase()))
      ) || topics[0];

      const preset = await getAudiencePreset(matchedTopic.id);
      if (preset) {
        defaultAudience = { ageMin: preset.age_min, ageMax: preset.age_max };
      }
    }
  } catch (e) {
    console.error('Failed to load ontology for design:', e);
  }

  const systemPrompt = `You are Sophie, a senior survey research designer. Based on the conversation below, design a survey.
${ontologyText}

RULES:
- The survey question and ALL options must be in ${lang}.
- Design ONE clear, specific survey question that addresses the client's needs.
- Provide 5-8 answer options that are mutually exclusive and collectively exhaustive.
- Include a neutral/N.A. option as the last choice.
- Choose the most appropriate survey pattern from the patterns listed above.
- Write a context paragraph (in ${lang}) that describes the scenario background for the AI agents who will answer this survey. USE the Singapore facts listed above to make the context realistic and grounded. This context should include relevant facts but NEVER include the actual survey results or expected outcomes.
- Suggest appropriate audience filters. Default suggestion: age ${defaultAudience.ageMin}-${defaultAudience.ageMax}.

Respond in EXACTLY this JSON format (no other text):
{
  "question": "The survey question",
  "options": ["Option 1", "Option 2", "Option 3", "Option 4", "Option 5"],
  "context": "Background context paragraph for AI agents (3-5 sentences of relevant facts from the ontology)",
  "audience": {"ageMin": ${defaultAudience.ageMin}, "ageMax": ${defaultAudience.ageMax}},
  "rationale": "1-sentence explanation of why you designed it this way"
}`;

  const messages = [
    { role: 'system' as const, content: systemPrompt },
    ...conversation.map(m => ({
      role: (m.role === 'sophie' ? 'assistant' : 'user') as 'assistant' | 'user',
      content: m.content,
    })),
    {
      role: 'user' as const,
      content: `Now design the survey based on our conversation. Remember: everything in ${lang}.`,
    },
  ];

  try {
    const res = await fetch(DEEPSEEK_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${DEEPSEEK_API_KEY}`,
      },
      body: JSON.stringify({
        model: 'deepseek-chat',
        messages,
        temperature: 0.5,
        max_tokens: 800,
      }),
    });

    const data = await res.json();
    const raw = data.choices?.[0]?.message?.content?.trim() || '';

    // Extract JSON from response (may be wrapped in ```json ... ```)
    let jsonStr = raw;
    const jsonMatch = raw.match(/```(?:json)?\s*([\s\S]*?)```/);
    if (jsonMatch) jsonStr = jsonMatch[1].trim();

    const survey = JSON.parse(jsonStr);

    return NextResponse.json({
      question: survey.question,
      options: survey.options,
      context: survey.context,
      audience: survey.audience,
      rationale: survey.rationale,
    });
  } catch (e) {
    console.error('Sophie design error:', e);
    return NextResponse.json(
      { error: zh ? '问卷设计失败，请重试' : 'Survey design failed, please retry' },
      { status: 500 }
    );
  }
}

// Parse uploaded questionnaire text → extract survey components
async function handleParseUpload(
  scenarioId: string,
  scenarioName: string,
  industryId: string,
  fileText: string,
  zh: boolean
) {
  const lang = zh ? '中文' : 'English';

  // Load ontology for context
  let ontologyText = '';
  try {
    const ontology = await buildOntologyContext(industryId, scenarioId);
    ontologyText = formatOntologyForPrompt(ontology, zh);
  } catch (e) {
    console.error('Failed to load ontology for upload parse:', e);
  }

  const systemPrompt = `You are Sophie, a senior survey research designer at Digital Twin Studio (Singapore).
A client has uploaded a questionnaire or research document. Your job is to extract the key components and convert them into a structured survey that can be run on our synthetic population of 172,000 AI citizens.

${ontologyText}

Analyze the uploaded text and extract:
1. The core research QUESTION — what they want to find out
2. Answer OPTIONS — 5-8 mutually exclusive, collectively exhaustive choices
3. CONTEXT — background information for AI agents (use Singapore facts from ontology above)
4. TARGET AUDIENCE — age range and any other demographic filters
5. PAIN POINT — what business problem or uncertainty this research addresses

RULES:
- Output everything in ${lang}.
- If the uploaded text contains multiple questions, pick the MOST important one.
- If the text is vague, infer the most likely research intent based on the industry (${industryId}) and scenario (${scenarioName}).
- Always include a neutral/N.A. option as the last choice.
- Context must use real Singapore facts, never leak expected results.

Respond in EXACTLY this JSON format (no other text):
{
  "question": "The survey question",
  "options": ["Option 1", "Option 2", "..."],
  "context": "Background context for AI agents (3-5 sentences)",
  "audience": {"ageMin": 21, "ageMax": 64},
  "painPoint": "1-sentence summary of the client's pain point",
  "rationale": "1-sentence explanation of what you extracted and why"
}`;

  const messages = [
    { role: 'system' as const, content: systemPrompt },
    { role: 'user' as const, content: `Here is the uploaded document:\n\n---\n${fileText.slice(0, 6000)}\n---\n\nExtract the survey components. Everything in ${lang}.` },
  ];

  try {
    const res = await fetch(DEEPSEEK_URL, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${DEEPSEEK_API_KEY}`,
      },
      body: JSON.stringify({
        model: 'deepseek-chat',
        messages,
        temperature: 0.3,
        max_tokens: 1000,
      }),
    });

    const data = await res.json();
    const raw = data.choices?.[0]?.message?.content?.trim() || '';

    let jsonStr = raw;
    const jsonMatch = raw.match(/```(?:json)?\s*([\s\S]*?)```/);
    if (jsonMatch) jsonStr = jsonMatch[1].trim();

    const parsed = JSON.parse(jsonStr);

    return NextResponse.json({
      question: parsed.question,
      options: parsed.options,
      context: parsed.context,
      audience: parsed.audience,
      painPoint: parsed.painPoint,
      rationale: parsed.rationale,
    });
  } catch (e) {
    console.error('Sophie parse upload error:', e);
    return NextResponse.json(
      { error: zh ? '问卷解析失败，请重试' : 'Failed to parse questionnaire, please retry' },
      { status: 500 }
    );
  }
}
