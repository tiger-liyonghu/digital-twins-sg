// ============================================================
// EXPERT KNOWLEDGE BASE — Singapore Digital Twin
// Auto-generated from deep codebase scan + web research.
// Source of truth for all 7 expert advisors' system prompts.
// Last updated: 2026-03-09
//
// Team restructure (2026-03-09):
//   - NEW: DataKai (data_engineer) — external data ETL, fact freshness, distribution audit
//   - MERGED: social_scientist → demographer (Dr. Chen Wei covers both)
//   - MERGED: network_scientist → nlp_researcher (Dr. Alex Tan covers both)
//   - REMOVED: software_architect (Claude Dev covers architecture)
//
// IMPORTANT: Time-sensitive parameters (CPF, population, EIP, etc.)
// are centralized in params.js (SG_PARAMS). This file references
// those values for context but params.js is the single source of truth.
// ============================================================

const EXPERT_KB = {

// ──────────────────────────────────────────────────────────────
// EXPERT 0: Population Scientist — Dr. Chen Wei
// (Merged: former social_scientist Prof. Sarah Lim's ABM/society scope)
// ──────────────────────────────────────────────────────────────
demographer: {
  role: "Population Scientist (Demography + Social Simulation)",
  scope: "Population synthesis, IPF, Bayesian CPT, SRMSE quality gates, Census representativeness, ABM simulation, society mode, social graph dynamics, causal inference",
  files: [
    "engine/synthesis/ipf.py",
    "engine/synthesis/sg_distributions.py",
    "engine/synthesis/synthesis_gate.py",
    "engine/synthesis/math_core.py",
    "engine/synthesis/household_builder.py",
    "scripts/02_synthesize_population.py",
    "scripts/20_seed_148k_v3.py"
  ],
  knowledge: `
## IPF (Iterative Proportional Fitting) Engine
File: engine/synthesis/ipf.py

- Target population: 20,000 synthetic agents (v2); 172,000 (v3 = 148K NVIDIA + 24K synthetic children)
- Singapore real population: 6,110,000 (2025) → scale factor ~35.5
- 4 Census dimensions: age(21 groups) × gender(2) × ethnicity(4) × planning_area(28) = 4,704 cells
- Algorithm: Deming-Stephan IPF
- Max iterations: 20 (default)
- Convergence tolerance: 0.01 (1% max relative deviation)
- Ratio clipping: [0.2, 5.0] to prevent instability
- Integerization: TRS (Truncation-Residual-Sampling) with probabilistic rounding
  deficit = target_n - sum(int_count)
  probs = residuals / residuals.sum()
  Random selection of indices to increment
- Convergence: max_deviation = max(|current - target| / (target + 1)) < tolerance

## Census Marginals (GHS 2025 — sg_distributions.py)
Age distribution (21 groups, %):
  0-4:3.8, 5-9:3.8, 10-14:3.8, 15-19:4.4, 20-24:5.6, 25-29:6.7, 30-34:7.7,
  35-39:7.1, 40-44:7.6, 45-49:7.3, 50-54:6.9, 55-59:6.5, 60-64:6.4,
  65-69:5.8, 70-74:4.6, 75-79:3.3, 80-84:1.9, 85-89:1.1, 90-94:0.5, 95-99:0.2, 100+:0.1

Gender: Male 48.6%, Female 51.4% (sex ratio 947:1000)
Ethnicity: Chinese 73.9%, Malay 13.5%, Indian 9.0%, Others 3.5%
Residency (8 categories): Citizen 59.9%, PR 8.8%, EP 3.2%, SP 3.3%, WP 16.2%, FDW 4.2%, DP 2.2%, STP 2.2%
Planning areas: 28 zones — top 5: Bedok(5.3%), Tampines(5.2%), Jurong West(5.1%), Sengkang(5.0%), Woodlands(4.9%)

## Bayesian CPT Tables (sg_distributions.py)
Education | age_group:
  Children 0-4: 100% No_Formal
  Age 15-19: 45% Secondary, 35% Post_Secondary, 15% Polytechnic, 5% University
  Age 25-29: 48% University, 12% Postgraduate → targets 37.3% degree+ for 25+
  Age 40-44: 38% University, 12% Postgraduate, 16% Secondary
  Elderly 80+: 35% No_Formal, 30% Primary, 15% Secondary

Income | education, age:
  University 25-39: [0.02, 0.03, 0.08, 0.20, 0.30, 0.20, 0.11, 0.06] (8 bands: 0 to 15000+)
  University 40-54: [0.02, 0.02, 0.05, 0.12, 0.22, 0.24, 0.18, 0.15] (peak earning)
  Postgraduate 25-39: [0.02, 0.01, 0.04, 0.10, 0.24, 0.26, 0.18, 0.15]
  Secondary 20-54: [0.06, 0.14, 0.28, 0.24, 0.14, 0.08, 0.04, 0.02]
  Retired 65+: [0.75, 0.12, 0.06, 0.03, 0.02, 0.01, 0.005, 0.005]

Housing | income_band:
  High (15000+): HDB_1_2:0.5%, HDB_3:2%, HDB_4:8%, HDB_5_EC:15%, Condo:52%, Landed:22.5%
  Medium (5000-6999): HDB_1_2:2%, HDB_3:9%, HDB_4:28%, HDB_5_EC:28%, Condo:27%, Landed:6%
  Low (0): HDB_1_2:22%, HDB_3:30%, HDB_4:28%, HDB_5_EC:13%, Condo:6%, Landed:1%

Marital | age, gender:
  Male 25-29: Single 78%, Married 21%, Divorced 1%
  Male 30-34: Single 42%, Married 55%, Divorced 3%
  Female 30-34: Single 30%, Married 66%, Divorced 4%

## Quality Gates (synthesis_gate.py)
SRMSE formula: sqrt( mean( (O_i - E_i)^2 ) ) / mean(E_i)
Thresholds: <0.05 Excellent, <0.10 Good (HARD gate), <0.20 Acceptable (SOFT gate), >=0.20 FAIL

Census ground truth targets:
  gender: {M:0.486, F:0.514}
  ethnicity: {Chinese:0.739, Malay:0.135, Indian:0.090, Others:0.035}
  housing_agg: {HDB:0.772, Condo:0.179, Landed:0.047}
  education_degree_plus: 0.38
  median_age: 43.2, median_income_employed: 5000
  married_30_34: 0.60, mean_household_size: 3.06
  household_size_dist: {1:16.5%, 2:19.5%, 3:18%, 4:21.5%, 5:14.5%, 6:6%, 7:2.5%, 8:1.5%}

Hard gates (must pass): gender, ethnicity, median_age, married_30_34, mean_household_size
Soft gates (warnings): household_size_distribution, k_anonymity, housing, education, income

ACTUAL RESULTS (last run):
  Gender SRMSE: 0.0019 — EXCELLENT
  Ethnicity SRMSE: 0.0025 — EXCELLENT
  Median Age: 43.0 vs 43.2 — PASS
  Married 30-34: 0.60 vs 0.60 — PASS
  Mean HH Size: 3.31 vs 3.06 — PASS
  HH Size Dist SRMSE: 0.0685 — PASS
  Education Degree+: 0.38 vs 0.38 — PASS
  Median Income: 4890 vs 5000 — PASS
  Overall: 9/9 PASS

Full validation report (16 tests):
  Age dist: SRMSE=0.0074, chi2=8.81, p=0.985
  Gender: SRMSE=0.0019, chi2=0.07, p=0.788
  Ethnicity: SRMSE=0.0027, chi2=0.82, p=0.844
  Area (28 zones): SRMSE=0.0092, chi2=2.27, p=1.0
  Education 25+: SRMSE=0.0001, chi2=0.0, p=1.0
  Residency: SRMSE=0.0187
  Housing: SRMSE=0.0932
  Big Five O↔E: r=0.253 (expected positive) — PASS
  Big Five C↔N: r=-0.307 (expected negative) — PASS
  Risk↔O: r=0.483 — PASS
  Trust↔A: r=0.471 — PASS

## Household Builder (household_builder.py)
Target HH size distribution (GHS 2025):
  {1:15.3%, 2:18.8%, 3:18%, 4:22.3%, 5:15.5%, 6:6.5%, 7:2.6%, 8:1%} → mean 3.06

10 phases: married couples → children → unmarried adults → elderly → FDWs → WP/SP workers → singles → redistribution
Phase 10: constraint redistribution (max 10 rounds, target SRMSE<0.05)

## Gaussian Copula (math_core.py)
Income × Education_Years × Age correlation matrix:
  R = [[1.00, 0.55, 0.30], [0.55, 1.00, -0.15], [0.30, -0.15, 1.00]]
Algorithm: Cholesky decomposition → Z~N(0,I) → Y=Z@L.T → U=Φ(Y)

## Validation Math (math_core.py)
Available statistical tests:
  SRMSE, Chi-Square, KL Divergence, Hellinger Distance, Freeman-Tukey Residuals (|FT|>2 = significant)

## Data Sources
GHS 2025 Tables: 3 (age/gender), 18 (education), 24 (marital), 34 (housing), 35 (income), 45 (housing/area), 47 (residency)
Population Trends 2025 (SingStat Sep 2025)
MOM Labour Force Survey 2025 — median income $5,775/month
HDB Key Statistics 2024/2025
Population in Brief 2025
Schmitt et al. 2007 (56 countries, N=17,837) — Big Five SE Asian baseline

## LATEST RESEARCH FINDINGS (2026-03-07 Web Learning)

KNOWN ISSUES TO FIX:
- Population reference outdated: 5,800,000 → 6,110,000 (June 2025)
- Scale factor needs recalculation: ~35.5 (6.11M/172K)

METHODOLOGY ADVANCES:
- VAE-based household synthesis (MVAE-Pop2): could replace 10-phase builder for better joint correlations
- GenSynthPop: iterative conditional approach for spatially explicit synthesis (better area-specific profiles)
- SRMSE alone is insufficient: add JSD at bivariate/trivariate levels, NRMSE, RAE
- Multi-level geographic validation: validate each of 28 planning areas independently (target Pearson r>0.99 marginals, r>0.95 cross-tabs)
- Five-pillar quality: representativeness + novelty + diversity + realism + coherence
- Bland-Altman plots for visual diagnostics across planning areas
- US National Synthetic Pop benchmark: 120.7M households, Pearson r>0.99

KEY PAPERS:
- VAE for population synthesis (Springer 2025): link.springer.com/article/10.1007/s43762-025-00195-9
- GenSynthPop spatially explicit (2024): link.springer.com/article/10.1007/s10458-024-09680-7
- US National Synthetic Pop (Nature 2025): nature.com/articles/s41597-025-04380-7
- IPF exponential convergence proof (arXiv 2025): arxiv.org/abs/2502.20264
`
},

// ──────────────────────────────────────────────────────────────
// EXPERT 1: Computational Social Scientist — Prof. Sarah Lim
// NOTE: MERGED into demographer (Dr. Chen Wei) as of 2026-03-09.
// Knowledge retained here for reference; Dr. Chen Wei covers this scope.
// ──────────────────────────────────────────────────────────────
social_scientist: {
  role: "Computational Social Scientist",
  scope: "Agent-Based Modeling, Society Mode simulation, emergent behavior, causal inference",
  files: [
    "engine/society/society_runner.py",
    "engine/society/social_graph.py",
    "engine/society/info_injector.py",
    "engine/society/propagation.py",
    "engine/v3/job_runner.py"
  ],
  knowledge: `
## Society Mode — 7-Day Simulation Cycle
File: engine/society/society_runner.py

Entry: run_society_job(job, llm) → _run_society_async(job, llm)
Default: NUM_DAYS = 7

Daily cycle (repeated 7 times):
  Phase 1: Info Injection (0 LLM) — inject_info(agents, campaign, day)
  Phase 2: Social Inbox Merge — carry over messages from previous day's propagation
  Phase 3: Propagation & Reactions (async LLM) — propagate(graph, agents_dict, exposures, llm, day)
    Returns: (social_inbox, reactions)
  Phase 4: Memory Update — track cumulative reactions per agent
  Phase 5 (day 7 only): Final Decision Round — ALL agents (exposed + control) answer survey question

Final decision: exposed agents get context from last 3 reactions. Unexposed = control group.
Progress updated in DB each day. Cancel check every day.

Result structure:
{
  mode: "society", num_days: 7,
  graph_stats: {nodes, total_edges, avg_degree, by_type},
  daily: [{day, exposed_today, new_exposed, cumulative_exposed, reactions, social_spread, sentiment:{pos,neg,neutral}, avg_intensity, tokens, cost}],
  exposed_group: {total, percentages},
  control_group: {total, percentages},
  campaign_reach: {total_agents, total_exposed, reach_rate}
}

## Causal Inference Design
RCT analogy: exposed group = treatment, unexposed group = control
Compare response distributions to isolate campaign's actual impact from baseline opinion
No randomization of treatment assignment (it's based on channel overlap + exposure probability)
— this is observational, not true RCT, but the causal logic is similar

## Emergent Properties
- Echo chambers: high-homophily clusters amplify same sentiment
- Information mutation: messages retold in spreader's own words (one_line_reaction)
- Cascade saturation: decay + finite network means reach plateaus around day 4-5
- Sentiment drift: group sentiment can diverge from initial campaign tone through social reinterpretation

## Information Injection Rules (info_injector.py)
Campaign schema: {message, brand, channels[], target_filter, base_exposure_rate(0.1-0.8), type(ad|news|policy)}

Exposure formula:
  day_rate = base_rate × (1 - 0.15)^(day-1)    # 15% daily decay (ad fatigue)
  channel_boost = |campaign_channels ∩ agent_channels| / |campaign_channels|
  final_rate = day_rate × (0.5 + 0.5 × channel_boost)
  If university/postgrad: final_rate *= 1.1

Channel affinity by age:
  young (18-34): instagram, tiktok, xiaohongshu, youtube, telegram
  middle (35-54): facebook, whatsapp, straits_times, cna, linkedin
  senior (55+): straits_times, tv, whatsapp, print, radio

Exposure decay example (base_rate=0.30):
  Day 1: 30.0%, Day 2: 25.5%, Day 3: 21.7%, Day 4: 18.4%, Day 5: 15.7%, Day 6: 13.3%, Day 7: 11.3%

## Social Graph Construction (social_graph.py)
build_social_graph(agents, avg_family=3, avg_friends=5, avg_weak=3)

Layer 1 — Family (strength=0.8, bidirectional):
  Group married adults by planning_area
  Pair by gender + age proximity (≤10 years)
  Add children: younger, single, same area, age < parent_age - 18
  0-2 children per couple

Layer 2 — Friends (strength=0.2-0.6):
  Same planning_area + age_diff < 15 years
  strength = 0.2 + age_similarity×0.2 + ethnicity_bonus(0.1 if same)
  age_similarity = 1.0 - |age_diff|/15

Layer 3 — Weak ties (strength=0.1):
  Random cross-area connections (social media)

Typical 200-agent graph: ~2000 edges, avg degree ~10
Graph stats: {nodes, total_edges, avg_degree, max_degree, by_type:{family,friend,social_media}}

## Propagation Mechanics (propagation.py)
Step 1: Identify stimulated agents (those with exposure items)
Step 2: Batch LLM call for reactions → {intensity:1-10, sentiment, would_share, one_line_reaction}
Step 3: Social spreading:
  Threshold: would_share=true AND intensity >= 4
  spread_prob = connection_strength × intensity / 10
  if family: spread_prob = min(1.0, spread_prob × 1.5)
  if random() < spread_prob: target receives social_inbox message

Spread probability examples:
  Family(0.8), intensity=5: min(1.0, 0.8×0.5×1.5) = 0.6 (60%)
  Friend(0.4), intensity=5: 0.4×0.5 = 0.2 (20%)
  Weak(0.1), intensity=10: 0.1×1.0 = 0.1 (10%)

Social message structure:
  {type:"social", from_agent, relationship, content:one_line_reaction, sender_sentiment, day}

Key references:
  McPherson et al. 2001 (homophily — Annual Review of Sociology)
  Granovetter 1973 (strength of weak ties)
  Watts & Strogatz 1998 (small-world networks)
  Centola 2010 (complex contagion)

## LATEST RESEARCH FINDINGS (2026-03-07 Web Learning)

CRITICAL ADVANCES:
- FDE-LLM (Scientific Reports 2025): Fuse dynamics equations with LLM agents. 10% opinion leaders (LLM), 90% followers (CA+SIR). Validated on Weibo data. DIRECTLY applicable to our tiered architecture.
- AgentSociety (Tsinghua 2025): 10,000+ LLM agents, 5M interactions. Mind-Behavior Coupling architecture (planning + memory + reasoning).
- GenSim (2024): 100K agent platform with error-correction for LLM drift in long-running simulations.
- OASIS (CAMEL-AI): scales to 1M agents via hybrid LLM + rule-based architecture. Our scaling solution.

ARCHITECTURE RECOMMENDATIONS:
- Tiered agents: top 10% by centrality get LLM calls, rest use dynamics equations calibrated from leaders → 10x cost reduction
- Agent memory persistence across 7 days: store past exposures, opinion shifts, contradictions per agent
- Output validation layer: check intensity [1,10], sentiment valid, consistency with demographic profile after each LLM step
- Hat-function ad fatigue: effectiveness rises days 1-3 (familiarity) THEN decays, not pure exponential decay

CAUSAL INFERENCE:
- Network spillover invalidates naive exposed vs control comparison. Need Aronow & Samii (2017) spillover-robust estimators.
- RAG grounding: feed real Singapore news to anchor reactions in real-world context

VALIDATION WARNINGS:
- LLMs may WORSEN ABM validation due to black-box structure, cultural biases, stochastic outputs (Springer AI Review 2025)
- Temporal drift: agent behavior day 7 may differ from day 1 due to LLM stochasticity, not simulation dynamics
- LLM homophily bias: amplifies echo chambers beyond realistic levels

KEY PAPERS:
- FDE-LLM: nature.com/articles/s41598-025-99704-3
- AgentSociety: arxiv.org/html/2502.08691v1
- GenSim: arxiv.org/abs/2410.04360
- OASIS: github.com/camel-ai/oasis
- Validation challenge: link.springer.com/article/10.1007/s10462-025-11412-6
`
},

// ──────────────────────────────────────────────────────────────
// EXPERT 2: LLM Simulation Specialist — Dr. Alex Tan
// (Merged: former network_scientist Dr. Priya Nair's graph/diffusion scope)
// ──────────────────────────────────────────────────────────────
nlp_researcher: {
  role: "LLM Simulation Specialist (NLP + Network Dynamics)",
  scope: "LLM persona simulation, prompt engineering, bias detection, response parsing",
  files: [
    "engine/v3/llm_client.py",
    "engine/v3/persona_builder.py",
    "engine/v3/job_runner.py",
    "engine/llm/decision_engine.py",
    "engine/society/propagation.py"
  ],
  knowledge: `
## LLM Configuration (llm_client.py)
Provider: DeepSeek
API Key: sk-82775a6709e44d19b0ba428e2245bb3e
Base URL: https://api.deepseek.com/v1
Model: deepseek-chat
Temperature: 0.7
Max tokens: 300
Concurrency: 30 (asyncio.Semaphore)
Cost: $0.0007 per 1K tokens → ~$0.00014 per typical 200-token response

Retry strategy: 3 attempts, exponential backoff 2^attempt + random.uniform(0,1) seconds
Handles: 429 (rate limit), timeout (30s), JSON decode errors
Fallback: {"choice":"SKIPPED","reasoning":"LLM unavailable","confidence":0.0,"model":"fallback"}

Async batch: aiohttp.TCPConnector(limit=40), asyncio.Semaphore(30)
  gather with return_exceptions=True → replace exceptions with fallback

## Persona Builder (persona_builder.py)
3-layer persona construction:

Layer A — Statistical Identity (always present):
  "You are a {age}-year-old {ethnicity} {gender} living in {area}, Singapore.
   Education: {education}. Marital status: {marital}.
   Monthly income: $[income]. Housing: [housing].
   Occupation: {occupation}. Industry: {industry}.
   Health: {health}. Residency: {residency}. Life stage: {life_phase}.
   Personality: {big5_summary}."

Layer B — NVIDIA Narrative (adults with data_source!='synthetic'):
  persona field: truncate to 800 chars (~200 tokens)
  cultural_background: truncate to 400 chars
  hobbies_and_interests: truncate to 300 chars

Layer C — Memories (Phase 2, not yet active):
  Recent memory items with type and content

Big Five summarization thresholds:
  O > 3.8: "curious and open-minded" | O < 2.5: "practical and conventional"
  C > 3.8: "disciplined and organized" | C < 2.5: "spontaneous and flexible"
  E > 3.8: "outgoing and sociable" | E < 2.5: "reserved and introspective"
  A > 3.8: "cooperative and trusting" | A < 2.5: "competitive and skeptical"
  N > 3.8: "emotionally sensitive" | N < 2.5: "emotionally stable"
  Risk > 3.8: "risk-tolerant" | Risk < 2.2: "risk-averse"

40 persona columns fetched from DB:
  agent_id, age, age_group, gender, ethnicity, education_level, occupation, industry,
  planning_area, marital_status, monthly_income, income_band, housing_type, health_status,
  life_phase, residency_status, big5_o/c/e/a/n, risk_appetite, social_trust, religious_devotion,
  persona, professional_persona, cultural_background, hobbies_and_interests,
  career_goals_and_ambitions, data_source

## Prompt Templates

SURVEY MODE SYSTEM PROMPT:
"You are simulating a real person living in Singapore. Based on your persona,
answer the survey question by choosing ONE option.
Respond in JSON: {"choice":"...","reasoning":"1-2 sentences","confidence":0.0-1.0}
Be authentic. Your answer should reflect your persona's age, income, education,
personality, and life circumstances. Consider Singapore's social context."

USER PROMPT: "PERSONA:\\n{persona}\\n\\nQUESTION: {question}\\n\\nOPTIONS:\\n{options}\\nChoose one option and explain why."

SOCIETY DECISION PROMPT:
"...Based on your persona and everything you've experienced recently, answer the question.
Consider your persona, what you've seen/heard, and how your social circle feels."
— Includes context from last 3 reactions for exposed agents

REACTION PROMPT:
"...react to the information you just received.
Respond in JSON: {"intensity":1-10, "sentiment":"positive|negative|neutral",
"would_share":true|false, "one_line_reaction":"your gut reaction"}"

LLM DECISION ENGINE PROMPT (decision_engine.py):
"...choose ONE action from the provided action space.
Respond in JSON: {"action":"...","reasoning":"...","confidence":0.0-1.0,
"emotion_delta":{"happiness":-2 to +2,"anxiety":-2 to +2,"anger":-2 to +2}}"

## Response Parsing
Option matching (_match_option):
  1. Exact match (case-insensitive)
  2. Substring match (bidirectional)
  3. Fallback to first option
Decision layer tracking: "llm" | "rule" | "probability"

## Quality Scoring (api_server.py)
NVIDIA Llama-3.1-Nemotron-70B-Reward model for response quality:
  > -5: high quality (thoughtful, persona-consistent)
  -5 to -15: acceptable (correct but generic)
  < -15: low quality (lazy, contradictory)

## Bias Considerations
- LLM may exhibit: Western-centric bias in political attitudes, stereotype amplification
- Mitigation: detailed persona with 30+ attributes reduces generic responses
- Testing: compare trait distributions across demographic groups
- Known limitation: model knowledge cutoff means current events may not be reflected
- Validation: GE2025 backtest shows demographic patterns emerge naturally (not hard-coded)

Key reference: Argyle et al. 2023, "Out of One, Many", Political Analysis 31(3)
  — GPT-3 reproduces human survey responses when given detailed personas

## LATEST RESEARCH FINDINGS (2026-03-07 Web Learning)

CRITICAL: Persona prompting may not help (arXiv 2602.18462). A/B test needed.
PROMISING: Third-person framing for sensitive questions (arXiv 2512.22725) — zero-cost bias reduction.
PROMISING: PolyPersona fine-tuning (arXiv 2512.14562) — LoRA on compact model for Singapore data.
WARNING: Temporal instability — same prompt drifts over months. Need prompt versioning + anchor checks.
ACTION: Expand Nemotron scoring to 5 dimensions (helpfulness, correctness, coherence, complexity, verbosity).
`
},

// ──────────────────────────────────────────────────────────────
// EXPERT 3: Network Scientist — Dr. Priya Nair
// NOTE: MERGED into nlp_researcher (Dr. Alex Tan) as of 2026-03-09.
// Knowledge retained here for reference; Dr. Alex Tan covers this scope.
// ──────────────────────────────────────────────────────────────
network_scientist: {
  role: "Network Scientist",
  scope: "Social graph, network topology, information cascades, diffusion models",
  files: [
    "engine/society/social_graph.py",
    "engine/society/propagation.py",
    "engine/society/info_injector.py"
  ],
  knowledge: `
## Social Graph Architecture (social_graph.py)
build_social_graph(agents, avg_family=3, avg_friends=5, avg_weak=3) → adjacency dict

Three-layer multiplex network:

LAYER 1 — FAMILY (strength=0.8, bidirectional)
  Algorithm: _build_families()
  1. Group agents by planning_area
  2. Find married adults (marital_status=="married")
  3. Pair compatible: different gender, age ≤ 10 years apart
  4. Add children: same area, single, age < oldest_parent_age - 18
  5. 0-2 children per couple (random)
  Edge type: "family", strength: 0.8 fixed

LAYER 2 — FRIENDS (strength=0.2-0.6, depends on similarity)
  Selection: same planning_area + age_diff < 15 years
  Target: avg_friends=5 connections per agent
  Strength formula:
    age_similarity = 1.0 - |age_diff| / 15  (range [0, 1])
    ethnicity_bonus = 0.1 if same ethnicity, else 0
    strength = 0.2 + age_similarity × 0.2 + ethnicity_bonus
    → range [0.2, 0.5] without ethnicity bonus, [0.3, 0.6] with
  Edge type: "friend"

LAYER 3 — WEAK TIES (strength=0.1, cross-area)
  Selection: random agents from different planning areas
  Target: avg_weak=3 connections per agent
  Edge type: "social_media", strength: 0.1 fixed

## Network Statistics
Typical 200-agent graph:
  Nodes: 200, Edges: ~2000, Avg degree: ~10
  Edge type breakdown: family ~600, friend ~1000, weak ~400
  Max degree: ~25-30

Graph stats function output:
  {nodes, total_edges, avg_degree, max_degree, by_type:{family:N, friend:N, social_media:N}}

## Homophily Model
Primary homophily dimensions:
  1. Geography (planning_area) — strongest driver, affects family + friends
  2. Age proximity — continuous, 15-year window for friends
  3. Ethnicity — bonus weight for same-ethnicity connections
  4. Marital status — used for family pairing only

Reference: McPherson, Smith-Lovin & Cook 2001, "Birds of a Feather: Homophily in Social Networks"

## Information Cascade Dynamics (propagation.py)

Diffusion threshold model:
  Agent shares if: would_share=true AND intensity >= 4 (out of 10)
  This is a ~40% intensity threshold for activation

Spread probability:
  P(spread) = connection_strength × intensity / 10
  Family boost: P = min(1.0, P × 1.5)

Cascade mechanics:
  Day 1: Direct exposure (campaign → agents via channels)
  Day 2+: Social propagation (agent → connections via social_inbox)
  Messages carry: sender's reaction + sentiment + relationship type
  Receiver processes: "your {relationship} told you: {one_line_reaction}"

Information mutation:
  Original campaign message → Agent A reacts with one_line_reaction
  → Agent B receives A's reaction (not original message)
  → Agent B reacts to A's reaction with own one_line_reaction
  → Natural drift from original message through retelling

## Propagation Examples
Family edge (strength=0.8):
  intensity=3: P = 0.8×0.3×1.5 = 0.36 (won't share, below threshold 4)
  intensity=5: P = 0.8×0.5×1.5 = 0.60
  intensity=8: P = min(1.0, 0.8×0.8×1.5) = 0.96
  intensity=10: P = min(1.0, 0.8×1.0×1.5) = 1.00

Friend edge (strength=0.4):
  intensity=5: P = 0.4×0.5 = 0.20
  intensity=8: P = 0.4×0.8 = 0.32
  intensity=10: P = 0.4×1.0 = 0.40

Weak tie (strength=0.1):
  intensity=5: P = 0.1×0.5 = 0.05
  intensity=10: P = 0.1×1.0 = 0.10

## Network Properties Expected
- Small-world: high clustering (friends in same area) + short paths (weak ties bridge areas)
- Assortative mixing: by age, ethnicity, planning area
- Community structure: planning areas form natural clusters
- Degree distribution: approximately log-normal (not strict power-law due to bounded friend count)

References:
  Granovetter 1973 — Strength of Weak Ties
  Watts & Strogatz 1998 — Small-World Networks
  Centola 2010 — Complex Contagion (threshold models)
  Barabasi & Albert 1999 — Scale-Free Networks

## LATEST RESEARCH FINDINGS (2026-03-07 Web Learning)

TOPOLOGY IMPROVEMENTS:
- Triadic closure: post-processing pass after friend-layer. If A-B and B-C friends, add A-C edge. Raises clustering from ~0.1 to 0.3-0.5.
- Preferential attachment: weight friend selection by (1+current_degree)^0.5 for realistic hubs.
- Personality-based connections: Big Five compatibility as factor in friend selection (Appliednetsci 2019).
- Temporal edge activation: family=evenings/weekends, friends=work hours, weak=always-on.

DIFFUSION ADVANCES:
- Cross-layer reinforcement: if agent hears from family AND friend, boost share_prob by (1+0.2*(k-1)). Complex contagion (Centola 2010).
- Heterogeneous thresholds: tie sharing threshold to Big Five E. High E=threshold 3, Low E=threshold 6.
- Neighborhood sentiment injection: add "Your contacts feel: X positive, Y negative" to LLM prompt. Zero-cost.
- Bounded confidence model: agents only update from neighbors within confidence threshold.

VALIDATION:
- Must compute: clustering coefficient (target 0.3-0.5), avg path length (<6), modularity (0.3-0.7), degree distribution shape.
- LLMs overestimate political homophily (arXiv 2408.16629). Our weak ties must be explicitly heterophilous.
- Group agents (GA-S3, ACL 2025): represent similar agents with single LLM call, 5-10x cost reduction.

KEY PAPERS:
- Homophily-based synthesis: arxiv.org/html/2509.02762
- GA-S3: aclanthology.org/2025.findings-acl.468/
- Cross-layer cascade: sciencedirect.com/science/article/abs/pii/S0957417424028574
- MOSAIC (EMNLP 2025): aclanthology.org/2025.emnlp-main.325/
- Bounded confidence: arxiv.org/html/2402.05368v1
`
},

// ──────────────────────────────────────────────────────────────
// EXPERT 4: Survey Methodologist — Prof. Rachel Koh
// ──────────────────────────────────────────────────────────────
survey_methodologist: {
  role: "Survey Methodologist",
  scope: "Question design, sampling methodology, response quality, weighting, backtest",
  files: [
    "engine/v3/sampler.py",
    "engine/v3/aggregator.py",
    "engine/v3/job_runner.py",
    "scripts/api_server.py"
  ],
  knowledge: `
## Sampling Engine (sampler.py)
sample_agents(n=200, mode="stratified", filter_=None, strata=None) → list[dict]

Three modes:
1. RANDOM: fetch 3×n agents, random offset in [0, total-fetch_n], sample to n
2. STRATIFIED (default): fetch 5×n from random offset, client-side stratification
   Default strata: ["age_group", "gender", "ethnicity"]
   Allocation: k = max(1, round(n × stratum_size / pool_size))
   Trim/pad to exactly n
3. TARGETED: direct limit query with filters, returns first n matching

Available filters:
  age_min, age_max (range), planning_area (exact), gender (exact), ethnicity (exact),
  education_level (exact), income_min, income_max (range),
  housing_type (exact), life_phase (exact), data_source (exact)

Fallback total population: 172,000 (if count query times out on Supabase free tier)

## Sample Sizes & Cost Estimates
N=2: test (~$0.001, <10 sec)
N=50: quick (~$0.007, ~30 sec)
N=1000: standard (~$0.14, ~3 min)
N=5000: deep (~$0.70, ~15 min)

## Aggregation (aggregator.py)
aggregate_responses(agents, responses, breakdowns=None) → dict

Default breakdown dimensions (6):
  age_group, gender, ethnicity, income_band, housing_type, education_level

Output: {total, distribution:{opt:count}, percentages:{opt:pct},
  breakdowns:{dimension:{group:{counts,total,percentages}}}}

## Sophie Gatekeeper
5-criteria scoring (each 0 or 1):
  1. Human decision-driven? (not physics/chemistry)
  2. Social interaction effects? (opinions influenced by others)
  3. Real experiment infeasible? (ethical/logistical/cost barriers)
  4. Calibration data exists? (Census/surveys available)
  5. Counterfactual analysis needed? (what-if scenarios)
Score ≥3/5: proceed. Score 1-2/5: suggest better tool.

## Response Quality Scoring (api_server.py)
NVIDIA Llama-3.1-Nemotron-70B-Reward model:
  > -5: high quality (thoughtful, persona-consistent)
  -5 to -15: acceptable (correct but generic)
  < -15: low quality (lazy, contradictory)
Non-blocking: if scoring fails, survey continues

## Option Matching Logic
1. Exact case-insensitive match
2. Bidirectional substring match
3. Fallback to first option
— Ensures no response is lost even with imperfect LLM formatting

## Backtest Validation Results
Test 1: 2023 Presidential Election (N=1000, VS+RP method, 2026-03-07)
  Prediction (adjusted): Tharman 67.1%, Ng Kok Song 19.7%, Tan Kin Lian 13.2%
  Actual: Tharman 70.4%, Ng Kok Song 15.7%, Tan Kin Lian 13.9%
  MAE: 2.7pp — All three candidates within ±4pp
  Method: Verbalized Sampling + Reformulated Prompting (third-person neutral)
  Raw output: Tharman 59.9%, Ng Kok Song 17.6%, Tan Kin Lian 11.8%, Abstain 10.7%
  Abstention votes redistributed proportionally to candidates
  Status: COMPLETED

Test 2: 2024 GST 9% Consumer Impact (N=100, real LLM run 2026-03-05)
  Prediction: 73% will reduce spending (4% significantly + 69% moderately)
  Actual (CASE survey): ~60% planned to reduce non-essential spending
  MAE: 13pp — Direction correct, overestimates "reduce" share
  Known bias: LLM "moderation bias" — agents cluster in moderate responses
  Status: COMPLETED

Test 3: GE2025 General Election — PENDING
  Actual results (ELD): PAP 65.57%, WP 14.99%, PSP 3.50%, Others 15.94%
  Prediction: Not yet run — awaiting experiment design with Sophie
  Planned: N=1000, A/B DeepSeek vs SEA-LION, demographic breakdown

## Survey Design Best Practices
- MECE options: mutually exclusive, collectively exhaustive
- Neutral wording: avoid leading questions
- Cultural sensitivity: Singapore multiracial context
- Include "Undecided" option: reduces forced-choice bias
- Option order: randomized in prompt to reduce primacy bias

References: AAPOR Standard Definitions, Groves et al. Survey Methodology (2009)

## Web Research Findings (2026-03)

### EMRP — Embedded MRP for Incomplete Joint Distributions
Multilevel Regression and Poststratification (MRP) is standard for small-area opinion estimation
(Gelman & Little 1997, Park et al. 2004). Our system implicitly uses EMRP:
  - IPF produces cell-level joint distributions from marginals
  - Stratified sampling draws from these cells → equivalent to poststratification
  - LLM persona reasoning = multilevel regression substitute
  Advantage: works with published marginals only, no microdata needed
  Gap: currently no formal uncertainty quantification — should add posterior intervals

### Third-Person Framing (arXiv 2512.22725)
Social desirability bias in LLM surveys can be mitigated by third-person framing:
  - Instead of "What do YOU think about X?" → "What would someone like [persona] think about X?"
  - Reduces tendency of LLM to give socially desirable answers
  - Particularly effective for sensitive topics (politics, religion, discrimination)
  ACTION: Consider adding third-person framing option for sensitive survey questions

### Persona Prompting Critique (arXiv 2602.18462)
Comprehensive meta-analysis shows persona prompting has NO clear aggregate improvement:
  - Some tasks benefit, others are harmed — depends on task type
  - Key finding: persona helps reasoning tasks, hurts factual recall
  - Our system uses personas for OPINION generation (not factual recall) → likely beneficial
  - Recommendation: validate persona effect per question type, not assumed universal

### Adaptive Sampling Strategies
Modern survey methodology increasingly uses adaptive designs:
  - Responsive design: adjust sampling in real-time based on intermediate results
  - Our system could: detect convergence early (stop at N=500 if stable) or expand strata with high variance
  - Cost saving: 30-50% reduction in LLM calls for stable opinion distributions

### Survey Quality Metrics Beyond MAE
Professional survey quality extends beyond prediction accuracy:
  - Design effect (DEFF): ratio of actual variance to SRS variance — measures stratification efficiency
  - Effective sample size: N_eff = N / DEFF — true statistical power
  - Non-response bias: our LLM agents always respond (0% non-response) — unrealistic advantage
  - Item non-response: should model "Don't know" / refusal rates by demographic

References: Gelman & Little 1997, Park et al. 2004, AAPOR Standard Definitions, arXiv 2512.22725, arXiv 2602.18462
`
},

// ──────────────────────────────────────────────────────────────
// EXPERT 5: Behavioral Psychologist — Dr. Michael Ong
// ──────────────────────────────────────────────────────────────
behavioral_psychologist: {
  role: "Behavioral Psychologist",
  scope: "Big Five personality, Gaussian Copula, decision models, cultural psychology",
  files: [
    "engine/synthesis/personality_init.py",
    "engine/synthesis/math_core.py",
    "engine/core/agent.py",
    "engine/models/probability_models.py"
  ],
  knowledge: `
## Big Five Personality Model (personality_init.py)

SE Asian Baseline (Schmitt et al. 2007, 56 countries, N=17,837):
  Openness (O):          mean=3.45, sd=0.55
  Conscientiousness (C): mean=3.30, sd=0.58
  Extraversion (E):      mean=3.20, sd=0.60
  Agreeableness (A):     mean=3.55, sd=0.52
  Neuroticism (N):       mean=2.85, sd=0.62

Age Trajectory Adjustments (Soto et al. 2011):
  Age 0-9:   O+0.00, C-0.20, E+0.10, A-0.15, N+0.05
  Age 10-19: O+0.05, C-0.10, E+0.05, A-0.10, N+0.10
  Age 20-29: baseline (0 adjustment)
  Age 30-39: O-0.05, C+0.10, E-0.05, A+0.08, N-0.08
  Age 40-49: O-0.08, C+0.15, E-0.08, A+0.12, N-0.12
  Age 50-59: O-0.10, C+0.18, E-0.12, A+0.15, N-0.15
  Age 60-69: O-0.12, C+0.20, E-0.15, A+0.18, N-0.18
  Age 70-79: O-0.15, C+0.18, E-0.18, A+0.20, N-0.20
  Age 80-89: O-0.18, C+0.15, E-0.20, A+0.22, N-0.22

Pattern: C increases with age (maturity), N decreases (emotional stability),
  A increases (prosociality), E decreases (introversion), O decreases (less novelty-seeking)

Gender Adjustments (McCrae & Costa 2003):
  Male:   O+0.05, C+0.00, E-0.05, A-0.10, N-0.15
  Female: O-0.05, C+0.00, E+0.05, A+0.10, N+0.15

Inter-trait Correlation Matrix:
  O:  [1.00,  0.10,  0.25,  0.10, -0.15]
  C:  [0.10,  1.00,  0.15,  0.20, -0.30]
  E:  [0.25,  0.15,  1.00,  0.15, -0.25]
  A:  [0.10,  0.20,  0.15,  1.00, -0.35]
  N:  [-0.15,-0.30, -0.25, -0.35,  1.00]
Key: C↔N=-0.30 (conscientious people less neurotic), A↔N=-0.35 (agreeable less neurotic)

Generation process:
  1. adjusted_mean = baseline + age_trajectory + gender_adjustment
  2. Cholesky decomposition of correlation matrix → L
  3. z ~ N(0, I) in R^5
  4. raw = adjusted_mean + sd × (L @ z)
  5. Clip to [1.0, 5.0]

## Attitude Derivation
Risk appetite = 0.3×O - 0.2×N - 0.15×C + 0.15×age_factor + 2.5 + noise(0, 0.3)
  → High O (curious) + low N (stable) → higher risk appetite
  → Clip to [1.0, 5.0]

Political leaning = 0.35×O - 0.15×C - age_conservatism + 1.8 + noise(0, 0.35)
  → High O → more progressive; older → more conservative

Social trust = 0.25×A + 0.15×E - 0.15×N + 2.2 + noise(0, 0.3)
  → High A (trusting) + high E (sociable) → more trusting

Religious devotion = 0.15×C + 0.10×A + ethnicity_factor + age_religious + 2.0 + noise(0, 0.4)
  Ethnicity factors: Chinese:0.0, Malay:0.5, Indian:0.3, Others:0.1

## Validated Correlations (from validation_report.json)
  Big Five O↔E: r=0.253 (expected positive — PASS)
  Big Five C↔N: r=-0.307 (expected negative — PASS)
  Big Five A↔N: r=-0.305 (expected negative — PASS)
  Risk↔O: r=0.483 (strong positive — PASS)
  Trust↔A: r=0.471 (strong positive — PASS)

## Markov Transition Models (probability_models.py)

Job Status Transitions (annual):
  Employed→Employed: 92.0%, →Unemployed: 2.5%, →Self: 1.5%, →Retired: 3.0%
  Unemployed→Employed: 45.0%, →Unemp: 40.0%, →Self: 8.0%, →Retired: 5.0%
  Age > 55: higher retirement probability

Marital Transitions (annual):
  Single→Married: 5.0% (×1.5 for age 25-35)
  Married→Divorced: 0.7%, →Widowed: 0.3% (×1.5 for female 60+)

Health Transitions (annual):
  Healthy→Chronic_Mild: 2.5% (×1.5 if smoking, age factor: 1 + 0.02×(age-40) for age>40)
  Chronic_Mild→Chronic_Severe: 3.5%
  Chronic_Severe→Disabled: 3.5%

## Health Status by Age (CPT)
  Age 40-44: 78% Healthy, 14% Mild, 5% Severe, 3% Disabled
  Age 60-64: 45% Healthy, 28% Mild, 17% Severe, 10% Disabled
  Age 80+:   15% Healthy, 25% Mild, 30% Severe, 30% Disabled

## Society Mode — Personality Effects on Reaction
  High E (extraverted): more likely to share (would_share=true)
  High N (neurotic): stronger negative reactions (higher intensity for negative stimuli)
  High O (open): more receptive to novel information
  High A (agreeable): less extreme reactions, more socially conforming
  High C (conscientious): more measured, lower impulsivity in sharing

References:
  Schmitt et al. 2007 — 56-country Big Five study
  Soto et al. 2011 — Age differences in Big Five
  McCrae & Costa 2003 — Gender and personality
  Rentfrow et al. 2015 — Geographic personality
`
},

// ──────────────────────────────────────────────────────────────
// EXPERT 6: Singapore Policy Expert — Mr. Tan Keng Huat
// ──────────────────────────────────────────────────────────────
policy_expert: {
  role: "Singapore Policy Expert",
  scope: "CPF, HDB, NS, EIP, media landscape, social norms, life phases",
  files: [
    "engine/rules/life_rules.py",
    "engine/core/agent.py",
    "engine/synthesis/sg_distributions.py",
    "engine/synthesis/household_builder.py",
    "engine/society/info_injector.py"
  ],
  knowledge: `
## CPF Model (life_rules.py)
Contribution rates (2026 actual — see params.js for canonical values):
  Age ≤55:  OA 23%, SA 6%, MA 8% (total 37%)
  Age 55-60: OA 17%, SA 5.5%, MA 11.5% (total 34%)
  Age 60-65: OA 10%, SA 4.5%, MA 10.5% (total 25%)
  Age 65-70: OA 6.5%, SA 3%, MA 8% (total 17.5%)
  Age >70:  OA 5%, SA 2%, MA 6% (total 13%)

PR graduated rates:
  Years 0-2: 60% of citizen rates
  Years 2-3: 80%
  Years 3+: 100%

Wage ceiling: $8,000/month (Jan 2025+, was $6,800 pre-2025)
Calculation: cpf_add = int(min(income, 8000) × rate)

## National Service (agent.py, life_rules.py)
NS Status enum:
  NOT_APPLICABLE: females, non-citizens
  PRE_ENLISTMENT: males 16-17
  SERVING_NSF: males 18-19 (auto-enlist at 18)
  ACTIVE_NSMEN: males 20-39 (after ORD, annual reservist)
  COMPLETED: males 40+ (NS obligation done)
  EXEMPT: special cases

## Life Phase Rules (agent.py)
10 phases (deterministic from age/gender/status):
  DEPENDENCE: age 0-6
  GROWTH: age 7-12
  ADOLESCENCE: age 13-16
  NS_SERVICE: male, Citizen/PR, age 17-20
  ESTABLISHMENT: age 17-35 (default post-adolescence)
  BEARING: age 36-50 (or num_children>0 and age≥30)
  RELEASE: age 51-62
  RETIREMENT_EARLY: age 63-74
  DECLINE: age 75-84 or Chronic_Severe
  END_OF_LIFE: age 85+ or Disabled

Agent type:
  PASSIVE: age < 13 (follows parent)
  SEMI_ACTIVE: age 13-14 (shared decisions)
  ACTIVE: age 15+ (independent)

## Housing Model
Census-calibrated distribution: HDB 77.2%, Condo 17.9%, Landed 4.7%
HDB types: 1-2 room, 3-room, 4-room (29%), 5-room/EC (27%)
Housing | income CPT: low income → HDB 1-3, high income → Condo/Landed

HDB Ethnic Integration Policy (EIP) — see params.js for canonical values:
  Quota limits on ethnic proportions in each HDB block/neighborhood
  Chinese: max 87% (block), 84% (neighborhood)
  Malay: max 22% (block), 25% (neighborhood)
  Indian/Others: max 10% (block), 13% (neighborhood)
  Note: neighborhood limit is STRICTER than block (larger area, tighter control)

## Household Structure (household_builder.py)
Target distribution (GHS 2025): mean 3.06 persons
  {1:15.3%, 2:18.8%, 3:18%, 4:22.3%, 5:15.5%, 6:6.5%, 7:2.6%, 8:1%}

Formation phases:
  1. Married couples (same area, opposite gender, age±10)
  2. Children 0-17 attached (parent 22-45 years older)
  3. Unmarried adults 18-34: 85%(18-25), 70%(25-30), 50%(30-34) live with parents
  4. Elderly 65+: ~40% live with adult children
  5. FDWs attached to upper-income families (≥$5K/month)
  6. WP/SP workers: shared accommodation 2-6 per unit
  7-10. Singles, redistribution, constraint matching

## Media Landscape (info_injector.py)
Channel affinity by age group:
  Young (18-34): Instagram, TikTok, Xiaohongshu, YouTube, Telegram
  Middle (35-54): Facebook, WhatsApp, Straits Times, CNA, LinkedIn
  Senior (55+): Straits Times, TV, WhatsApp, Print, Radio

13 channels modeled: instagram, tiktok, facebook, whatsapp, youtube,
  xiaohongshu, telegram, straits_times, cna, linkedin, tv, radio, print

Education boost: University/Postgrad → 1.1× exposure (higher media consumption)

## Residency (8 categories)
  Citizen: 59.9% — full CPF, NS, vote
  PR: 8.8% — graduated CPF, NS for 2nd-gen males
  EP (Employment Pass): 3.2% — professionals, no CPF
  SP (S Pass): 3.3% — mid-skilled, levy
  WP (Work Permit): 16.2% — unskilled, dormitories
  FDW (Foreign Domestic Worker): 4.2% — live-in
  DP (Dependant's Pass): 2.2% — EP/SP family
  STP (Student Pass): 2.2% — enrolled students

## Income Model
Education multipliers: No_Formal:0.5, Primary:0.6, Secondary:0.7, Post_Secondary:0.85,
  Polytechnic:1.0, University:1.4, Postgraduate:1.8
Age multipliers: <25:0.5, 25-35:0.85, 35-45:1.0, 45-55:1.05, 55-63:0.90, 63-70:0.50, 70+:0.0
MOM median income: $5,775/month (2025)

## GE2025 Validation Patterns
PAP support by age: 21-34: ~55%, 35-54: ~65%, 55+: ~78% (increases with age)
Opposition concentration: younger, university-educated segments
Malay voters: distinctive patterns consistent with GRC data
Ethnicity: Chinese 73.9%, Malay 13.5%, Indian 9.0%, Others 3.5%
These patterns emerge from persona-driven LLM reasoning — NOT hard-coded

## Web Research Findings (2026-03)

### CRITICAL: CPF Parameter Updates (2025/2026)
Singapore CPF rates have been updated — our system uses outdated values:
  - Wage ceiling: $6,800 → $8,000/month (effective Jan 2025, raised again Sep 2025)
  - Age 55-60 total: 27% → 34% (significant increase since 2024)
  - Age 60-65 total: 18% → 25% (significant increase since 2024)
  - Age 65-70 total: 13% → 17.5%
  ACTION: Update life_rules.py CPF tables immediately — affects all financial calculations

### CRITICAL: Population Count
Singapore total population 2025: 6.11 million (not 5.8M as in our system)
  - Citizens: 3.64M, PRs: 0.56M, Non-residents: 1.91M
  ACTION: Update sg_distributions.py population parameters

### CRITICAL: EIP Quota Labels
Current code has Chinese quotas as: max 84% (block), 87% (neighborhood)
  Correct values: max 87% (block), 84% (neighborhood)
  The block and neighborhood labels appear swapped for Chinese
  ACTION: Verify and fix in household_builder.py

### CPF LIFE Scheme Updates
CPF LIFE (Lifelong Income For the Elderly):
  - Standard Plan: higher monthly payouts, lower bequest
  - Basic Plan: lower payouts, higher bequest
  - Escalating Plan (new 2025): payouts increase 2% annually to hedge inflation
  - Full Retirement Sum (FRS) 2025: $213,000 (up from $205,800)
  - Basic Retirement Sum (BRS): $106,500
  ACTION: Consider modeling CPF LIFE in retirement income calculations

### HDB BTO Changes 2025-2026
  - New flat classification: Standard, Plus, Prime (replaces mature/non-mature)
  - Plus/Prime flats: 10-year MOP, subsidy clawback on resale
  - Singles can buy 2-room flexi in any location (expanded from non-mature only)
  - Impact on housing model: different resale restrictions by classification

### Singapore Green Plan 2030
  - 80% of buildings green by 2030 (up from 49%)
  - EV adoption target: all new car registrations electric by 2030
  - Carbon tax: $25/tonne (2024) → $45 (2026) → $80 (2030)
  - Impact on simulation: energy costs, transport choices, green job creation

### Forward Singapore Initiatives
  - Majulah Package: $7,500 for lower-income Singaporeans aged 50+
  - SkillsFuture Level-Up: $4,000 credit for workers aged 40+
  - Workfare: enhanced for workers earning ≤$2,500/month
  - ComCare: long-term assistance eligibility widened

References: CPF Board Annual Report 2025, DOS Population Brief 2025, HDB Annual Report 2025, MOF Budget 2026
`
},

// ──────────────────────────────────────────────────────────────
// EXPERT 7: Privacy & Ethics Officer — Ms. Adeline Wee
// ──────────────────────────────────────────────────────────────
privacy_officer: {
  role: "Privacy & Ethics Officer",
  scope: "Data protection, PDPA, k-anonymity, AI governance, ethical AI",
  files: [
    "engine/compliance/validation_framework.py",
    "engine/compliance/ai_governance.py",
    "engine/compliance/privacy_engine.py",
    "engine/synthesis/synthesis_gate.py"
  ],
  knowledge: `
## k-Anonymity Enforcement (synthesis_gate.py)
Target: k ≥ 5 on quasi-identifiers
Quasi-identifier sets checked:
  [age_group, gender, planning_area]
  [age_group, gender, ethnicity]
  [planning_area, housing_type]

Actual results (20K population):
  min_k=1, violations: 166 on age/gender/area, 12 on age/gender/ethnicity
  172K population: violations significantly reduced due to larger base

## PDPA Compliance
Personal Data Protection Act 2012 (Singapore):
  - System uses ZERO real personal data
  - All agents are synthetic: generated from Census aggregate statistics
  - Census source: only published aggregate tables (GHS 2025), never individual records
  - No consent collection needed (no personal data)
  - LLM API calls: only synthetic persona descriptions sent, no PII

## Privacy Validation Framework (validation_framework.py)
Category C: Privacy (6 modules)
  C1: PDPA Compliance — zero direct identifiers ✓
  C2: k-Anonymity — k≥5 on quasi-identifiers
  C3: l-Diversity — l≥3 on sensitive attributes
  C4: Re-identification Risk — prosecutor risk <0.20, journalist risk <0.05
  C5: Synthetic Data Guide — 5-step compliance process
  C6: Cross-Border Transfer — legal safeguards for data sent to LLM providers

## AI Governance Framework (ai_governance.py)

A. AI Verify Assessment (Singapore IMDA framework, 11 principles):
  P1: Transparency — 5 checks: data sources documented, decision pipeline documented,
    limitations documented, synthetic nature disclosed, model methodology documented (ALL must pass)
  P2: Explainability — ≥95% decisions explainable
    Layer 1 (rules): always explainable
    Layer 2 (probability): require model coefficients
    Layer 3 (LLM): require reasoning chain
  P3: Reproducibility — SHA-256 hash comparison of same-seed runs (must match exactly)
  P7: Fairness — Disparate impact ratio ≥ 0.80 for all protected groups (80% rule)
    For each group: mean_outcome / max_group_mean ≥ 0.80
  P8: Data Governance — ≥4/5 checks (lineage, quality, PDPA, k-anonymity, retention)
  P10: Human Oversight — ≥3/5 checks (logging, review threshold, kill switch, override, approvals)

B. Agentic AI Governance (IMDA Jan 2026):
  D1: Risk Assessment — zero CRITICAL unmitigated risks
  D2: Human Accountability — approval checkpoints defined
  D3: Technical Controls — agent permission boundaries:
    can_read: true, can_write: false, max_actions_per_tick: 10, requires_human_approval: depends
  Action validation: validate_action(agent_type, action, target) → (bool, reason)

C. MAS FEAT Compliance (Financial services):
  Fairness: disparate impact ratios
  Ethics: 5-item checklist
  Accountability: audit trail
  Transparency: model card

## Model Card (ai_governance.py:generate_model_card)
Required sections:
  model_name: "Singapore Digital Twin — Synthetic Population Engine"
  version: "2.0"
  type: "Agent-based social simulation"
  data_sources: 5 public government sources
  synthetic_disclosure: "SYNTHETIC agents, no real individuals"
  methodology, decision_pipeline, limitations (8), intended_use (4), prohibited_use (4)
  evaluation_metrics (5), regulatory_compliance (5 frameworks)

## Prohibited Uses
  1. Individual-level predictions about real persons
  2. Automated decision-making without human oversight
  3. Surveillance or profiling
  4. Discrimination based on protected attributes

## Ethical Considerations
  - AI-generated opinions must be labeled as simulation, not real public opinion
  - Results should include confidence intervals and limitations
  - Demographic biases in LLM may affect output fairness
  - Regular fairness audits (80% rule) across all protected groups
  - Kill switch available: jobs can be cancelled mid-run
  - All decisions logged in agent_responses table with decision_layer tracking

## Complete Validation Module Registry (42 modules)
Category A: Population Synthesis (7 modules: IPF, marginals, joints, correlations, households, personality, rounding)
Category B: Event & Transition Models (6: mortality, Markov, fertility, CPF, marriage, income Gini)
Category C: Privacy (6: PDPA, k-anonymity, l-diversity, re-identification, synthetic guide, cross-border)
Category D: AI Governance (6: AI Verify, agentic risks, fairness, explainability, reproducibility, MAS FEAT)
Category E: LLM Safety (3: prompt safety, decision bounds, bias testing)
Category F: System Integrity (2: data lineage, model card)
`
},

// ──────────────────────────────────────────────────────────────
// EXPERT 8: Software Architect — James Liu
// NOTE: REMOVED as of 2026-03-09. Claude Dev covers architecture.
// Knowledge retained here for reference.
// ──────────────────────────────────────────────────────────────
software_architect: {
  role: "Software Architect",
  scope: "System design, async concurrency, database schema, API, cost, scaling",
  files: [
    "engine/v3/job_runner.py",
    "engine/v3/llm_client.py",
    "engine/v3/sampler.py",
    "engine/v3/db.py",
    "supabase/migrations/*.sql",
    "scripts/api_server.py"
  ],
  knowledge: `
## System Architecture

Backend: Python 3 + asyncio
Database: Supabase PostgreSQL (https://rndfpyuuredtqncegygi.supabase.co)
LLM: DeepSeek Chat API (https://api.deepseek.com/v1)
Frontend: Static HTML/JS + Supabase JS SDK + Chart.js
Deployment: Local runner process + static file server (port 8888)

## Async Concurrency Model (llm_client.py)
aiohttp + asyncio.Semaphore(30) for parallel LLM calls
TCPConnector(limit=40) — slightly above semaphore for connection reuse
Temperature: 0.7, Max tokens: 300
Retry: 3 attempts, exponential backoff 2^attempt + random(0,1) seconds
Rate limit (429): handled via backoff
Timeout: 30 seconds per request

Batch flow:
  1. Build list of (system_prompt, user_prompt) tuples
  2. Create semaphore, connector
  3. asyncio.gather(*tasks, return_exceptions=True)
  4. Replace exceptions with fallback responses
  5. Return ordered list

## Database Schema

agents (172K rows):
  agent_id TEXT PK, age INT, age_group TEXT, gender TEXT, ethnicity TEXT,
  residency_status TEXT, planning_area TEXT, education_level TEXT,
  occupation TEXT, industry TEXT, monthly_income INT, income_band TEXT,
  marital_status TEXT, housing_type TEXT, health_status TEXT,
  big5_o/c/e/a/n NUMERIC(3,2), risk_appetite NUMERIC, social_trust NUMERIC,
  religious_devotion NUMERIC, life_phase TEXT, is_alive BOOLEAN,
  data_source TEXT ('nvidia_nemotron'|'synthetic'|'hybrid'),
  persona TEXT, professional_persona TEXT, cultural_background TEXT,
  hobbies_and_interests TEXT, career_goals_and_ambitions TEXT
  Indexes: age_group, gender, ethnicity, planning_area, education, income_band, housing, data_source

simulation_jobs:
  id UUID PK, question TEXT, options JSONB, sample_size INT,
  filter JSONB, strata JSONB, sim_mode TEXT ('survey'|'society'),
  campaign JSONB, num_days INT DEFAULT 7,
  status TEXT ('pending'|'running'|'completed'|'failed'|'cancelled'),
  progress NUMERIC(0-100), result JSONB,
  total_agents INT, total_tokens INT, total_cost_usd NUMERIC,
  started_at TIMESTAMPTZ, completed_at TIMESTAMPTZ

agent_responses:
  id UUID PK, job_id UUID FK, agent_id TEXT FK,
  decision_layer TEXT ('llm'|'rule'|'probability'),
  choice TEXT, reasoning TEXT, confidence NUMERIC(0-1),
  llm_model TEXT, tokens_used INT, cost_usd NUMERIC

agent_memories:
  id UUID PK, agent_id TEXT FK,
  memory_type TEXT ('experience'|'decision'|'observation'|'belief_update'|'compressed'|'interaction'|'reflection'),
  content TEXT, importance INT(1-10),
  source_job_id UUID, source_event_id UUID, source_memory_ids UUID[]

runner_status: runner_id TEXT PK, last_heartbeat TIMESTAMPTZ, active_jobs INT, version TEXT

## Job Runner (job_runner.py)
Daemon loop: poll every 5 seconds for pending jobs
Flow: sample → build persona → async LLM batch → parse → aggregate → write results
Small job (≤5 agents): sync LLM calls
Large job (>5): async batch with semaphore(30)
Progress: update every 5% or 5 agents
Cancel check: every 10 completions
DB insert: 100 responses per batch (single agent fallback on batch failure)
Mode routing: sim_mode='survey' → run_one_job, sim_mode='society' → run_society_job

## Cost Model
DeepSeek pricing: $0.0007 / 1K tokens
Typical response: ~200 tokens → $0.00014 per agent

Survey mode costs:
  N=200: ~$0.028 (~3 min)
  N=1000: ~$0.14 (~3 min)
  N=5000: ~$0.70 (~15 min)

Society mode costs (200 agents, 7 days):
  Reactions/day: ~200-400 calls × 200 tokens
  Decision round: 200 calls × 200 tokens
  Total: ~$0.50-1.50 per full society job

## Error Handling & Resilience
LLM failure: 3 retries → fallback response (no data loss)
DB batch failure: fallback to single-agent inserts
Count query timeout: fallback to 172,000 (Supabase free tier)
Job cancellation: checked every 10 agents, graceful stop
Rate limiting: exponential backoff with jitter
Non-blocking quality scoring: Nemotron failure doesn't stop survey

## Scaling Analysis
Current: 172K agents, 30 concurrent LLM calls
Bottleneck: LLM API throughput (not DB or CPU)
N=200→5000: linear scaling in cost and time, no architecture changes needed
Theoretical max: limited by DeepSeek rate limits (~60 req/s)

## Code Structure
engine/
  core/agent.py — Agent dataclass (80+ attributes)
  synthesis/ — IPF, distributions, personality, households, quality gates
  models/ — Markov transitions, CPF, probability models
  llm/decision_engine.py — LLM persona reasoning
  v3/ — Current architecture: db, job_runner, sampler, persona_builder, llm_client, aggregator
  society/ — Society mode: society_runner, social_graph, info_injector, propagation
  compliance/ — Validation, privacy, AI governance (42 modules)
scripts/ — Population seeding, API server, validation

## Key Design Decisions
1. 148K NVIDIA Nemotron personas first (validated > synthetic)
2. Supabase only (serverless, no ops)
3. Async job queue (polling, not webhooks — simpler)
4. DeepSeek (cost-effective vs GPT-4: 10× cheaper)
5. Stratified sampling by default (representative without full scan)
6. 3-layer decision: rule → probability → LLM (deterministic → statistical → creative)
7. Static frontend (no framework, minimal dependencies)
8. sim_mode column (not 'mode' — PostgreSQL reserved word)

## Web Research Findings (2026-03)

### Supabase Queues (pgmq) — Replace Polling
Supabase now offers built-in Queues (based on pgmq):
  - Drop-in replacement for our 5-second polling daemon
  - select pgmq.send('job_queue', job_payload) — producer
  - select * from pgmq.read('job_queue', 30, 1) — consumer with visibility timeout
  - Built-in retry, dead-letter queue, exactly-once delivery
  - Eliminates: runner_status heartbeat table, polling overhead, race conditions
  ACTION: Evaluate migration from polling to Supabase Queues for job dispatch

### FDE-LLM: Fuse Dynamics Equations with LLM
Research approach for hybrid simulation:
  - 10% agents (opinion leaders) use full LLM reasoning
  - 90% agents (followers) use rule-based dynamics equations
  - Dynamics: opinion_t+1 = opinion_t + influence_sum × susceptibility
  - LLM leaders set the opinion landscape, rules propagate it
  - Cost reduction: 10× fewer LLM calls for society mode
  - Quality: similar to full-LLM for aggregate distributions
  Our system already has 3-layer decision (rule→probability→LLM) — FDE-LLM extends this

### DeepSeek Cache-Hit Pricing Optimization
DeepSeek offers 8× cost savings via cache hits:
  - Cache miss: $0.56/M input tokens
  - Cache hit: $0.07/M input tokens (87.5% savings)
  - Strategy: shared system prompt prefix across all agents in a batch
  - Our system: persona varies per agent, but system_prompt base is shared
  ACTION: Restructure prompts to maximize shared prefix (system instructions first, persona last)

### Async Architecture Improvements
  - Connection pooling: PgBouncer on Supabase (already available)
  - Batch insert: use COPY instead of INSERT for agent_responses (10× faster)
  - Streaming responses: DeepSeek supports SSE — could show progress per agent
  - WebSocket notifications: Supabase Realtime instead of polling for job status

### Horizontal Scaling Patterns
  - Multiple runner instances with job claiming (SELECT FOR UPDATE SKIP LOCKED)
  - Partition agent_responses by job_id for faster queries
  - Read replicas for frontend queries (Supabase Pro)
  - CDN for static frontend (Cloudflare Pages or Vercel)

### Observability Stack
  - OpenTelemetry traces for LLM call chains
  - Prometheus metrics: tokens/sec, cost/job, latency percentiles
  - Structured logging: JSON logs with job_id correlation
  - Alert on: job stuck >30min, cost >$5/job, error rate >5%

References: Supabase Queues docs, DeepSeek API pricing 2026, pgmq GitHub, OpenTelemetry docs
`
},

// ──────────────────────────────────────────────────────────────
// EXPERT NEW: Data Engineer — DataKai
// Added 2026-03-09. Responsible for external data quality,
// ETL pipelines, fact freshness, and distribution auditing.
// ──────────────────────────────────────────────────────────────
data_engineer: {
  role: "Data Engineer / Data Quality Officer",
  scope: "External data ETL, Singapore open data integration, fact freshness auditing, distribution validation, sophie_context_facts management",
  files: [
    "web/lib/sophie-ontology.ts",
    "web/supabase/sophie-ontology.sql",
    "engine/synthesis/sg_distributions.py",
    "frontend/experts/params.js",
    "scripts/04_validate_population.py"
  ],
  knowledge: `
## Core Responsibility
DataKai is the single point of accountability for data quality across the entire Digital Twin platform.
Three pillars:
1. **Freshness** — every fact has a source, year, and next-update date. Stale data gets flagged.
2. **Consistency** — no contradictions between params.js, sg_distributions.py, and sophie_context_facts.
3. **Completeness** — all topics in sophie_topics have relevant context facts with citable sources.

## Singapore Open Data Sources (Tier 1 — Must Monitor)

### SingStat Table Builder
- URL: https://tablebuilder.singstat.gov.sg/
- API: REST (JSON/CSV), docs at /view-api/for-developers
- Key tables for agent calibration:
  M810001 — Population indicators (annual)
  M810011 — Residents by age group, ethnic group, sex
  Household income by decile, dwelling type
- Update: monthly/quarterly/annual depending on table
- Action: quarterly pull of key marginals, compare vs sg_distributions.py

### data.gov.sg
- URL: https://data.gov.sg
- Format: REST API (JSON/CSV)
- Key datasets:
  Census 2020 by planning area (age, sex, ethnicity, dwelling) — 55 areas
  HDB resale prices (monthly, from 2017)
  CPI by category (monthly)
  Singapore residents by age/ethnicity/sex (annual)
  Hospital admissions, causes of death (annual)
  Employment by sector (quarterly)
- Action: automated monitoring of last-updated dates

### CPF Board Statistics
- URL: https://www.cpf.gov.sg/member/infohub/reports-and-statistics
- Key data: contribution rates by age, FRS, withdrawal stats, member balances by age/gender
- Format: XLSX download + CSV on data.gov.sg
- Update: quarterly/annual
- Action: verify CPF rates in params.js match latest published rates

### MOM Labour Force Data
- URL: https://stats.mom.gov.sg/
- Key data: median income by occupation/industry/age/education, unemployment rate
- Format: CSV + data.gov.sg API
- Update: quarterly
- Action: verify income distributions in sg_distributions.py

### MAS Statistics
- URL: https://www.mas.gov.sg/statistics
- API: REST (JSON) via developer.tech.gov.sg
- Key data: interest rates, exchange rates, credit/debit card volumes
- Update: daily to monthly

### LTA DataMall
- URL: https://datamall.lta.gov.sg
- API: REST, 10M calls/day
- Key data: passenger volume O-D, ridership, COE prices
- Update: real-time to monthly

### OneMap Population Query
- URL: https://www.onemap.gov.sg/apidocs/
- Key data: 22 demographic layers by planning area
- Format: REST API (JSON)

## Supabase Tables Under DataKai's Management

### sophie_context_facts (production)
- Current count: 37 facts
- Target: 200+ facts (all topics should have 3-5 facts)
- RULE: every fact MUST have source field with format "Organization YYYY" (e.g., "DOS 2025")
- RULE: no "Informal survey" sources — replace with citable data
- RULE: facts older than 2 years from current date get flagged for review

### sophie_topics (production)
- Current: 51 topics across 5 industries × 3 scenarios
- 13 topics have NO context facts — need to be populated

### sg_distributions.py (code)
- Contains: age/gender/ethnicity/residency marginals, CPTs for education|age, income|education+age, housing|income, marital|age+gender, health|age
- Data source: GHS 2025, Population Trends 2025, MOM 2025
- Known issue: age marginal sums to 0.949 not 1.0
- Known issue: income median $5,000 here vs $5,775 in params.js (different definitions: excl vs incl employer CPF — MUST document this clearly)

### params.js (code)
- Contains: CPF rates, population figures, HDB stats, EIP quotas, NS rules
- Version: 2026-03, verified 2026-03-07
- Monthly review cycle

## Data Quality Audit Checklist (Run Monthly)

### 1. Freshness Check
- [ ] All sophie_context_facts have source with year
- [ ] No facts citing data > 2 years old without justification
- [ ] params.js version date is within 30 days
- [ ] CPF rates match latest CPF Board publication

### 2. Consistency Check
- [ ] params.js median income matches sg_distributions.py (or difference documented)
- [ ] params.js ethnicity proportions match sg_distributions.py
- [ ] params.js population total matches sg_distributions.py scale factor
- [ ] sophie_context_facts don't contradict params.js
- [ ] sophie-types.ts defaultContext doesn't contradict sophie_context_facts

### 3. Completeness Check
- [ ] Every sophie_topic has >= 3 context facts
- [ ] Every industry has probe templates for all 3 scenarios
- [ ] Every topic with audience_preset has fact-backed age range rationale

### 4. Agent Distribution Audit
- [ ] Run validation against Census/GHS latest data
- [ ] Compare 172K agent marginals vs SingStat latest
- [ ] Flag any dimension with SRMSE > 0.10
- [ ] Check joint distributions (age×ethnicity×housing) not just marginals

## Known Data Issues (as of 2026-03-09)

### HIGH — Must Fix
1. Ethnicity randomly assigned to 148K NVIDIA agents, contradicts persona text
   - Example: agent described as "Chinese Singaporean" assigned ethnicity="Others"
   - Fix: extract ethnicity from NVIDIA persona text, use as ground truth
2. Students/unemployed get implausible income ($5,622/month for 19yo student)
   - Fix: income CPT must condition on occupation (student → $0-500)
3. Lunch cost inconsistency: sophie_context_facts says S$5-8 hawker, sophie-types.ts says S$8-15
   - Fix: standardize on DOS CPI food data, remove "Informal survey" source

### MEDIUM — Should Fix
4. Household income median cited as 2023 (S$10,099) — 2024/2025 data available
5. 65+ population cited as 16% — likely ~18%+ by 2025
6. Population 5.92M (2024) — 2025 data available (params.js has 6.11M, contradiction!)
7. CPF FRS $205,800 is 2025 — 2026 figure should be available
8. E-commerce penetration 15% likely understated by 2026
9. V3 pipeline dropped quality gates from V2 — need to re-implement

### LOW — Nice to Have
10. Add "as of YYYY-QN" to all rate-based facts (CPF, TDSR, etc.)
11. Hawker centre count (114) needs verification — new ones being built
12. BTO supply range (19K-23K) ends at 2025, extend to 2026

## ETL Pipeline Design (Future)

### Architecture
\`\`\`
Cron (monthly) → Python ETL scripts → Supabase tables
                                    ↓
                              sophie_context_facts (auto-update)
                              sg_distributions.py (flag for review)
                              params.js (flag for review)
\`\`\`

### API Integration Priority
1. SingStat Table Builder API — population, income, housing (auto-pull)
2. data.gov.sg API — CPI, HDB prices, employment (auto-pull)
3. CPF Board — manual check (no reliable API for rate tables)
4. MOM stats — semi-auto (data.gov.sg has some, rest manual)

### Data Versioning
- Every update creates a snapshot row with timestamp
- Previous values preserved for backtesting
- Changelog in learning_log.js
`
}

};

// Make globally available
if (typeof window !== 'undefined') window.EXPERT_KB = EXPERT_KB;
