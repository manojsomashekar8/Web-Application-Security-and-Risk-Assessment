-- KEV is n/a (NULL) when a finding has no mapped CVE, so the column must accept NULL (decision D54).
ALTER TABLE findings ALTER COLUMN kev DROP NOT NULL;
