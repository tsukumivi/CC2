CREATE TABLE IF NOT EXISTS guest_sessions (
  owner_id TEXT PRIMARY KEY,
  last_seen_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_guest_sessions_last_seen
  ON guest_sessions(last_seen_at);
