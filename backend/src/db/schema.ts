export const CREATE_TABLES_SQL = `
CREATE TABLE IF NOT EXISTS models (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  provider TEXT NOT NULL,
  license_type TEXT NOT NULL,
  input_price REAL,
  output_price REAL,
  context_length INTEGER,
  is_codex_harness INTEGER DEFAULT 0
);

CREATE TABLE IF NOT EXISTS tasks (
  id TEXT PRIMARY KEY,
  name TEXT NOT NULL,
  category TEXT NOT NULL,
  difficulty TEXT NOT NULL,
  description TEXT NOT NULL,
  scoring_criteria TEXT NOT NULL,
  capability TEXT DEFAULT NULL
);

CREATE TABLE IF NOT EXISTS runs (
  run_id TEXT NOT NULL,
  model_id TEXT NOT NULL,
  task_id TEXT NOT NULL,
  score REAL NOT NULL,
  failure_label TEXT NOT NULL,
  transcript TEXT NOT NULL,
  latency_ms INTEGER,
  created_at TEXT NOT NULL,
  PRIMARY KEY (run_id, model_id, task_id)
);
`;
