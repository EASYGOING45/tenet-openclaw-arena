export const CREATE_TABLES_SQL = `
CREATE TABLE IF NOT EXISTS agents (
  agent_id TEXT PRIMARY KEY,
  model_id TEXT NOT NULL,
  provider TEXT NOT NULL,
  model_name TEXT NOT NULL,
  license_type TEXT NOT NULL,
  input_price REAL,
  output_price REAL,
  context_length INTEGER,
  is_active INTEGER DEFAULT 1
);

CREATE TABLE IF NOT EXISTS tasks (
  task_id TEXT PRIMARY KEY,
  title TEXT NOT NULL,
  capability TEXT NOT NULL,
  difficulty TEXT NOT NULL,
  description TEXT NOT NULL,
  yaml_path TEXT NOT NULL,
  tags TEXT NOT NULL,
  timeout_seconds INTEGER DEFAULT 180,
  scoring_rules TEXT NOT NULL,
  pass_threshold REAL DEFAULT 70,
  fail_threshold REAL DEFAULT 40,
  is_active INTEGER DEFAULT 1
);

CREATE TABLE IF NOT EXISTS runs (
  run_id TEXT NOT NULL,
  run_group TEXT NOT NULL,
  agent_id TEXT NOT NULL,
  task_id TEXT NOT NULL,
  score REAL NOT NULL,
  verdict TEXT NOT NULL,
  duration_ms INTEGER,
  events TEXT NOT NULL,
  error TEXT,
  created_at TEXT NOT NULL,
  PRIMARY KEY (run_id, agent_id, task_id)
);

CREATE INDEX IF NOT EXISTS idx_runs_agent ON runs(agent_id);
CREATE INDEX IF NOT EXISTS idx_runs_task ON runs(task_id);
CREATE INDEX IF NOT EXISTS idx_runs_group ON runs(run_group);
`;
