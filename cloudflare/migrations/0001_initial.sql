CREATE TABLE IF NOT EXISTS task_attempts (
  owner_id TEXT NOT NULL,
  id TEXT NOT NULL,
  task_id TEXT NOT NULL,
  concept_id TEXT NOT NULL,
  response TEXT NOT NULL,
  code TEXT NOT NULL,
  stdin TEXT NOT NULL,
  passed INTEGER NOT NULL,
  assisted INTEGER NOT NULL,
  assessment TEXT NOT NULL,
  result_json TEXT NOT NULL,
  created_at TEXT NOT NULL,
  next_review_at TEXT NOT NULL,
  request_hash TEXT NOT NULL,
  PRIMARY KEY (owner_id, id)
);
CREATE INDEX IF NOT EXISTS idx_task_attempts_owner_task_time
  ON task_attempts(owner_id, task_id, created_at DESC, id DESC);

CREATE TABLE IF NOT EXISTS task_drafts (
  owner_id TEXT NOT NULL,
  task_id TEXT NOT NULL,
  payload TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  PRIMARY KEY (owner_id, task_id)
);

CREATE TABLE IF NOT EXISTS task_draft_generations (
  owner_id TEXT NOT NULL,
  task_id TEXT NOT NULL,
  generation INTEGER NOT NULL,
  PRIMARY KEY (owner_id, task_id)
);

CREATE TABLE IF NOT EXISTS projects (
  owner_id TEXT NOT NULL,
  id TEXT NOT NULL,
  title TEXT NOT NULL,
  description TEXT NOT NULL DEFAULT '',
  code TEXT NOT NULL DEFAULT '',
  created_at TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  PRIMARY KEY (owner_id, id)
);
CREATE INDEX IF NOT EXISTS idx_projects_owner_updated
  ON projects(owner_id, updated_at DESC);

CREATE TABLE IF NOT EXISTS project_files (
  owner_id TEXT NOT NULL,
  project_id TEXT NOT NULL,
  name TEXT NOT NULL,
  content TEXT NOT NULL,
  updated_at TEXT NOT NULL,
  PRIMARY KEY (owner_id, project_id, name),
  FOREIGN KEY (owner_id, project_id) REFERENCES projects(owner_id, id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS execution_quota (
  month TEXT PRIMARY KEY,
  count INTEGER NOT NULL DEFAULT 0
);
