-- Pickaxe Tax contribution store (Cloudflare D1). Idempotent.
CREATE TABLE IF NOT EXISTS contributions (
  seq INTEGER PRIMARY KEY AUTOINCREMENT,
  id TEXT UNIQUE NOT NULL,
  day TEXT NOT NULL,               -- YYYY-MM-DD only, no time
  kind TEXT NOT NULL,              -- skeleton | ledger | agent
  payload TEXT NOT NULL,           -- validated JSON, labels removed
  labels TEXT,                     -- JSON array, opt-in topic labels
  token_hash TEXT NOT NULL         -- sha256 of the delete token
);
CREATE INDEX IF NOT EXISTS contributions_kind ON contributions(kind);
CREATE TABLE IF NOT EXISTS used_pow (seed TEXT PRIMARY KEY, exp INTEGER NOT NULL);
CREATE TABLE IF NOT EXISTS rate (key TEXT PRIMARY KEY, day TEXT NOT NULL, n INTEGER NOT NULL);
CREATE TABLE IF NOT EXISTS meta (key TEXT PRIMARY KEY, value TEXT NOT NULL);
