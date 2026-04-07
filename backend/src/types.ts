export interface Agent {
  agent_id: string;
  model_id: string;
  provider: string;
  model_name: string;
  license_type: string;
  input_price: number | null;
  output_price: number | null;
  context_length: number | null;
  is_active: boolean;
}

export interface Task {
  task_id: string;
  title: string;
  capability: string;
  difficulty: string;
  description: string;
  yaml_path: string;
  tags: string[];
  timeout_seconds: number;
  scoring_rules: ScoringRule[];
  pass_threshold: number;
  fail_threshold: number;
  is_active: boolean;
}

export interface ScoringRule {
  event: string;
  condition?: string;
  score: number;
  note?: string;
}

export interface Run {
  run_id: string;
  run_group: string;
  agent_id: string;
  task_id: string;
  score: number;
  verdict: "PASS" | "PARTIAL" | "FAIL" | "ERROR";
  duration_ms: number | null;
  events: BenchmarkEvent[];
  error: string | null;
  created_at: string;
}

export interface BenchmarkEvent {
  type: string;
  line?: string;
  tool?: string;
  skill?: string;
  source?: string;
  content_preview?: string;
  parser?: string;
}

export interface LeaderboardEntry {
  rank: number;
  agent_id: string;
  model_id: string;
  model_name: string;
  provider: string;
  license_type: string;
  score: number;
  vote_count: number;
  rank_spread: string;
  input_price: number | null;
  output_price: number | null;
  context_length: number | null;
  tasks: Array<{
    task_id: string;
    title: string;
    capability: string;
    score: number;
    verdict: string;
  }>;
}
