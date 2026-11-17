CREATE TABLE IF NOT EXISTS validation_results (
    id           SERIAL PRIMARY KEY,
    target       TEXT NOT NULL,
    known_vulns  INTEGER NOT NULL,
    detected     INTEGER NOT NULL,
    true_pos     INTEGER NOT NULL,
    precision    DOUBLE PRECISION NOT NULL,
    recall       DOUBLE PRECISION NOT NULL,
    run_date     DATE NOT NULL DEFAULT CURRENT_DATE
);
