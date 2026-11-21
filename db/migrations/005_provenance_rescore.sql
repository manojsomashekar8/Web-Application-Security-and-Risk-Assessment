-- Per-finding enrichment provenance and n/a flag; per-scan stage timings, top-10 overlap and stored raw alerts
-- (raw alerts make a re-score possible without a new scan).
ALTER TABLE findings ADD COLUMN IF NOT EXISTS provenance jsonb NOT NULL DEFAULT '{}'::jsonb;
ALTER TABLE findings ADD COLUMN IF NOT EXISTS enrichment_na boolean NOT NULL DEFAULT false;
ALTER TABLE scans ADD COLUMN IF NOT EXISTS stage_seconds jsonb;
ALTER TABLE scans ADD COLUMN IF NOT EXISTS top10_overlap double precision;
ALTER TABLE scans ADD COLUMN IF NOT EXISTS raw_alerts jsonb;
