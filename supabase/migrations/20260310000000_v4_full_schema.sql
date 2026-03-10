-- ============================================================
-- Digital Twins Singapore — V4 Full Schema (New Database)
-- Optimized: agents split into core + profiles
-- ============================================================

-- ============================================================
-- 1. AGENTS (Core demographics only — lightweight)
-- ============================================================
CREATE TABLE agents (
  agent_id    TEXT PRIMARY KEY,
  -- Demographics
  age         INTEGER NOT NULL CHECK (age >= 0 AND age <= 120),
  age_group   TEXT NOT NULL,
  gender      TEXT NOT NULL CHECK (gender IN ('M', 'F')),
  ethnicity   TEXT NOT NULL CHECK (ethnicity IN ('Chinese', 'Malay', 'Indian', 'Others')),
  residency_status TEXT NOT NULL DEFAULT 'Citizen'
    CHECK (residency_status IN ('Citizen','PR','EP','SP','WP','FDW','DP','STP')),
  planning_area TEXT,
  -- Education & Career
  education_level TEXT CHECK (education_level IN (
    'No_Formal','Primary','Secondary','Post_Secondary','Polytechnic','University','Postgraduate')),
  occupation  TEXT DEFAULT '',
  industry    TEXT DEFAULT '',
  monthly_income INTEGER DEFAULT 0,
  income_band TEXT DEFAULT '0',
  -- Housing & Health
  housing_type TEXT DEFAULT 'HDB_4',
  health_status TEXT DEFAULT 'Healthy'
    CHECK (health_status IN ('Healthy','Chronic_Mild','Chronic_Severe','Disabled')),
  marital_status TEXT DEFAULT 'Single',
  household_id TEXT,
  num_children INTEGER DEFAULT 0,
  -- Personality (Big Five, 1-5)
  big5_o      NUMERIC(3,2) DEFAULT 3.0,
  big5_c      NUMERIC(3,2) DEFAULT 3.0,
  big5_e      NUMERIC(3,2) DEFAULT 3.0,
  big5_a      NUMERIC(3,2) DEFAULT 3.0,
  big5_n      NUMERIC(3,2) DEFAULT 3.0,
  -- Attitudes (1-5)
  risk_appetite     NUMERIC(3,2) DEFAULT 3.0,
  political_leaning NUMERIC(3,2) DEFAULT 3.0,
  social_trust      NUMERIC(3,2) DEFAULT 3.0,
  religious_devotion NUMERIC(3,2) DEFAULT 3.0,
  -- Life state
  life_phase  TEXT DEFAULT 'establishment',
  is_alive    BOOLEAN DEFAULT TRUE,
  -- Media & Culture
  media_diet       TEXT,
  social_media_usage TEXT,
  dialect_group    TEXT,
  -- Data lineage
  data_source TEXT DEFAULT 'nvidia_nemotron'
    CHECK (data_source IN ('nvidia_nemotron','synthetic','hybrid')),
  created_at  TIMESTAMPTZ DEFAULT NOW(),
  updated_at  TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for stratified sampling
CREATE INDEX idx_agents_age_group ON agents(age_group);
CREATE INDEX idx_agents_gender ON agents(gender);
CREATE INDEX idx_agents_ethnicity ON agents(ethnicity);
CREATE INDEX idx_agents_planning_area ON agents(planning_area);
CREATE INDEX idx_agents_education ON agents(education_level);
CREATE INDEX idx_agents_income_band ON agents(income_band);
CREATE INDEX idx_agents_housing ON agents(housing_type);
CREATE INDEX idx_agents_age ON agents(age);
CREATE INDEX idx_agents_residency ON agents(residency_status);
CREATE INDEX idx_agents_strata ON agents(age_group, gender, residency_status);

-- ============================================================
-- 2. AGENT_PROFILES (Narrative text — loaded on demand)
-- ============================================================
CREATE TABLE agent_profiles (
  agent_id    TEXT PRIMARY KEY REFERENCES agents(agent_id) ON DELETE CASCADE,
  persona     TEXT DEFAULT '',
  professional_persona TEXT DEFAULT '',
  cultural_background TEXT DEFAULT '',
  sports_persona TEXT DEFAULT '',
  arts_persona TEXT DEFAULT '',
  travel_persona TEXT DEFAULT '',
  culinary_persona TEXT DEFAULT '',
  hobbies_and_interests TEXT DEFAULT '',
  career_goals_and_ambitions TEXT DEFAULT '',
  skills_and_expertise TEXT DEFAULT ''
);

-- ============================================================
-- 3. HOUSEHOLDS
-- ============================================================
CREATE TABLE households (
  household_id TEXT PRIMARY KEY,
  size         INTEGER DEFAULT 1,
  housing_type TEXT,
  planning_area TEXT,
  total_income INTEGER DEFAULT 0,
  created_at   TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- 4. SIMULATION_JOBS (Async survey queue)
-- ============================================================
CREATE TABLE simulation_jobs (
  id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  question     TEXT NOT NULL,
  options      JSONB NOT NULL DEFAULT '[]',
  sample_size  INTEGER NOT NULL DEFAULT 200,
  filter       JSONB DEFAULT '{}',
  strata       JSONB DEFAULT '["age_group","gender","ethnicity"]',
  sim_mode     TEXT DEFAULT 'survey',
  campaign     JSONB DEFAULT '{}'::jsonb,
  num_days     INTEGER DEFAULT 7,
  status       TEXT DEFAULT 'pending'
    CHECK (status IN ('pending','running','completed','failed','cancelled')),
  progress     NUMERIC(5,2) DEFAULT 0,
  result       JSONB,
  total_agents INTEGER DEFAULT 0,
  total_tokens INTEGER DEFAULT 0,
  total_cost_usd NUMERIC(8,4) DEFAULT 0,
  started_at   TIMESTAMPTZ,
  completed_at TIMESTAMPTZ,
  created_at   TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_jobs_status ON simulation_jobs(status);

-- ============================================================
-- 5. AGENT_RESPONSES (Per-agent per-job)
-- ============================================================
CREATE TABLE agent_responses (
  id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  job_id       UUID NOT NULL REFERENCES simulation_jobs(id) ON DELETE CASCADE,
  agent_id     TEXT NOT NULL REFERENCES agents(agent_id),
  decision_layer TEXT NOT NULL CHECK (decision_layer IN ('rule','probability','llm')),
  choice       TEXT NOT NULL,
  reasoning    TEXT,
  confidence   NUMERIC(3,2),
  llm_model    TEXT,
  tokens_used  INTEGER DEFAULT 0,
  cost_usd     NUMERIC(6,4) DEFAULT 0,
  created_at   TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_responses_job ON agent_responses(job_id);
CREATE INDEX idx_responses_agent ON agent_responses(agent_id);

-- ============================================================
-- 6. AGENT_MEMORIES (Episodic memory)
-- ============================================================
CREATE TABLE agent_memories (
  id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  agent_id        TEXT NOT NULL REFERENCES agents(agent_id) ON DELETE CASCADE,
  memory_type     TEXT NOT NULL DEFAULT 'experience'
    CHECK (memory_type IN ('experience','decision','observation','belief_update','compressed','interaction','reflection')),
  content         TEXT NOT NULL,
  importance      INTEGER NOT NULL DEFAULT 5 CHECK (importance >= 1 AND importance <= 10),
  source_job_id   UUID REFERENCES simulation_jobs(id),
  source_event_id UUID,
  source_memory_ids UUID[],
  created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_memories_agent ON agent_memories(agent_id);
CREATE INDEX idx_memories_type ON agent_memories(memory_type);
CREATE INDEX idx_memories_created ON agent_memories(created_at DESC);

-- ============================================================
-- 7. EVENTS (External/internal events)
-- ============================================================
CREATE TABLE events (
  id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  title               TEXT NOT NULL,
  description         TEXT,
  event_type          TEXT NOT NULL DEFAULT 'policy',
  impact_biological   NUMERIC(3,1) DEFAULT 0,
  impact_psychological NUMERIC(3,1) DEFAULT 0,
  impact_social       NUMERIC(3,1) DEFAULT 0,
  impact_economic     NUMERIC(3,1) DEFAULT 0,
  impact_cognitive    NUMERIC(3,1) DEFAULT 0,
  impact_spiritual    NUMERIC(3,1) DEFAULT 0,
  target_filter       JSONB,
  agents_affected     INTEGER DEFAULT 0,
  created_at          TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- 8. RUNNER_STATUS (Heartbeat)
-- ============================================================
CREATE TABLE runner_status (
  runner_id      TEXT PRIMARY KEY,
  last_heartbeat TIMESTAMPTZ NOT NULL DEFAULT NOW(),
  active_jobs    INTEGER DEFAULT 0,
  version        TEXT DEFAULT '1.0'
);

-- ============================================================
-- 9. SOPHIE ONTOLOGY TABLES
-- ============================================================

-- 9a. Industries
CREATE TABLE sophie_industries (
  id         TEXT PRIMARY KEY,
  name       TEXT NOT NULL,
  name_zh    TEXT NOT NULL,
  icon       TEXT NOT NULL DEFAULT '🔧',
  sort_order INT NOT NULL DEFAULT 0,
  is_other   BOOLEAN NOT NULL DEFAULT FALSE,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- 9b. Topics (industry × scenario)
CREATE TABLE sophie_topics (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  industry_id   TEXT NOT NULL REFERENCES sophie_industries(id) ON DELETE CASCADE,
  scenario_type TEXT NOT NULL CHECK (scenario_type IN ('policy_simulation','product_pricing','audience_intelligence')),
  name          TEXT NOT NULL,
  name_zh       TEXT NOT NULL,
  description   TEXT,
  description_zh TEXT,
  keywords      TEXT[] DEFAULT '{}',
  sort_order    INT NOT NULL DEFAULT 0,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_topics_industry_scenario ON sophie_topics(industry_id, scenario_type);

-- 9c. Context facts
CREATE TABLE sophie_context_facts (
  id         UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  topic_id   UUID NOT NULL REFERENCES sophie_topics(id) ON DELETE CASCADE,
  fact       TEXT NOT NULL,
  fact_zh    TEXT NOT NULL,
  source     TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_facts_topic ON sophie_context_facts(topic_id);

-- 9d. Audience presets
CREATE TABLE sophie_audience_presets (
  id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  topic_id    UUID NOT NULL REFERENCES sophie_topics(id) ON DELETE CASCADE,
  age_min     INT NOT NULL DEFAULT 18,
  age_max     INT NOT NULL DEFAULT 80,
  gender      TEXT NOT NULL DEFAULT 'all',
  housing     TEXT NOT NULL DEFAULT 'all',
  income_min  INT NOT NULL DEFAULT 0,
  income_max  INT NOT NULL DEFAULT 0,
  rationale   TEXT,
  rationale_zh TEXT
);

CREATE INDEX idx_audience_topic ON sophie_audience_presets(topic_id);

-- 9e. Probe templates
CREATE TABLE sophie_probe_templates (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  industry_id   TEXT NOT NULL REFERENCES sophie_industries(id) ON DELETE CASCADE,
  scenario_type TEXT NOT NULL CHECK (scenario_type IN ('policy_simulation','product_pricing','audience_intelligence')),
  stage         INT NOT NULL DEFAULT 1 CHECK (stage >= 1 AND stage <= 3),
  template      TEXT NOT NULL,
  template_zh   TEXT NOT NULL,
  sort_order    INT NOT NULL DEFAULT 0
);

CREATE INDEX idx_probes_industry_scenario ON sophie_probe_templates(industry_id, scenario_type);

-- 9f. Survey patterns
CREATE TABLE sophie_survey_patterns (
  id                 UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  name               TEXT NOT NULL,
  name_zh            TEXT NOT NULL,
  pattern_type       TEXT NOT NULL CHECK (pattern_type IN ('likert','choice','behavior','willingness','ranking','open_ended')),
  description        TEXT,
  description_zh     TEXT,
  example_question   TEXT,
  example_question_zh TEXT,
  example_options    JSONB,
  example_options_zh JSONB,
  best_for           TEXT,
  best_for_zh        TEXT
);

-- ============================================================
-- 10. DT STUDIO TABLES
-- ============================================================

-- 10a. Sessions
CREATE TABLE dt_sessions (
  id         TEXT PRIMARY KEY,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  updated_at TIMESTAMPTZ DEFAULT NOW(),
  scenario_id TEXT,
  status     TEXT DEFAULT 'active',
  title      TEXT,
  metadata   JSONB
);

-- 10b. Conversations
CREATE TABLE dt_conversations (
  id         BIGSERIAL PRIMARY KEY,
  session_id TEXT REFERENCES dt_sessions(id) ON DELETE CASCADE,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  role       TEXT,
  content    TEXT,
  phase      TEXT,
  metadata   JSONB
);

CREATE INDEX idx_conv_session ON dt_conversations(session_id);

-- 10c. Survey jobs
CREATE TABLE dt_survey_jobs (
  id              TEXT PRIMARY KEY,
  session_id      TEXT REFERENCES dt_sessions(id) ON DELETE CASCADE,
  created_at      TIMESTAMPTZ DEFAULT NOW(),
  job_type        TEXT,
  params          JSONB,
  status          TEXT DEFAULT 'queued',
  progress        INT DEFAULT 0,
  total           INT DEFAULT 0,
  started_at      TIMESTAMPTZ,
  completed_at    TIMESTAMPTZ,
  error_count     INT DEFAULT 0,
  quality_summary JSONB
);

-- 10d. Survey results
CREATE TABLE dt_survey_results (
  id         BIGSERIAL PRIMARY KEY,
  job_id     TEXT REFERENCES dt_survey_jobs(id) ON DELETE CASCADE,
  session_id TEXT REFERENCES dt_sessions(id) ON DELETE CASCADE,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  result_data JSONB,
  analysis   TEXT
);

-- 10e. Error logs
CREATE TABLE dt_error_logs (
  id         BIGSERIAL PRIMARY KEY,
  created_at TIMESTAMPTZ DEFAULT NOW(),
  session_id TEXT REFERENCES dt_sessions(id) ON DELETE CASCADE,
  job_id     TEXT,
  agent_id   TEXT,
  category   TEXT NOT NULL,
  severity   TEXT,
  detail     JSONB,
  resolution TEXT,
  resolved_at TIMESTAMPTZ
);

CREATE INDEX idx_errors_session ON dt_error_logs(session_id);
CREATE INDEX idx_errors_category ON dt_error_logs(category);

-- 10f. Quality incidents
CREATE TABLE dt_quality_incidents (
  id                   BIGSERIAL PRIMARY KEY,
  created_at           TIMESTAMPTZ DEFAULT NOW(),
  job_id               TEXT,
  agent_id             TEXT,
  issue_type           TEXT,
  prompt_used          TEXT,
  raw_response         TEXT,
  reward_score         FLOAT,
  was_excluded         BOOLEAN DEFAULT FALSE,
  replacement_agent_id TEXT
);

-- 10g. System learnings
CREATE TABLE dt_system_learnings (
  id                 BIGSERIAL PRIMARY KEY,
  created_at         TIMESTAMPTZ DEFAULT NOW(),
  source_incident_ids TEXT[],
  learning_type      TEXT,
  description        TEXT,
  before_state       TEXT,
  after_state        TEXT,
  applied_at         TIMESTAMPTZ,
  applied_by         TEXT DEFAULT 'auto'
);

-- 10h. Client files
CREATE TABLE dt_client_files (
  id             BIGSERIAL PRIMARY KEY,
  session_id     TEXT REFERENCES dt_sessions(id) ON DELETE CASCADE,
  created_at     TIMESTAMPTZ DEFAULT NOW(),
  file_type      TEXT,
  file_name      TEXT,
  storage_path   TEXT,
  file_size      INT,
  downloaded_at  TIMESTAMPTZ,
  download_count INT DEFAULT 0
);

-- ============================================================
-- 11. ROW LEVEL SECURITY
-- ============================================================

ALTER TABLE agents ENABLE ROW LEVEL SECURITY;
ALTER TABLE agent_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE households ENABLE ROW LEVEL SECURITY;
ALTER TABLE simulation_jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE agent_responses ENABLE ROW LEVEL SECURITY;
ALTER TABLE agent_memories ENABLE ROW LEVEL SECURITY;
ALTER TABLE events ENABLE ROW LEVEL SECURITY;
ALTER TABLE runner_status ENABLE ROW LEVEL SECURITY;
ALTER TABLE sophie_industries ENABLE ROW LEVEL SECURITY;
ALTER TABLE sophie_topics ENABLE ROW LEVEL SECURITY;
ALTER TABLE sophie_context_facts ENABLE ROW LEVEL SECURITY;
ALTER TABLE sophie_audience_presets ENABLE ROW LEVEL SECURITY;
ALTER TABLE sophie_probe_templates ENABLE ROW LEVEL SECURITY;
ALTER TABLE sophie_survey_patterns ENABLE ROW LEVEL SECURITY;
ALTER TABLE dt_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE dt_conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE dt_survey_jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE dt_survey_results ENABLE ROW LEVEL SECURITY;
ALTER TABLE dt_error_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE dt_quality_incidents ENABLE ROW LEVEL SECURITY;
ALTER TABLE dt_system_learnings ENABLE ROW LEVEL SECURITY;
ALTER TABLE dt_client_files ENABLE ROW LEVEL SECURITY;

-- Public read policies
CREATE POLICY "Public read agents" ON agents FOR SELECT USING (true);
CREATE POLICY "Public read profiles" ON agent_profiles FOR SELECT USING (true);
CREATE POLICY "Public read households" ON households FOR SELECT USING (true);
CREATE POLICY "Public read jobs" ON simulation_jobs FOR SELECT USING (true);
CREATE POLICY "Public read responses" ON agent_responses FOR SELECT USING (true);
CREATE POLICY "Public read memories" ON agent_memories FOR SELECT USING (true);
CREATE POLICY "Public read events" ON events FOR SELECT USING (true);
CREATE POLICY "Public read sophie_industries" ON sophie_industries FOR SELECT USING (true);
CREATE POLICY "Public read sophie_topics" ON sophie_topics FOR SELECT USING (true);
CREATE POLICY "Public read sophie_facts" ON sophie_context_facts FOR SELECT USING (true);
CREATE POLICY "Public read sophie_audience" ON sophie_audience_presets FOR SELECT USING (true);
CREATE POLICY "Public read sophie_probes" ON sophie_probe_templates FOR SELECT USING (true);
CREATE POLICY "Public read sophie_patterns" ON sophie_survey_patterns FOR SELECT USING (true);
CREATE POLICY "Public read dt_sessions" ON dt_sessions FOR SELECT USING (true);
CREATE POLICY "Public read dt_conversations" ON dt_conversations FOR SELECT USING (true);
CREATE POLICY "Public read dt_survey_jobs" ON dt_survey_jobs FOR SELECT USING (true);
CREATE POLICY "Public read dt_survey_results" ON dt_survey_results FOR SELECT USING (true);

-- Service role write policies
CREATE POLICY "Service write agents" ON agents FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Service write profiles" ON agent_profiles FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Service write households" ON households FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Service write jobs" ON simulation_jobs FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Service write responses" ON agent_responses FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Service write memories" ON agent_memories FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Service write events" ON events FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Service write runner" ON runner_status FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Service write sophie_industries" ON sophie_industries FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Service write sophie_topics" ON sophie_topics FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Service write sophie_facts" ON sophie_context_facts FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Service write sophie_audience" ON sophie_audience_presets FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Service write sophie_probes" ON sophie_probe_templates FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Service write sophie_patterns" ON sophie_survey_patterns FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Service write dt_sessions" ON dt_sessions FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Service write dt_conversations" ON dt_conversations FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Service write dt_survey_jobs" ON dt_survey_jobs FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Service write dt_survey_results" ON dt_survey_results FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Service write dt_error_logs" ON dt_error_logs FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Service write dt_quality_incidents" ON dt_quality_incidents FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Service write dt_system_learnings" ON dt_system_learnings FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Service write dt_client_files" ON dt_client_files FOR ALL USING (true) WITH CHECK (true);
