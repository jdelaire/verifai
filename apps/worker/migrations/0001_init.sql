-- VerifAI D1 schema – initial migration
-- Applies to: verifai-db

CREATE TABLE IF NOT EXISTS jobs (
  id TEXT PRIMARY KEY,
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  status TEXT NOT NULL DEFAULT 'pending' CHECK (status IN ('pending', 'processing', 'done', 'failed')),
  object_key TEXT NOT NULL,
  file_hash TEXT,
  error_message TEXT,
  expires_at TEXT NOT NULL,
  ip_address TEXT
);

CREATE INDEX idx_jobs_status ON jobs(status);
CREATE INDEX idx_jobs_expires_at ON jobs(expires_at);
CREATE INDEX idx_jobs_file_hash ON jobs(file_hash);

CREATE TABLE IF NOT EXISTS reports (
  job_id TEXT PRIMARY KEY REFERENCES jobs(id),
  created_at TEXT NOT NULL DEFAULT (datetime('now')),
  ai_likelihood INTEGER,
  confidence TEXT CHECK (confidence IN ('high', 'medium', 'low')),
  verdict_text TEXT,
  evidence_json TEXT NOT NULL DEFAULT '[]',
  metadata_json TEXT NOT NULL DEFAULT '{}',
  provenance_json TEXT NOT NULL DEFAULT '{}',
  limitations_json TEXT NOT NULL DEFAULT '[]'
);

CREATE TABLE IF NOT EXISTS rate_limits (
  ip_address TEXT NOT NULL,
  window_date TEXT NOT NULL,
  request_count INTEGER NOT NULL DEFAULT 0,
  last_request_at TEXT NOT NULL DEFAULT (datetime('now')),
  PRIMARY KEY (ip_address, window_date)
);
