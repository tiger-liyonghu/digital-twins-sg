-- Society Mode: add sim_mode, campaign, num_days to simulation_jobs
ALTER TABLE simulation_jobs ADD COLUMN IF NOT EXISTS sim_mode TEXT DEFAULT 'survey';
ALTER TABLE simulation_jobs ADD COLUMN IF NOT EXISTS campaign JSONB DEFAULT '{}'::jsonb;
ALTER TABLE simulation_jobs ADD COLUMN IF NOT EXISTS num_days INTEGER DEFAULT 7;
