// ============================================================
// EXPERT LEARNING LOG — Findings from web research
// Last updated: 2026-03-07
// Next scheduled review: 2026-04-07
// ============================================================

const EXPERT_LEARNING_LOG = {
  last_updated: '2026-03-07',
  next_review: '2026-04-07',
  review_cycle: 'monthly',

  // ──────────────────────────────────────────────────────────
  // CONSOLIDATED ACTION ITEMS — Ranked by Priority
  // ──────────────────────────────────────────────────────────
  action_items: [

    // ============ CRITICAL — Parameter Errors to Fix Now ============
    {
      id: 'FIX-001',
      priority: 'CRITICAL',
      expert: 'policy_expert',
      title: 'CPF Wage Ceiling outdated: $6,800 → $8,000',
      detail: 'CPF OW ceiling increased to $8,000/month from 1 Jan 2026. System still uses $6,800 (Jan 2024 value).',
      files: ['engine/rules/life_rules.py', 'frontend/experts/knowledge.js'],
      action: 'Change min(income, 6800) to min(income, 8000)',
      source: 'https://www.cpf.gov.sg/employer/infohub/news/cpf-related-announcements/new-contribution-rates',
      status: 'fixed-2026-03-07'
    },
    {
      id: 'FIX-002',
      priority: 'CRITICAL',
      expert: 'policy_expert',
      title: 'CPF rates age 55-60 outdated: 27% → 34%',
      detail: 'Total CPF contribution rate for age 55-60 increased from 27% to 34% (employer 16% + employee 18%).',
      files: ['engine/rules/life_rules.py'],
      action: 'Update OA/SA/MA sub-allocation for age 55-60 bracket',
      source: 'https://cpflah.sg/2025/cpf-updates-from-1-jan-2026/',
      status: 'fixed-2026-03-07'
    },
    {
      id: 'FIX-003',
      priority: 'CRITICAL',
      expert: 'policy_expert',
      title: 'CPF rates age 60-65 outdated: 18% → 25%',
      detail: 'Total CPF contribution rate for age 60-65 increased from 18% to 25% (employer 12.5% + employee 12.5%).',
      files: ['engine/rules/life_rules.py'],
      action: 'Update OA/SA/MA sub-allocation for age 60-65 bracket',
      source: 'https://cpflah.sg/2025/cpf-updates-from-1-jan-2026/',
      status: 'fixed-2026-03-07'
    },
    {
      id: 'FIX-004',
      priority: 'CRITICAL',
      expert: 'policy_expert',
      title: 'Population reference outdated: 5.8M → 6.11M',
      detail: 'Singapore total population is 6,110,000 (June 2025), not 5,800,000.',
      files: ['engine/synthesis/ipf.py', 'frontend/experts/knowledge.js'],
      action: 'Update POPULATION constant and scale factor',
      source: 'https://www.population.gov.sg/files/media-centre/publications/Population_in_Brief_2025.pdf',
      status: 'fixed-2026-03-07'
    },
    {
      id: 'FIX-005',
      priority: 'CRITICAL',
      expert: 'policy_expert',
      title: 'EIP quota labels swapped for Chinese',
      detail: 'System has Chinese max 84%(block)/87%(neighborhood) but official is 87%(block)/84%(neighborhood).',
      files: ['frontend/experts/knowledge.js'],
      action: 'Swap block/neighborhood values',
      source: 'https://www.hdb.gov.sg/residential/buying-a-flat/buying-procedure-for-resale-flats/plan-source-and-contract/planning-considerations/eip-spr-quota',
      status: 'fixed-2026-03-07'
    },

    // ============ HIGH — Significant Improvements ============
    {
      id: 'IMP-001',
      priority: 'HIGH',
      expert: 'software_architect',
      title: 'Restructure LLM prompts for DeepSeek cache-hit pricing',
      detail: 'DeepSeek cache-hit: $0.07/M tokens vs $0.56/M (miss) — 8x difference. Shared system prompt prefix across batch = massive savings.',
      files: ['engine/v3/llm_client.py', 'engine/v3/persona_builder.py'],
      action: 'Ensure system prompt is identical across all agent calls in a batch; only user prompt varies',
      source: 'https://api-docs.deepseek.com/quick_start/pricing',
      status: 'pending'
    },
    {
      id: 'IMP-002',
      priority: 'HIGH',
      expert: 'software_architect',
      title: 'Implement exact-match prompt cache in Postgres',
      detail: 'Hash full prompt → check llm_cache table before API call. Many identical personas = 80-90% cache hits.',
      files: ['engine/v3/llm_client.py'],
      action: 'Add llm_cache table; hash-based lookup before API call',
      status: 'pending'
    },
    {
      id: 'IMP-003',
      priority: 'HIGH',
      expert: 'survey_methodologist',
      title: 'Third-person framing for sensitive questions',
      detail: 'arXiv 2512.22725: neutral third-person framing mitigates social desirability bias. Zero-cost prompt change.',
      files: ['engine/v3/persona_builder.py'],
      action: 'For sensitive topics, use "What would a person with these characteristics think..." instead of "You are..."',
      source: 'https://arxiv.org/html/2512.22725',
      status: 'pending'
    },
    {
      id: 'IMP-004',
      priority: 'HIGH',
      expert: 'survey_methodologist',
      title: 'A/B test persona prompting vs minimal prompting',
      detail: 'arXiv 2602.18462: persona prompting shows NO clear improvement on 70K+ instances. Must validate for our use case.',
      files: ['engine/v3/persona_builder.py'],
      action: 'Run GE2025 backtest with full persona vs demographics-only prompt; compare MAE',
      source: 'https://arxiv.org/abs/2602.18462',
      status: 'pending'
    },
    {
      id: 'IMP-005',
      priority: 'HIGH',
      expert: 'social_scientist',
      title: 'Tiered agent architecture: LLM leaders + rule-based followers',
      detail: 'FDE-LLM (Scientific Reports 2025) + OASIS: 10% opinion leaders get LLM calls, 90% followers use dynamics equations. 10x cost reduction.',
      files: ['engine/society/society_runner.py', 'engine/society/propagation.py'],
      action: 'Classify agents by centrality; top 10% get LLM reactions; others use CA+SIR dynamics calibrated from leader behavior',
      source: 'https://www.nature.com/articles/s41598-025-99704-3',
      status: 'pending'
    },
    {
      id: 'IMP-006',
      priority: 'HIGH',
      expert: 'social_scientist',
      title: 'Agent memory persistence across 7 simulation days',
      detail: 'A-Mem (arXiv 2502.12110) + AgentSociety: agents need structured memory of past exposures, opinion shifts, contradictions.',
      files: ['engine/society/society_runner.py'],
      action: 'Maintain per-agent memory dict across days; feed last 3 memories into LLM context',
      source: 'https://arxiv.org/pdf/2502.12110',
      status: 'pending'
    },
    {
      id: 'IMP-007',
      priority: 'HIGH',
      expert: 'social_scientist',
      title: 'Output validation after each LLM step',
      detail: 'GenSim: error correction prevents drift. Check intensity in [1,10], sentiment in valid set, consistency with profile.',
      files: ['engine/society/propagation.py'],
      action: 'Add validation layer after LLM reaction parsing; reject and retry invalid outputs',
      source: 'https://arxiv.org/abs/2410.04360',
      status: 'pending'
    },
    {
      id: 'IMP-008',
      priority: 'HIGH',
      expert: 'network_scientist',
      title: 'Add triadic closure to friend-layer construction',
      detail: 'If A-B and B-C are friends, A-C should also be friends with prob proportional to shared attributes. Raises clustering from ~0.1 to realistic ~0.3-0.5.',
      files: ['engine/society/social_graph.py'],
      action: 'Post-processing pass: for each agent, check friend-of-friend pairs; add edge with probability based on attribute similarity',
      source: 'https://arxiv.org/html/2509.02762',
      status: 'pending'
    },
    {
      id: 'IMP-009',
      priority: 'HIGH',
      expert: 'network_scientist',
      title: 'Inject neighborhood sentiment into LLM reaction prompts',
      detail: 'Bounded confidence model: agent decisions influenced by neighbors\' aggregate sentiment. Zero-cost prompt addition.',
      files: ['engine/society/propagation.py'],
      action: 'Before LLM call, count neighbor sentiments from social_inbox; add "Your contacts feel: X positive, Y negative" to prompt',
      source: 'https://arxiv.org/html/2402.05368v1',
      status: 'pending'
    },
    {
      id: 'IMP-010',
      priority: 'HIGH',
      expert: 'network_scientist',
      title: 'Cross-layer reinforcement in propagation',
      detail: 'Multi-source exposure boost: if agent hears from family AND friend, share prob increases. Models complex contagion (Centola 2010).',
      files: ['engine/society/propagation.py'],
      action: 'Track exposure source types per agent; multiply share_prob by (1 + 0.2*(num_source_types - 1))',
      status: 'pending'
    },
    {
      id: 'IMP-011',
      priority: 'HIGH',
      expert: 'network_scientist',
      title: 'Add graph validation metrics',
      detail: 'Report clustering coefficient (target 0.3-0.5), avg path length (<6), modularity (0.3-0.7), degree distribution shape.',
      files: ['engine/society/social_graph.py'],
      action: 'Add validate_graph() function computing these metrics; include in society result JSON',
      status: 'pending'
    },
    {
      id: 'IMP-012',
      priority: 'HIGH',
      expert: 'demographer',
      title: 'Add bivariate/trivariate JSD validation',
      detail: 'Current validation checks marginals only. Must validate joint distributions (age×ethnicity×area) to catch hidden distortions.',
      files: ['engine/synthesis/synthesis_gate.py', 'engine/synthesis/math_core.py'],
      action: 'Compute JSD at marginal, bivariate, and trivariate levels for all IPF dimension pairs',
      source: 'https://www.nature.com/articles/s41597-025-04380-7',
      status: 'pending'
    },
    {
      id: 'IMP-013',
      priority: 'HIGH',
      expert: 'demographer',
      title: 'Multi-level geographic validation (per planning area)',
      detail: 'US National Synthetic Pop validates at national + city + dissemination area. We should validate each of 28 planning areas independently.',
      files: ['engine/synthesis/synthesis_gate.py'],
      action: 'Run SRMSE + JSD for each planning area separately; flag areas with SRMSE > 0.10',
      source: 'https://www.nature.com/articles/s41597-025-04380-7',
      status: 'pending'
    },
    {
      id: 'IMP-014',
      priority: 'HIGH',
      expert: 'survey_methodologist',
      title: 'Implement EMRP for demographic poststratification',
      detail: 'Embedded MRP handles incomplete joint distributions (we only have marginals, not full 6-way joint). Corrects bias in classical MRP.',
      files: ['engine/v3/aggregator.py'],
      action: 'Replace proportional allocation with EMRP; generate synthetic pop tables from marginals, apply MRP for small-area estimates',
      source: 'https://pmc.ncbi.nlm.nih.gov/articles/PMC11418010/',
      status: 'pending'
    },

    // ============ MEDIUM — Improvements for Next Release ============
    {
      id: 'IMP-015',
      priority: 'MEDIUM',
      expert: 'social_scientist',
      title: 'Replace 15%/day flat decay with hat-function ad fatigue',
      detail: 'Research shows effectiveness rises for first 2-3 exposures (familiarity) then decays. More realistic than pure decay.',
      files: ['engine/society/info_injector.py'],
      action: 'day_rate = base_rate * hat_function(day) where hat peaks at day 2-3',
      source: 'https://www.sciencedirect.com/science/article/abs/pii/S0167923624001568',
      status: 'pending'
    },
    {
      id: 'IMP-016',
      priority: 'MEDIUM',
      expert: 'social_scientist',
      title: 'Network spillover correction for causal estimation',
      detail: 'Social graph creates interference between exposed/control groups. Need Aronow & Samii (2017) spillover-robust estimators.',
      files: ['engine/society/society_runner.py'],
      action: 'Compute and report spillover-adjusted ATE alongside raw exposed vs control comparison',
      source: 'https://www.turing.ac.uk/research/research-projects/causal-inference-and-agent-based-modelling',
      status: 'pending'
    },
    {
      id: 'IMP-017',
      priority: 'MEDIUM',
      expert: 'policy_expert',
      title: 'Add HDB Prime/Plus/Standard classification',
      detail: 'New 3-tier HDB classification system (from 2024) replaces mature/non-mature binary.',
      files: ['engine/core/agent.py', 'engine/synthesis/sg_distributions.py'],
      action: 'Add hdb_classification attribute correlated with planning_area',
      status: 'pending'
    },
    {
      id: 'IMP-018',
      priority: 'MEDIUM',
      expert: 'policy_expert',
      title: 'Update media channel order: TikTok first for young',
      detail: 'TikTok leads in time spent (34h29m/month). Add Facebook to senior tier.',
      files: ['engine/society/info_injector.py'],
      action: 'Reorder CHANNEL_AFFINITY["young"] to tiktok first; add facebook to senior set',
      status: 'pending'
    },
    {
      id: 'IMP-019',
      priority: 'MEDIUM',
      expert: 'network_scientist',
      title: 'Tie sharing threshold to Big Five personality',
      detail: 'Heterogeneous thresholds: high E → threshold 3 (simple spreader), low E → threshold 6 (requires convincing).',
      files: ['engine/society/propagation.py'],
      action: 'Replace fixed intensity>=4 with personality-based threshold',
      status: 'pending'
    },
    {
      id: 'IMP-020',
      priority: 'MEDIUM',
      expert: 'network_scientist',
      title: 'Add preferential attachment to friend selection',
      detail: 'Weight friend selection by (1 + current_degree)^0.5 to create realistic social hubs.',
      files: ['engine/society/social_graph.py'],
      action: 'Modify friend selection to include degree-based weighting',
      status: 'pending'
    },
    {
      id: 'IMP-021',
      priority: 'MEDIUM',
      expert: 'demographer',
      title: 'Add impossible-combination realism checks',
      detail: 'Flag: age 5 + university education, age 20 + retired status, etc.',
      files: ['engine/synthesis/synthesis_gate.py'],
      action: 'Add realism validator checking age-education, age-marital, age-income coherence',
      status: 'pending'
    },
    {
      id: 'IMP-022',
      priority: 'MEDIUM',
      expert: 'survey_methodologist',
      title: 'Prompt versioning + anchor calibration questions',
      detail: 'Temporal instability: same prompt yields different distributions over time. Need fixed calibration questions for drift detection.',
      files: ['engine/v3/job_runner.py'],
      action: 'Store prompt version + model version per job; run 3 anchor questions periodically to detect drift',
      status: 'pending'
    },
    {
      id: 'IMP-023',
      priority: 'MEDIUM',
      expert: 'software_architect',
      title: 'Migrate from polling to Supabase Queues (pgmq)',
      detail: 'pgmq provides guaranteed delivery, visibility timeout, no wasted connections. Drop-in replacement for 5s polling.',
      files: ['engine/v3/job_runner.py'],
      action: 'Enable pgmq extension; replace polling loop with pgmq.read()',
      source: 'https://supabase.com/docs/guides/queues',
      status: 'pending'
    },
    {
      id: 'IMP-024',
      priority: 'MEDIUM',
      expert: 'survey_methodologist',
      title: 'Multi-dimensional Nemotron scoring (5 dimensions)',
      detail: 'Expand from single quality score to helpfulness, correctness, coherence, complexity, verbosity. Use correctness to flag demographic implausibility.',
      files: ['scripts/api_server.py'],
      action: 'Request 5-dimension scores from Nemotron; flag low correctness responses',
      status: 'pending'
    },

    // ============ CRITICAL — Individual Coherence (from 100-agent audit 2026-03-07) ============
    {
      id: 'COH-001',
      priority: 'CRITICAL',
      expert: 'demographer',
      title: 'Income is generated independently of occupation',
      detail: 'Root cause of most contradictions. Income is drawn from P(income|education,age) but NEVER conditioned on occupation. Result: 27% of agents have income/occupation mismatch. Unemployed avg $4,746/mo, Students avg $1,909/mo (some $12K+). Estimated ~46,000 agents affected.',
      files: ['engine/synthesis/sg_distributions.py', 'engine/core/agent.py'],
      action: 'Add occupation→income override: Unemployed/Student→$0 (or small allowance), Retired→CPF payout model, Homemaker→$0. Then draw income only for employed occupations via P(income|education,age,occupation).',
      status: 'pending'
    },
    {
      id: 'COH-002',
      priority: 'CRITICAL',
      expert: 'demographer',
      title: 'Occupation assigned without age constraint',
      detail: 'Occupation drawn from P(occupation|education) only — no age dependency. Age 22 can become "Senior Official or Manager", age 24 can be Senior Manager. Estimated ~3,400 agents under 28 with senior titles.',
      files: ['engine/synthesis/sg_distributions.py'],
      action: 'Add age floor for senior occupations: Senior Official/Manager requires age≥35, Professional requires age≥23 (post-uni). Use P(occupation|education,age_group).',
      status: 'pending'
    },
    {
      id: 'COH-003',
      priority: 'HIGH',
      expert: 'policy_expert',
      title: 'NS delay not reflected in education assignment',
      detail: 'Male citizens serve NS 18-20, so cannot hold University degree before age ~24. Current CPT P(education|age) ignores gender×residency. Male citizen age 20-23 with University is impossible in Singapore.',
      files: ['engine/synthesis/sg_distributions.py'],
      action: 'For male Citizen/PR age 20-23: set max education to Post_Secondary/Polytechnic. University only from age 24+.',
      status: 'pending'
    },
    {
      id: 'COH-004',
      priority: 'HIGH',
      expert: 'demographer',
      title: 'WP workers in Condo/Landed housing',
      detail: 'Work Permit holders typically live in dormitories or shared housing, not luxury housing. ~2% of WP holders in Condo/Landed. Housing CPT uses P(housing|income) without residency constraint.',
      files: ['engine/synthesis/sg_distributions.py', 'engine/synthesis/household_builder.py'],
      action: 'Override housing for WP: 90% HDB_1_2 (shared), 10% HDB_3. FDW: inherit employer household. EP/SP: allow Condo.',
      status: 'pending'
    },
    {
      id: 'COH-005',
      priority: 'HIGH',
      expert: 'behavioral_psychologist',
      title: 'Children (age<15) with Chronic_Mild health',
      detail: 'Health CPT allows Chronic_Mild for infants/children. Age 0 with Chronic_Mild, age 9 with Chronic_Mild. Transition rate 2.5%/year from birth is unrealistic — children are overwhelmingly healthy.',
      files: ['engine/models/probability_models.py'],
      action: 'Set age 0-14: 99% Healthy, 1% Chronic_Mild. Chronic_Severe/Disabled: 0% for age<15.',
      status: 'pending'
    },
    {
      id: 'COH-006',
      priority: 'HIGH',
      expert: 'demographer',
      title: 'No cross-attribute coherence validation post-synthesis',
      detail: 'System validates marginal distributions (SRMSE) but never checks individual-level coherence. 21% of agents have at least one impossible/implausible attribute combination. Need a post-synthesis coherence filter.',
      files: ['engine/synthesis/synthesis_gate.py'],
      action: 'Add coherence_check() with ~15 rules (see COH-007). Run after synthesis, reject+resample violating agents. Target: <1% violation rate.',
      status: 'pending'
    },
    {
      id: 'COH-007',
      priority: 'HIGH',
      expert: 'demographer',
      title: 'Design: Coherence Rule Engine (15 rules)',
      detail: 'Proposed rules for post-synthesis validation:\n1. Student/Unemployed/Homemaker/Child → income=$0\n2. Senior Manager → age≥35\n3. Professional → age≥23\n4. Male citizen 18-20 → occupation=National_Service\n5. Male citizen 20-23 → education≤Post_Secondary\n6. Age<6 → education=No_Formal, occupation=Infant/Toddler\n7. Age 6-12 → education=Primary, occupation=Student\n8. Age 13-16 → education≤Secondary, occupation=Student\n9. WP → housing∈{HDB_1_2, HDB_3}\n10. FDW → housing=employer household\n11. Age<15 → health=Healthy (99%)\n12. Age<16 → marital=Single\n13. Age<21 citizen → marital≠Married (legal)\n14. Income>0 → occupation∉{Unemployed,Student,Child}\n15. Landed/Condo → income≥$3000 or age≥65(retired)',
      files: ['engine/synthesis/synthesis_gate.py'],
      action: 'Implement as validate_agent_coherence(agent) → list[violations]. Integrate into synthesis pipeline.',
      status: 'pending'
    },
  ],

  // ──────────────────────────────────────────────────────────
  // LEARNING SOURCES BY EXPERT
  // ──────────────────────────────────────────────────────────
  sources: {
    demographer: [
      'https://link.springer.com/article/10.1007/s43762-025-00195-9',
      'https://link.springer.com/article/10.1007/s10458-024-09680-7',
      'https://www.nature.com/articles/s41597-025-04380-7',
      'https://arxiv.org/abs/2502.20264',
      'https://www.population.gov.sg/files/media-centre/publications/Population_in_Brief_2025.pdf',
    ],
    social_scientist: [
      'https://www.nature.com/articles/s41599-024-03611-3',
      'https://arxiv.org/html/2502.08691v1',
      'https://arxiv.org/abs/2410.04360',
      'https://github.com/camel-ai/oasis',
      'https://www.nature.com/articles/s41598-025-99704-3',
      'https://arxiv.org/pdf/2502.12110',
      'https://link.springer.com/article/10.1007/s10462-025-11412-6',
    ],
    survey_methodologist: [
      'https://arxiv.org/abs/2602.18462',
      'https://arxiv.org/abs/2512.14562',
      'https://arxiv.org/html/2512.22725',
      'https://arxiv.org/html/2502.07068v1',
      'https://pmc.ncbi.nlm.nih.gov/articles/PMC11418010/',
      'https://www.verasight.io/reports/synthetic-omnibus-survey',
    ],
    network_scientist: [
      'https://arxiv.org/html/2509.02762',
      'https://aclanthology.org/2025.findings-acl.468/',
      'https://arxiv.org/html/2402.05368v1',
      'https://link.springer.com/article/10.1007/s41109-025-00731-w',
      'https://arxiv.org/html/2408.16629',
    ],
    software_architect: [
      'https://supabase.com/docs/guides/queues',
      'https://api-docs.deepseek.com/quick_start/pricing',
      'https://github.com/zilliztech/GPTCache',
      'https://dasroot.net/posts/2026/02/async-llm-pipelines-python-bottlenecks/',
    ],
    policy_expert: [
      'https://www.cpf.gov.sg/employer/infohub/news/cpf-related-announcements/new-contribution-rates',
      'https://www.hdb.gov.sg/residential/buying-a-flat/buying-procedure-for-resale-flats/plan-source-and-contract/planning-considerations/eip-spr-quota',
      'https://hashmeta.com/blog/singapore-social-media-landscape-in-2025-trends-and-opportunities/',
      'https://www.eld.gov.sg/finalresults2025.html',
      'https://www.population.gov.sg/files/media-centre/publications/Population_in_Brief_2025.pdf',
    ],
  },

  // ──────────────────────────────────────────────────────────
  // STATISTICS
  // ──────────────────────────────────────────────────────────
  stats: {
    total_items: 31,
    critical: 7,
    high: 14,
    medium: 10,
    experts_consulted: 9,
    sources_reviewed: 50,
    agents_audited: 100,
    coherence_violation_rate: '21%',
    date: '2026-03-07'
  }
};

if (typeof window !== 'undefined') window.EXPERT_LEARNING_LOG = EXPERT_LEARNING_LOG;
