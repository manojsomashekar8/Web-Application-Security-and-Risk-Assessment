-- Classification (vulnerability / potential / informational / excluded), raw alert count, and fingerprint.
ALTER TABLE findings ADD COLUMN IF NOT EXISTS classification text NOT NULL DEFAULT 'vulnerability';
ALTER TABLE findings ADD COLUMN IF NOT EXISTS occurrences integer NOT NULL DEFAULT 1;
ALTER TABLE findings ADD COLUMN IF NOT EXISTS fingerprint text NOT NULL DEFAULT '';
