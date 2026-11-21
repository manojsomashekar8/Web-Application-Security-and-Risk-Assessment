-- Validation v2: pages reached, total and matching alerts, coverage flag, run time, and per-category detection.
-- precision/recall become nullable so a run with too little coverage stores no number (never a fake 0).
ALTER TABLE validation_results ADD COLUMN IF NOT EXISTS pages_reached integer;
ALTER TABLE validation_results ADD COLUMN IF NOT EXISTS total_alerts integer;
ALTER TABLE validation_results ADD COLUMN IF NOT EXISTS matching_alerts integer;
ALTER TABLE validation_results ADD COLUMN IF NOT EXISTS coverage_ok boolean;
ALTER TABLE validation_results ADD COLUMN IF NOT EXISTS run_time timestamptz NOT NULL DEFAULT now();
ALTER TABLE validation_results ALTER COLUMN precision DROP NOT NULL;
ALTER TABLE validation_results ALTER COLUMN recall DROP NOT NULL;

CREATE TABLE IF NOT EXISTS validation_categories (
    id          SERIAL PRIMARY KEY,
    target      TEXT NOT NULL,
    category    TEXT NOT NULL,
    detected    BOOLEAN,            -- NULL when coverage is too low: shown as 'Coverage too low', not as 0
    run_date    DATE NOT NULL DEFAULT CURRENT_DATE,
    run_time    TIMESTAMPTZ NOT NULL DEFAULT now()
);
