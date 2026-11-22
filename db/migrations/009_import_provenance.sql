-- Imported scans record where they came from. import_hash makes a second import of the same file a duplicate.
ALTER TABLE scans ADD COLUMN IF NOT EXISTS imported_from text;
ALTER TABLE scans ADD COLUMN IF NOT EXISTS imported_at timestamptz;
ALTER TABLE scans ADD COLUMN IF NOT EXISTS import_hash text;
CREATE UNIQUE INDEX IF NOT EXISTS scans_import_hash_key ON scans (import_hash) WHERE import_hash IS NOT NULL;
