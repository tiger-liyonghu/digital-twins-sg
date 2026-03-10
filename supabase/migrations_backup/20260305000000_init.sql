-- ============================================================
-- Singapore Digital Twin — Database Schema
-- Supabase (PostgreSQL)
-- ============================================================

-- Enable UUID generation
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ============================================================
-- CORE TABLES
-- ============================================================

-- Agents (20,000 synthetic persons)
CREATE TABLE IF NOT EXISTS agents (
    agent_id TEXT PRIMARY KEY,          -- A00000..A19999
    age INTEGER NOT NULL CHECK (age >= 0 AND age <= 100),
    age_group TEXT,
    gender TEXT NOT NULL CHECK (gender IN ('M', 'F')),
    ethnicity TEXT NOT NULL CHECK (ethnicity IN ('Chinese', 'Malay', 'Indian', 'Others')),
    residency_status TEXT NOT NULL CHECK (residency_status IN ('Citizen', 'PR', 'EP', 'SP', 'WP', 'FDW', 'DP', 'STP')),
    planning_area TEXT NOT NULL,

    -- Education & Career
    education_level TEXT,
    occupation TEXT DEFAULT '',
    industry TEXT DEFAULT '',
    employer_type TEXT DEFAULT '',
    monthly_income INTEGER DEFAULT 0,

    -- Family
    marital_status TEXT DEFAULT 'Single',
    household_id TEXT,
    household_role TEXT DEFAULT '',
    num_children INTEGER DEFAULT 0,

    -- Housing & Finance
    housing_type TEXT,
    housing_value INTEGER DEFAULT 0,
    monthly_savings INTEGER DEFAULT 0,
    total_debt INTEGER DEFAULT 0,

    -- CPF
    cpf_oa INTEGER DEFAULT 0,
    cpf_sa INTEGER DEFAULT 0,
    cpf_ma INTEGER DEFAULT 0,
    cpf_ra INTEGER DEFAULT 0,

    -- Health
    health_status TEXT DEFAULT 'Healthy',
    chronic_conditions JSONB DEFAULT '[]',
    bmi_category TEXT DEFAULT 'normal',
    smoking BOOLEAN DEFAULT FALSE,

    -- NS
    ns_status TEXT DEFAULT 'Not_Applicable',

    -- Transport
    commute_mode TEXT DEFAULT 'MRT',
    has_vehicle BOOLEAN DEFAULT FALSE,

    -- Personality (Big Five, 1-5)
    big5_o NUMERIC(3,2) DEFAULT 3.0,
    big5_c NUMERIC(3,2) DEFAULT 3.0,
    big5_e NUMERIC(3,2) DEFAULT 3.0,
    big5_a NUMERIC(3,2) DEFAULT 3.0,
    big5_n NUMERIC(3,2) DEFAULT 3.0,

    -- Attitudes (1-5)
    risk_appetite NUMERIC(3,2) DEFAULT 3.0,
    political_leaning NUMERIC(3,2) DEFAULT 3.0,
    social_trust NUMERIC(3,2) DEFAULT 3.0,
    religious_devotion NUMERIC(3,2) DEFAULT 3.0,

    -- Life state
    life_phase TEXT DEFAULT 'establishment',
    agent_type TEXT DEFAULT 'active' CHECK (agent_type IN ('passive', 'semi_active', 'active')),
    is_alive BOOLEAN DEFAULT TRUE,

    -- Metadata
    generation TEXT DEFAULT '3rd+',
    years_in_sg INTEGER DEFAULT 0,
    religion TEXT DEFAULT 'None',
    primary_language TEXT DEFAULT 'English',

    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Households
CREATE TABLE IF NOT EXISTS households (
    household_id TEXT PRIMARY KEY,
    planning_area TEXT,
    housing_type TEXT,
    household_size INTEGER DEFAULT 1,
    household_income INTEGER DEFAULT 0,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- SIMULATION STATE
-- ============================================================

-- World state snapshots (weekly full + daily deltas)
CREATE TABLE IF NOT EXISTS world_states (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    tick INTEGER NOT NULL,
    sim_date DATE NOT NULL,
    state_type TEXT NOT NULL CHECK (state_type IN ('full', 'delta')),

    -- Macro indicators
    gdp_growth NUMERIC(5,2),
    unemployment_rate NUMERIC(5,2),
    inflation_rate NUMERIC(5,2),
    interest_rate NUMERIC(5,2),
    hdb_resale_index NUMERIC(8,2),
    sti_index NUMERIC(8,2),

    -- Population aggregates
    total_agents INTEGER,
    active_agents INTEGER,
    mean_happiness NUMERIC(3,2),
    mean_income NUMERIC(10,2),

    -- Event summary
    events_triggered INTEGER DEFAULT 0,
    llm_calls_made INTEGER DEFAULT 0,

    -- Full state snapshot (JSONB, only for state_type='full')
    snapshot JSONB,

    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_world_states_tick ON world_states(tick);
CREATE INDEX idx_world_states_date ON world_states(sim_date);

-- Agent state changes (delta log)
CREATE TABLE IF NOT EXISTS agent_deltas (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    tick INTEGER NOT NULL,
    agent_id TEXT NOT NULL REFERENCES agents(agent_id),
    field_name TEXT NOT NULL,
    old_value TEXT,
    new_value TEXT,
    reason TEXT,              -- what caused the change
    event_id UUID,            -- link to triggering event
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_agent_deltas_tick ON agent_deltas(tick);
CREATE INDEX idx_agent_deltas_agent ON agent_deltas(agent_id);

-- ============================================================
-- EVENT SYSTEM
-- ============================================================

-- Events (external + internal)
CREATE TABLE IF NOT EXISTS events (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    tick INTEGER NOT NULL,
    sim_date DATE NOT NULL,
    event_type TEXT NOT NULL,          -- 'macro', 'policy', 'news', 'personal', 'market'
    source TEXT,                        -- 'cna_rss', 'reddit', 'serpapi', 'rule_engine', 'llm'
    title TEXT NOT NULL,
    description TEXT,

    -- Impact vector (6 dimensions, -5 to +5)
    impact_biological NUMERIC(3,1) DEFAULT 0,
    impact_psychological NUMERIC(3,1) DEFAULT 0,
    impact_social NUMERIC(3,1) DEFAULT 0,
    impact_economic NUMERIC(3,1) DEFAULT 0,
    impact_cognitive NUMERIC(3,1) DEFAULT 0,
    impact_spiritual NUMERIC(3,1) DEFAULT 0,

    -- Targeting
    target_filter JSONB,               -- which agents are affected
    agents_affected INTEGER DEFAULT 0,

    raw_data JSONB,                    -- original event data
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_events_tick ON events(tick);
CREATE INDEX idx_events_type ON events(event_type);

-- Agent reactions to events
CREATE TABLE IF NOT EXISTS agent_reactions (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    tick INTEGER NOT NULL,
    event_id UUID REFERENCES events(id),
    agent_id TEXT NOT NULL REFERENCES agents(agent_id),

    decision_layer TEXT NOT NULL CHECK (decision_layer IN ('rule', 'probability', 'llm')),
    action TEXT NOT NULL,
    reasoning TEXT,                     -- LLM explanation if applicable

    -- Emotion change
    emotion_before JSONB,
    emotion_after JSONB,

    -- Cost tracking
    llm_model TEXT,
    llm_tokens INTEGER,
    llm_cost_usd NUMERIC(6,4),

    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_reactions_tick ON agent_reactions(tick);
CREATE INDEX idx_reactions_agent ON agent_reactions(agent_id);

-- ============================================================
-- TICK MANAGEMENT
-- ============================================================

-- Simulation ticks
CREATE TABLE IF NOT EXISTS ticks (
    tick INTEGER PRIMARY KEY,
    sim_date DATE NOT NULL,
    status TEXT DEFAULT 'pending' CHECK (status IN ('pending', 'running', 'completed', 'failed')),

    agents_activated INTEGER DEFAULT 0,
    events_processed INTEGER DEFAULT 0,
    rule_decisions INTEGER DEFAULT 0,
    prob_decisions INTEGER DEFAULT 0,
    llm_decisions INTEGER DEFAULT 0,

    total_llm_cost_usd NUMERIC(8,4) DEFAULT 0,
    duration_seconds NUMERIC(8,2),

    started_at TIMESTAMPTZ,
    completed_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- WHAT-IF BRANCHES
-- ============================================================

CREATE TABLE IF NOT EXISTS branches (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    name TEXT NOT NULL,
    description TEXT,
    parent_branch_id UUID REFERENCES branches(id),
    fork_tick INTEGER NOT NULL,          -- tick where branch diverges

    -- Policy/scenario parameters
    scenario JSONB NOT NULL,

    status TEXT DEFAULT 'active' CHECK (status IN ('active', 'completed', 'archived')),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- VERTICAL: INSURANCE
-- ============================================================

CREATE TABLE IF NOT EXISTS insurance_policies (
    id UUID DEFAULT uuid_generate_v4() PRIMARY KEY,
    agent_id TEXT NOT NULL REFERENCES agents(agent_id),

    product_type TEXT NOT NULL,           -- 'life', 'health', 'motor', 'home', 'travel'
    product_name TEXT,
    insurer TEXT,

    premium_monthly NUMERIC(10,2),
    sum_assured NUMERIC(12,2),
    coverage_start DATE,
    coverage_end DATE,

    status TEXT DEFAULT 'active',
    lapse_risk NUMERIC(3,2) DEFAULT 0,

    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_insurance_agent ON insurance_policies(agent_id);

-- ============================================================
-- ROW LEVEL SECURITY (basic)
-- ============================================================

ALTER TABLE agents ENABLE ROW LEVEL SECURITY;
ALTER TABLE world_states ENABLE ROW LEVEL SECURITY;
ALTER TABLE events ENABLE ROW LEVEL SECURITY;

-- Public read access for now (will tighten later)
CREATE POLICY "Public read agents" ON agents FOR SELECT USING (true);
CREATE POLICY "Public read world_states" ON world_states FOR SELECT USING (true);
CREATE POLICY "Public read events" ON events FOR SELECT USING (true);
