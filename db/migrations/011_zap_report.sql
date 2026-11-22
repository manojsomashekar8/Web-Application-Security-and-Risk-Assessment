-- File name of the ZAP-generated HTML report for this scan (written to results/zap-reports by ZAP).
ALTER TABLE scans ADD COLUMN IF NOT EXISTS zap_report text;
