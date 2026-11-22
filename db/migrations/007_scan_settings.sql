-- Exact settings each scan used (profile name plus every value), stored with the scan.
ALTER TABLE scans ADD COLUMN IF NOT EXISTS settings jsonb;
