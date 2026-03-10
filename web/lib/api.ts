const API_BASE = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:3456';

export interface SurveyParams {
  client_name?: string;
  question: string;
  options: string[];
  context?: string;
  sample_size: number;
  age_min?: number;
  age_max?: number;
  gender?: string;
  housing?: string;
  ethnicity?: string;
  income_min?: number;
  income_max?: number;
  marital?: string;
  education?: string;
  life_phase?: string;
  has_income?: boolean;
}

export interface EligibleParams {
  age_min?: number;
  age_max?: number;
  gender?: string;
  housing?: string;
  income_min?: number;
  income_max?: number;
  marital?: string;
  education?: string;
  life_phase?: string;
  has_income?: boolean;
}

export interface EligibleResult {
  total_population: number;
  eligible_count: number;
  eligible_pct: number;
  summary: {
    age_mean?: number;
    age_range?: string;
    income_median?: number;
    gender_dist?: Record<string, number>;
    housing_top3?: Record<string, number>;
    ethnicity_dist?: Record<string, number>;
  };
}

export interface JobStatus {
  job_id: string;
  status: 'queued' | 'sampling' | 'running' | 'done' | 'error';
  progress: number;
  total: number;
  eligible_count?: number;
  total_population?: number;
  result: SurveyResult | null;
  error: string | null;
}

export interface AgentLog {
  age: number;
  gender: string;
  ethnicity: string;
  income: number;
  housing: string;
  choice: string;
  willingness: number;
  concern: string;
  reward: number | null;
}

export interface SurveyResult {
  client_name: string;
  question: string;
  options: string[];
  total_population: number;
  eligible_count: number;
  n_respondents: number;
  timestamp: string;
  overall: {
    choice_distribution: Record<string, number>;
    avg_willingness: number;
    positive_rate: number;
  };
  breakdowns: {
    by_age: Record<string, { n: number; positive_rate: number; avg_willingness?: number }>;
    by_income: Record<string, { n: number; positive_rate: number }>;
  };
  concerns: string[];
  reasoning_samples: string[];
  agent_log: AgentLog[];
  quality: {
    available: boolean;
    model?: string;
    n_scored?: number;
    mean_reward?: number;
    high_quality?: number;
    high_quality_pct?: number;
    acceptable?: number;
    acceptable_pct?: number;
    low_quality?: number;
    low_quality_pct?: number;
  };
  cost: {
    total_tokens: number;
    total_cost_usd: number;
    cost_per_agent: number;
  };
}

export async function submitSurvey(params: SurveyParams): Promise<{ job_id: string }> {
  const res = await fetch(`${API_BASE}/api/survey`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ error: `HTTP ${res.status}` }));
    throw new Error(err.error || `HTTP ${res.status}`);
  }
  return res.json();
}

export async function getJobStatus(jobId: string): Promise<JobStatus> {
  const res = await fetch(`${API_BASE}/api/job/${jobId}`);
  return res.json();
}

export interface SimulationParams {
  question: string;
  options: string[];
  context?: string;
  event_name?: string;
  sample_size: number;
  age_min?: number;
  age_max?: number;
  gender?: string;
  housing?: string;
}

export interface SimulationJobStatus {
  job_id: string;
  status: 'queued' | 'sampling' | 'running' | 'done' | 'error';
  progress: number;
  total: number;
  rounds_done: number;
  current_round: 'day1' | 'day3' | 'day5' | 'day7' | null;
  interim_results: Record<string, { distribution: Record<string, number> }>;
  result: SimulationResult | null;
  error: string | null;
}

export interface SimulationResult {
  question: string;
  options: string[];
  event_name: string;
  sample_size: number;
  total_population: number;
  eligible_count: number;
  total_llm_calls: number;
  timestamp: string;
  summary: {
    day1_support_pct: number;
    day1_oppose_pct: number;
    day7_support_pct: number;
    day7_oppose_pct: number;
    opinion_changed_pct: number;
    moved_support: number;
    moved_oppose: number;
    polarization_d1: number;
    polarization_d7: number;
    echo_chamber_d1: number;
    echo_chamber_d7: number;
  };
  rounds: Record<string, { distribution: Record<string, number> }>;
  cluster_evolution: Record<string, {
    n: number;
    day1_avg: number;
    day3_avg: number;
    day5_avg: number;
    day7_avg: number;
    day1_majority: string;
    day7_majority: string;
  }>;
  demographic_shifts: Record<string, {
    n: number;
    support_d1: number;
    support_d7: number;
    oppose_d1: number;
    oppose_d7: number;
  }>;
  opinion_journeys: {
    age: number;
    gender: string;
    ethnicity: string;
    housing: string;
    income: number;
    cluster: string;
    day1_choice: string;
    day3_choice: string;
    day5_choice: string;
    day7_choice: string;
    day1_score: number;
    day3_score: number;
    day5_score: number;
    day7_score: number;
    day1_reasoning: string;
    day7_reasoning: string;
    changed: boolean;
  }[];
}

export async function submitSimulation(params: SimulationParams): Promise<{ job_id: string }> {
  const res = await fetch(`${API_BASE}/api/social-simulation`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ error: `HTTP ${res.status}` }));
    throw new Error(err.error || `HTTP ${res.status}`);
  }
  return res.json();
}

export async function getSimulationStatus(jobId: string): Promise<SimulationJobStatus> {
  const res = await fetch(`${API_BASE}/api/job/${jobId}`);
  return res.json();
}

export async function getEligibleCount(params: EligibleParams): Promise<EligibleResult> {
  const res = await fetch(`${API_BASE}/api/eligible`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(params),
  });
  return res.json();
}
