-- Digital Twin Studio — Sophie Cloud Tables
-- Run this in your Supabase SQL editor

-- Sessions
CREATE TABLE IF NOT EXISTS dt_sessions (
  id TEXT PRIMARY KEY,
  created_at TIMESTAMPTZ DEFAULT now(),
  updated_at TIMESTAMPTZ DEFAULT now(),
  scenario_id TEXT,
  status TEXT DEFAULT 'active' CHECK (status IN ('active','completed','archived')),
  title TEXT,
  metadata JSONB DEFAULT '{}'
);

-- Conversations (every message between Sophie and client)
CREATE TABLE IF NOT EXISTS dt_conversations (
  id BIGSERIAL PRIMARY KEY,
  session_id TEXT REFERENCES dt_sessions(id),
  created_at TIMESTAMPTZ DEFAULT now(),
  role TEXT NOT NULL CHECK (role IN ('sophie','client','system')),
  content TEXT NOT NULL,
  phase TEXT,
  metadata JSONB DEFAULT '{}'
);
CREATE INDEX IF NOT EXISTS idx_conv_session ON dt_conversations(session_id);

-- Survey jobs
CREATE TABLE IF NOT EXISTS dt_survey_jobs (
  id TEXT PRIMARY KEY,
  session_id TEXT REFERENCES dt_sessions(id),
  created_at TIMESTAMPTZ DEFAULT now(),
  job_type TEXT CHECK (job_type IN ('test_run','full_run')),
  params JSONB,
  status TEXT DEFAULT 'queued',
  progress INT DEFAULT 0,
  total INT DEFAULT 0,
  started_at TIMESTAMPTZ,
  completed_at TIMESTAMPTZ,
  error_count INT DEFAULT 0,
  quality_summary JSONB
);

-- Survey results
CREATE TABLE IF NOT EXISTS dt_survey_results (
  id BIGSERIAL PRIMARY KEY,
  job_id TEXT REFERENCES dt_survey_jobs(id),
  session_id TEXT REFERENCES dt_sessions(id),
  created_at TIMESTAMPTZ DEFAULT now(),
  result_data JSONB,
  analysis TEXT
);

-- Error logs (system evolution)
CREATE TABLE IF NOT EXISTS dt_error_logs (
  id BIGSERIAL PRIMARY KEY,
  created_at TIMESTAMPTZ DEFAULT now(),
  session_id TEXT REFERENCES dt_sessions(id),
  job_id TEXT,
  agent_id TEXT,
  category TEXT NOT NULL,
  severity TEXT DEFAULT 'info' CHECK (severity IN ('critical','warning','info')),
  detail JSONB,
  resolution TEXT,
  resolved_at TIMESTAMPTZ
);
CREATE INDEX IF NOT EXISTS idx_errors_session ON dt_error_logs(session_id);
CREATE INDEX IF NOT EXISTS idx_errors_category ON dt_error_logs(category);

-- Quality incidents
CREATE TABLE IF NOT EXISTS dt_quality_incidents (
  id BIGSERIAL PRIMARY KEY,
  created_at TIMESTAMPTZ DEFAULT now(),
  job_id TEXT,
  agent_id TEXT,
  issue_type TEXT,
  prompt_used TEXT,
  raw_response TEXT,
  reward_score FLOAT,
  was_excluded BOOLEAN DEFAULT false,
  replacement_agent_id TEXT
);

-- System learnings (auto-evolution)
CREATE TABLE IF NOT EXISTS dt_system_learnings (
  id BIGSERIAL PRIMARY KEY,
  created_at TIMESTAMPTZ DEFAULT now(),
  source_incident_ids TEXT[],
  learning_type TEXT,
  description TEXT,
  before_state TEXT,
  after_state TEXT,
  applied_at TIMESTAMPTZ,
  applied_by TEXT DEFAULT 'auto'
);

-- Client files (PDF, CSV downloads)
CREATE TABLE IF NOT EXISTS dt_client_files (
  id BIGSERIAL PRIMARY KEY,
  session_id TEXT REFERENCES dt_sessions(id),
  created_at TIMESTAMPTZ DEFAULT now(),
  file_type TEXT,
  file_name TEXT,
  storage_path TEXT,
  file_size INT,
  downloaded_at TIMESTAMPTZ,
  download_count INT DEFAULT 0
);

-- Enable RLS but allow all for now (anon key)
ALTER TABLE dt_sessions ENABLE ROW LEVEL SECURITY;
ALTER TABLE dt_conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE dt_survey_jobs ENABLE ROW LEVEL SECURITY;
ALTER TABLE dt_survey_results ENABLE ROW LEVEL SECURITY;
ALTER TABLE dt_error_logs ENABLE ROW LEVEL SECURITY;
ALTER TABLE dt_quality_incidents ENABLE ROW LEVEL SECURITY;
ALTER TABLE dt_system_learnings ENABLE ROW LEVEL SECURITY;
ALTER TABLE dt_client_files ENABLE ROW LEVEL SECURITY;

-- Allow anon access (for demo; add auth later)
CREATE POLICY "anon_all" ON dt_sessions FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "anon_all" ON dt_conversations FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "anon_all" ON dt_survey_jobs FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "anon_all" ON dt_survey_results FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "anon_all" ON dt_error_logs FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "anon_all" ON dt_quality_incidents FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "anon_all" ON dt_system_learnings FOR ALL USING (true) WITH CHECK (true);
CREATE POLICY "anon_all" ON dt_client_files FOR ALL USING (true) WITH CHECK (true);
