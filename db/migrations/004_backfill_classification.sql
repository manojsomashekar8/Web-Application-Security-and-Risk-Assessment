-- Rows stored before classification existed got the default 'vulnerability'.
-- Recompute from stored ZAP risk and confidence, using the same rules as src/triage.py classify().
UPDATE findings SET classification = CASE
    WHEN zap_confidence = 'False Positive' THEN 'excluded'
    WHEN zap_risk = 'Informational' THEN 'informational'
    WHEN zap_confidence = 'Low' THEN 'potential'
    ELSE 'vulnerability'
END;
