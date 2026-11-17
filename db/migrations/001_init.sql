CREATE TABLE IF NOT EXISTS targets (
    id          SERIAL PRIMARY KEY,
    name        TEXT NOT NULL,
    url         TEXT NOT NULL UNIQUE,
    criticality TEXT NOT NULL CHECK (criticality IN ('Low','Medium','High')),
    data_sensitivity TEXT NOT NULL CHECK (data_sensitivity IN ('Low','Medium','High')),
    internet_exposure TEXT NOT NULL CHECK (internet_exposure IN ('Low','Medium','High')),
    business_impact TEXT NOT NULL CHECK (business_impact IN ('Low','Medium','High')),
    created_at  TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE IF NOT EXISTS scans (
    id          SERIAL PRIMARY KEY,
    target_id   INTEGER NOT NULL REFERENCES targets(id) ON DELETE CASCADE,
    status      TEXT NOT NULL CHECK (status IN ('queued','running','done','failed')),
    started_at  TIMESTAMPTZ,
    finished_at TIMESTAMPTZ,
    error       TEXT
);

CREATE TABLE IF NOT EXISTS findings (
    id            SERIAL PRIMARY KEY,
    scan_id       INTEGER NOT NULL REFERENCES scans(id) ON DELETE CASCADE,
    plugin_id     TEXT NOT NULL,
    type          TEXT NOT NULL,
    cwe           INTEGER,
    owasp         TEXT,
    url           TEXT NOT NULL,
    zap_risk      TEXT NOT NULL,
    zap_confidence TEXT NOT NULL,
    cve           TEXT,
    cvss          DOUBLE PRECISION,
    epss          DOUBLE PRECISION,
    kev           BOOLEAN NOT NULL,
    risk          DOUBLE PRECISION NOT NULL,
    weighted_sum  DOUBLE PRECISION NOT NULL,
    cvss_only     DOUBLE PRECISION NOT NULL,
    zap_risk_only DOUBLE PRECISION NOT NULL,
    rank_risk     INTEGER NOT NULL,
    rank_weighted_sum INTEGER NOT NULL,
    rank_cvss_only INTEGER NOT NULL,
    rank_zap_risk_only INTEGER NOT NULL,
    explanation   TEXT NOT NULL,
    factors       JSONB NOT NULL
);
CREATE INDEX IF NOT EXISTS findings_scan_rank ON findings (scan_id, rank_risk);

CREATE TABLE IF NOT EXISTS schema_migrations (version TEXT PRIMARY KEY, applied_at TIMESTAMPTZ NOT NULL DEFAULT now());

-- Read-only role for Grafana. Password is set by make up from .env.
DO $$ BEGIN
    IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'grafana_ro') THEN
        CREATE ROLE grafana_ro LOGIN PASSWORD 'set-by-make-up';
    END IF;
END $$;
GRANT CONNECT ON DATABASE wasra TO grafana_ro;
GRANT USAGE ON SCHEMA public TO grafana_ro;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO grafana_ro;
ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT SELECT ON TABLES TO grafana_ro;
