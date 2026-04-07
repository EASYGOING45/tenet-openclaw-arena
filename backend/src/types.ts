export interface Model {
  id: string;
  name: string;
  provider: string;
  license_type: string;
  input_price: number | null;
  output_price: number | null;
  context_length: number | null;
  is_codex_harness: boolean;
}

export interface Task {
  id: string;
  name: string;
  category: string;
  difficulty: string;
  description: string;
  scoring_criteria: Record<string, number>;
}

export interface Run {
  run_id: string;
  model_id: string;
  task_id: string;
  score: number;
  failure_label: string;
  transcript: string;
  latency_ms: number | null;
  created_at: string;
}

export interface LeaderboardEntry {
  rank: number;
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
    score: number;
    failure_label: string;
  }>;
}
