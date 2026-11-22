-- The ZAP version that ran each scan (read from ZAP's version API when the scan starts).
ALTER TABLE scans ADD COLUMN IF NOT EXISTS zap_version text;
