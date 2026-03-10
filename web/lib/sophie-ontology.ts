import { supabase } from './supabase';

export interface Industry {
  id: string;
  name: string;
  name_zh: string;
  icon: string;
  sort_order: number;
  is_other: boolean;
}

export interface Topic {
  id: string;
  industry_id: string;
  scenario_type: string;
  name: string;
  name_zh: string;
  description: string | null;
  description_zh: string | null;
  keywords: string[];
}

export interface ContextFact {
  id: string;
  topic_id: string;
  fact: string;
  fact_zh: string;
  source: string | null;
}

export interface AudiencePreset {
  age_min: number;
  age_max: number;
  gender: string;
  housing: string;
  income_min: number;
  income_max: number;
  rationale: string | null;
  rationale_zh: string | null;
}

export interface ProbeTemplate {
  stage: number;
  template: string;
  template_zh: string;
}

export interface SurveyPattern {
  name: string;
  name_zh: string;
  pattern_type: string;
  description: string | null;
  description_zh: string | null;
  example_question: string | null;
  example_question_zh: string | null;
  example_options: string[] | null;
  example_options_zh: string[] | null;
  best_for: string | null;
  best_for_zh: string | null;
}

// ─── Queries ───────────────────────────────────

export async function getIndustries(): Promise<Industry[]> {
  const { data, error } = await supabase
    .from('sophie_industries')
    .select('*')
    .order('sort_order');
  if (error) throw error;
  return data || [];
}

export async function getTopics(industryId: string, scenarioType: string): Promise<Topic[]> {
  const { data, error } = await supabase
    .from('sophie_topics')
    .select('*')
    .eq('industry_id', industryId)
    .eq('scenario_type', scenarioType)
    .order('sort_order');
  if (error) throw error;
  return data || [];
}

export async function getContextFacts(topicIds: string[]): Promise<ContextFact[]> {
  if (topicIds.length === 0) return [];
  const { data, error } = await supabase
    .from('sophie_context_facts')
    .select('*')
    .in('topic_id', topicIds);
  if (error) throw error;
  return data || [];
}

export async function getAudiencePreset(topicId: string): Promise<AudiencePreset | null> {
  const { data, error } = await supabase
    .from('sophie_audience_presets')
    .select('*')
    .eq('topic_id', topicId)
    .limit(1)
    .single();
  if (error && error.code !== 'PGRST116') throw error; // PGRST116 = no rows
  return data || null;
}

export async function getProbeTemplates(industryId: string, scenarioType: string): Promise<ProbeTemplate[]> {
  const { data, error } = await supabase
    .from('sophie_probe_templates')
    .select('stage, template, template_zh')
    .eq('industry_id', industryId)
    .eq('scenario_type', scenarioType)
    .order('stage')
    .order('sort_order');
  if (error) throw error;
  return data || [];
}

export async function getSurveyPatterns(): Promise<SurveyPattern[]> {
  const { data, error } = await supabase
    .from('sophie_survey_patterns')
    .select('*');
  if (error) throw error;
  return data || [];
}

// ─── Build context for Sophie's LLM prompt ───────

export async function buildOntologyContext(
  industryId: string,
  scenarioType: string,
): Promise<{
  topics: Topic[];
  facts: ContextFact[];
  probes: ProbeTemplate[];
  patterns: SurveyPattern[];
}> {
  const [topics, probes, patterns] = await Promise.all([
    getTopics(industryId, scenarioType),
    getProbeTemplates(industryId, scenarioType),
    getSurveyPatterns(),
  ]);

  const topicIds = topics.map(t => t.id);
  const facts = await getContextFacts(topicIds);

  return { topics, facts, probes, patterns };
}

// Format ontology into text for LLM system prompt
export function formatOntologyForPrompt(
  ontology: { topics: Topic[]; facts: ContextFact[]; probes: ProbeTemplate[]; patterns: SurveyPattern[] },
  zh: boolean
): string {
  const { topics, facts, probes, patterns } = ontology;

  let text = '';

  // Topics
  if (topics.length > 0) {
    text += zh ? '\n## 该行业常见调研主题\n' : '\n## Common Research Topics in This Industry\n';
    for (const t of topics) {
      text += `- ${zh ? t.name_zh : t.name}: ${zh ? (t.description_zh || '') : (t.description || '')}\n`;
    }
  }

  // Context facts
  if (facts.length > 0) {
    text += zh ? '\n## 新加坡相关事实\n' : '\n## Relevant Singapore Facts\n';
    for (const f of facts) {
      text += `- ${zh ? f.fact_zh : f.fact}${f.source ? ` (${f.source})` : ''}\n`;
    }
  }

  // Probe guidance
  if (probes.length > 0) {
    text += zh ? '\n## 提问指引（按阶段）\n' : '\n## Probing Guidance (by stage)\n';
    for (const p of probes) {
      text += `- Stage ${p.stage}: ${zh ? p.template_zh : p.template}\n`;
    }
  }

  // Survey patterns
  if (patterns.length > 0) {
    text += zh ? '\n## 可用的问卷设计模式\n' : '\n## Available Survey Design Patterns\n';
    for (const p of patterns) {
      text += `- ${zh ? p.name_zh : p.name} (${p.pattern_type}): ${zh ? (p.best_for_zh || '') : (p.best_for || '')}\n`;
    }
  }

  return text;
}
