-- Performance indexes for agents table
-- Run via Supabase SQL Editor: https://supabase.com/dashboard/project/utabzpkafzahqjqlvywo/sql

-- Composite index for stratified sampling (age_group + gender + residency)
CREATE INDEX IF NOT EXISTS idx_agents_strata
ON agents (age_group, gender, residency_status);

-- Single-column indexes for simple queries
CREATE INDEX IF NOT EXISTS idx_agents_age_group ON agents (age_group);
CREATE INDEX IF NOT EXISTS idx_agents_gender ON agents (gender);
