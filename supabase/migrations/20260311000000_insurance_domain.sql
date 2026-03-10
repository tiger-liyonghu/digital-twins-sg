-- ============================================================
-- Insurance Domain Layer (P0)
-- Domain Layer pattern: versioned, independent, JOINable
-- ============================================================

-- 1. Domain Versions — generic registry for all domain layers
CREATE TABLE IF NOT EXISTS domain_versions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  domain TEXT NOT NULL,                 -- 'insurance' | 'financial' | 'transport' | ...
  version TEXT NOT NULL,                -- 'v1.0', 'v1.1'
  is_active BOOLEAN DEFAULT false,
  status TEXT DEFAULT 'draft'
    CHECK (status IN ('draft','generating','validating','active','archived')),
  description TEXT,

  -- Provenance
  research_doc TEXT,                    -- e.g. 'insurance_profile_research_v1.md'
  data_sources JSONB DEFAULT '{}',      -- {"PGS_2022": ["T58","T66","T68","T69"], ...}
  generation_params JSONB DEFAULT '{}', -- Full CPT snapshot for reproducibility
  cpt_file TEXT,                        -- e.g. 'data/cpt/insurance_v1.yaml'

  -- Stats
  agent_count INTEGER DEFAULT 0,
  validation_result JSONB DEFAULT '{}', -- Marginal checks: {"ip_rate": 0.71, "pass": true, ...}

  created_at TIMESTAMPTZ DEFAULT now(),
  activated_at TIMESTAMPTZ,
  UNIQUE(domain, version)
);

-- Ensure at most one active version per domain
CREATE UNIQUE INDEX idx_one_active_per_domain
  ON domain_versions(domain) WHERE is_active = true;

-- 2. Agent Insurance — the insurance domain data
CREATE TABLE IF NOT EXISTS agent_insurance (
  agent_id TEXT NOT NULL REFERENCES agents(agent_id) ON DELETE CASCADE,
  version_id UUID NOT NULL REFERENCES domain_versions(id) ON DELETE CASCADE,

  -- ===== Health Insurance =====
  has_medishield_life BOOLEAN NOT NULL DEFAULT true,
  has_ip BOOLEAN NOT NULL DEFAULT false,
  ip_tier TEXT CHECK (ip_tier IS NULL OR ip_tier IN ('private','A','B1','standard')),
  has_rider BOOLEAN DEFAULT false,
  ip_insurer TEXT,                      -- AIA / GE / Prudential / NTUC / Singlife / Raffles

  -- ===== Life Insurance =====
  has_term_life BOOLEAN NOT NULL DEFAULT false,
  term_life_coverage INT DEFAULT 0,     -- S$
  has_whole_life BOOLEAN NOT NULL DEFAULT false,

  -- ===== Critical Illness =====
  has_ci BOOLEAN NOT NULL DEFAULT false,
  ci_coverage INT DEFAULT 0,            -- S$

  -- ===== Financial =====
  monthly_insurance_spend INT DEFAULT 0,  -- S$/month
  medisave_balance INT DEFAULT 0,         -- S$

  -- ===== Behavioral =====
  insurance_attitude TEXT CHECK (insurance_attitude IS NULL OR insurance_attitude IN
    ('proactive','adequate','passive','resistant','unaware')),
  protection_gap_awareness TEXT CHECK (protection_gap_awareness IS NULL OR protection_gap_awareness IN
    ('aware_acting','aware_inactive','unaware','overconfident')),
  preferred_channel TEXT CHECK (preferred_channel IS NULL OR preferred_channel IN
    ('agent_tied','ifa','online','bank','employer')),
  last_life_event_trigger TEXT,

  -- ===== Health Utilization =====
  annual_hospitalization_freq REAL DEFAULT 0.0,

  created_at TIMESTAMPTZ DEFAULT now(),
  PRIMARY KEY (agent_id, version_id)
);

-- Query indexes: active version + common filters
CREATE INDEX idx_ins_version ON agent_insurance(version_id);
CREATE INDEX idx_ins_has_ip ON agent_insurance(version_id, has_ip);
CREATE INDEX idx_ins_ip_tier ON agent_insurance(version_id, ip_tier) WHERE ip_tier IS NOT NULL;
CREATE INDEX idx_ins_has_term ON agent_insurance(version_id, has_term_life) WHERE has_term_life = true;
CREATE INDEX idx_ins_has_ci ON agent_insurance(version_id, has_ci) WHERE has_ci = true;
CREATE INDEX idx_ins_attitude ON agent_insurance(version_id, insurance_attitude) WHERE insurance_attitude IS NOT NULL;

-- 3. Convenience view: agents + active insurance (for sampling JOINs)
CREATE OR REPLACE VIEW agents_with_insurance AS
SELECT
  a.*,
  i.has_medishield_life,
  i.has_ip, i.ip_tier, i.has_rider, i.ip_insurer,
  i.has_term_life, i.term_life_coverage, i.has_whole_life,
  i.has_ci, i.ci_coverage,
  i.monthly_insurance_spend, i.medisave_balance,
  i.insurance_attitude, i.protection_gap_awareness,
  i.preferred_channel, i.last_life_event_trigger,
  i.annual_hospitalization_freq
FROM agents a
LEFT JOIN agent_insurance i ON a.agent_id = i.agent_id
LEFT JOIN domain_versions dv ON i.version_id = dv.id
  AND dv.domain = 'insurance' AND dv.is_active = true;

-- 4. RLS
ALTER TABLE domain_versions ENABLE ROW LEVEL SECURITY;
ALTER TABLE agent_insurance ENABLE ROW LEVEL SECURITY;

CREATE POLICY "domain_versions_public_read" ON domain_versions
  FOR SELECT USING (true);
CREATE POLICY "domain_versions_service_write" ON domain_versions
  FOR ALL USING (true) WITH CHECK (true);

CREATE POLICY "agent_insurance_public_read" ON agent_insurance
  FOR SELECT USING (true);
CREATE POLICY "agent_insurance_service_write" ON agent_insurance
  FOR ALL USING (true) WITH CHECK (true);

-- 5. Add domains column to sophie_topics for auto-domain-awareness
ALTER TABLE sophie_topics ADD COLUMN IF NOT EXISTS domains TEXT[] DEFAULT '{}';

-- Tag finance/insurance topics
UPDATE sophie_topics
SET domains = ARRAY['insurance']
WHERE industry_id = 'finance'
  AND (name ILIKE '%insurance%' OR name ILIKE '%IP%' OR name ILIKE '%shield%'
       OR name ILIKE '%protection%' OR name ILIKE '%premium%'
       OR scenario_type = 'product_pricing');
