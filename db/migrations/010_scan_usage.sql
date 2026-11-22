-- Peak and average CPU and memory per scan, sampled by scripts/sample_usage.py while the scan ran.
ALTER TABLE scans ADD COLUMN IF NOT EXISTS usage jsonb;
