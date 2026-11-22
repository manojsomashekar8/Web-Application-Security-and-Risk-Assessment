-- Number of URLs in ZAP's site tree after each spider stage (cumulative), so a scan shows whether a spider reached the app.
ALTER TABLE scans ADD COLUMN IF NOT EXISTS stage_urls jsonb;
