-- P2: Add media consumption and dialect group fields to agents
-- These enable more nuanced simulation for media/information and
-- intra-ethnic cultural differences.

ALTER TABLE agents
  ADD COLUMN IF NOT EXISTS media_diet TEXT,           -- e.g. 'straits_times', 'social_media', 'whatsapp', 'tv', 'chinese_media'
  ADD COLUMN IF NOT EXISTS social_media_usage TEXT,   -- e.g. 'heavy', 'moderate', 'light', 'none'
  ADD COLUMN IF NOT EXISTS dialect_group TEXT;         -- e.g. 'Hokkien', 'Teochew', 'Cantonese', 'Hakka', 'Hainanese' (Chinese ethnicity only)

COMMENT ON COLUMN agents.media_diet IS 'Primary news/information source';
COMMENT ON COLUMN agents.social_media_usage IS 'Social media engagement level';
COMMENT ON COLUMN agents.dialect_group IS 'Chinese dialect group (Census 2020), NULL for non-Chinese';
