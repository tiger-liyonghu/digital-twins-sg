-- ============================================================
-- V3 Schema: 148K NVIDIA-base Digital Twin
-- ============================================================

-- gen_random_uuid() is built-in on Supabase (pgcrypto)

-- ============================================================
-- Drop old V2 tables (data already cleared)
-- ============================================================
DROP TABLE IF EXISTS agent_reactions CASCADE;
DROP TABLE IF EXISTS agent_deltas CASCADE;
DROP TABLE IF EXISTS insurance_policies CASCADE;
DROP TABLE IF EXISTS ticks CASCADE;
DROP TABLE IF EXISTS branches CASCADE;
DROP TABLE IF EXISTS world_states CASCADE;
DROP TABLE IF EXISTS events CASCADE;
DROP TABLE IF EXISTS households CASCADE;
DROP TABLE IF EXISTS agents CASCADE;

-- ============================================================
-- AGENTS (148K NVIDIA base + augmented fields)
-- ============================================================

CREATE TABLE agents (
    agent_id TEXT PRIMARY KEY,              -- NVIDIA uuid (hex, 32 chars)

    -- === NVIDIA native fields ===
    age INTEGER NOT NULL CHECK (age >= 0 AND age <= 120),
    age_group TEXT,
    gender TEXT NOT NULL CHECK (gender IN ('M', 'F')),
    marital_status TEXT DEFAULT 'Single',
    education_level TEXT,
    occupation TEXT DEFAULT '',
    industry TEXT DEFAULT '',
    planning_area TEXT NOT NULL,

    -- NVIDIA narrative fields (rich text for persona prompt)
    persona TEXT DEFAULT '',
    professional_persona TEXT DEFAULT '',
    cultural_background TEXT DEFAULT '',
    sports_persona TEXT DEFAULT '',
    arts_persona TEXT DEFAULT '',
    travel_persona TEXT DEFAULT '',
    culinary_persona TEXT DEFAULT '',
    hobbies_and_interests TEXT DEFAULT '',
    career_goals_and_ambitions TEXT DEFAULT '',
    skills_and_expertise TEXT DEFAULT '',

    -- === CPT-augmented fields ===
    ethnicity TEXT NOT NULL CHECK (ethnicity IN ('Chinese', 'Malay', 'Indian', 'Others')),
    residency_status TEXT NOT NULL DEFAULT 'Citizen'
        CHECK (residency_status IN ('Citizen', 'PR', 'EP', 'SP', 'WP', 'FDW', 'DP', 'STP')),
    monthly_income INTEGER DEFAULT 0,
    income_band TEXT DEFAULT '0',
    housing_type TEXT DEFAULT 'HDB_4',
    health_status TEXT DEFAULT 'Healthy'
        CHECK (health_status IN ('Healthy', 'Chronic_Mild', 'Chronic_Severe', 'Disabled')),

    -- === Personality (Big Five, 1-5) ===
    big5_o NUMERIC(3,2) DEFAULT 3.0,
    big5_c NUMERIC(3,2) DEFAULT 3.0,
    big5_e NUMERIC(3,2) DEFAULT 3.0,
    big5_a NUMERIC(3,2) DEFAULT 3.0,
    big5_n NUMERIC(3,2) DEFAULT 3.0,

    -- === Attitudes (1-5) ===
    risk_appetite NUMERIC(3,2) DEFAULT 3.0,
    political_leaning NUMERIC(3,2) DEFAULT 3.0,
    social_trust NUMERIC(3,2) DEFAULT 3.0,
    religious_devotion NUMERIC(3,2) DEFAULT 3.0,

    -- === Life state ===
    life_phase TEXT DEFAULT 'establishment',
    is_alive BOOLEAN DEFAULT TRUE,

    -- === Data lineage ===
    data_source TEXT DEFAULT 'nvidia_nemotron' CHECK (data_source IN ('nvidia_nemotron', 'synthetic', 'hybrid')),

    -- === Timestamps ===
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_agents_age_group ON agents(age_group);
CREATE INDEX idx_agents_gender ON agents(gender);
CREATE INDEX idx_agents_ethnicity ON agents(ethnicity);
CREATE INDEX idx_agents_planning_area ON agents(planning_area);
CREATE INDEX idx_agents_education ON agents(education_level);
CREATE INDEX idx_agents_income_band ON agents(income_band);
CREATE INDEX idx_agents_housing ON agents(housing_type);

-- ============================================================
-- SIMULATION JOBS (async job queue)
-- ============================================================

CREATE TABLE simulation_jobs (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    question TEXT NOT NULL,
    options JSONB NOT NULL DEFAULT '[]',      -- ["option1", "option2", ...]
    sample_size INTEGER NOT NULL DEFAULT 200,
    filter JSONB DEFAULT '{}',                -- {"age_min": 18, "income_max": 10000}
    strata JSONB DEFAULT '["age_group", "gender", "ethnicity"]',

    status TEXT DEFAULT 'pending'
        CHECK (status IN ('pending', 'running', 'completed', 'failed', 'cancelled')),
    progress NUMERIC(5,2) DEFAULT 0,          -- 0-100%

    -- Results
    result JSONB,                             -- aggregated analysis
    total_agents INTEGER DEFAULT 0,
    total_tokens INTEGER DEFAULT 0,
    total_cost_usd NUMERIC(8,4) DEFAULT 0,

    -- Timing
    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_jobs_status ON simulation_jobs(status);

-- ============================================================
-- AGENT RESPONSES (per-agent per-job)
-- ============================================================

CREATE TABLE agent_responses (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    job_id UUID NOT NULL REFERENCES simulation_jobs(id),
    agent_id TEXT NOT NULL REFERENCES agents(agent_id),

    decision_layer TEXT NOT NULL CHECK (decision_layer IN ('rule', 'probability', 'llm')),
    choice TEXT NOT NULL,                     -- selected option
    reasoning TEXT,                           -- LLM explanation
    confidence NUMERIC(3,2),                  -- 0-1

    -- Cost tracking
    llm_model TEXT,
    tokens_used INTEGER DEFAULT 0,
    cost_usd NUMERIC(6,4) DEFAULT 0,

    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_responses_job ON agent_responses(job_id);
CREATE INDEX idx_responses_agent ON agent_responses(agent_id);

-- ============================================================
-- AGENT MEMORIES
-- ============================================================

CREATE TABLE agent_memories (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    agent_id TEXT NOT NULL REFERENCES agents(agent_id),

    memory_type TEXT NOT NULL DEFAULT 'experience'
        CHECK (memory_type IN (
            'experience', 'decision', 'observation', 'belief_update',
            'compressed', 'interaction', 'reflection'
        )),
    content TEXT NOT NULL,
    importance INTEGER NOT NULL DEFAULT 5 CHECK (importance >= 1 AND importance <= 10),

    -- Traceability
    source_job_id UUID REFERENCES simulation_jobs(id),
    source_event_id UUID,
    source_memory_ids UUID[],                 -- for compressed memories

    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_memories_agent ON agent_memories(agent_id);
CREATE INDEX idx_memories_type ON agent_memories(memory_type);
CREATE INDEX idx_memories_created ON agent_memories(created_at DESC);

-- ============================================================
-- EVENTS
-- ============================================================

CREATE TABLE events (
    id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
    title TEXT NOT NULL,
    description TEXT,
    event_type TEXT NOT NULL DEFAULT 'policy',

    -- Impact vector (6 dimensions, -5 to +5)
    impact_biological NUMERIC(3,1) DEFAULT 0,
    impact_psychological NUMERIC(3,1) DEFAULT 0,
    impact_social NUMERIC(3,1) DEFAULT 0,
    impact_economic NUMERIC(3,1) DEFAULT 0,
    impact_cognitive NUMERIC(3,1) DEFAULT 0,
    impact_spiritual NUMERIC(3,1) DEFAULT 0,

    -- Targeting
    target_filter JSONB,
    agents_affected INTEGER DEFAULT 0,

    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- RUNNER STATUS (heartbeat)
-- ============================================================

CREATE TABLE runner_status (
    runner_id TEXT PRIMARY KEY,
    last_heartbeat TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    active_jobs INTEGER DEFAULT 0,
    version TEXT DEFAULT '1.0'
);

-- ============================================================
-- ROW LEVEL SECURITY
-- ============================================================

ALTER TABLE agents ENABLE ROW LEVEL SECURITY;
ALTER TABLE simulation_jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE agent_responses ENABLE ROW LEVEL SECURITY;
ALTER TABLE agent_memories ENABLE ROW LEVEL SECURITY;
ALTER TABLE events ENABLE ROW LEVEL SECURITY;

-- Public read for agents (no PII)
CREATE POLICY "Public read agents" ON agents FOR SELECT USING (true);
-- Public read for jobs (status only via Realtime, full result via authenticated)
CREATE POLICY "Public read jobs" ON simulation_jobs FOR SELECT USING (true);
CREATE POLICY "Public read responses" ON agent_responses FOR SELECT USING (true);
CREATE POLICY "Public read memories" ON agent_memories FOR SELECT USING (true);
CREATE POLICY "Public read events" ON events FOR SELECT USING (true);

-- Service role can do everything (for Runner)
CREATE POLICY "Service write agents" ON agents FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Service write jobs" ON simulation_jobs FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Service write responses" ON agent_responses FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Service write memories" ON agent_memories FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "Service write events" ON events FOR ALL USING (true) WITH CHECK (true);
