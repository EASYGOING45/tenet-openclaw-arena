const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:3000'

export interface Model {
  id: string
  name: string
  provider: string
  license_type: string
  input_price: number | null
  output_price: number | null
  context_length: number | null
  is_codex_harness: boolean
}

export interface Task {
  id: string
  name: string
  category: string
  difficulty: string
  description: string
  scoring_criteria: Record<string, number>
}

export interface Result {
  run_id: string
  model_id: string
  task_id: string
  score: number
  failure_label: string
  transcript: string
  latency_ms: number
  created_at: string
}

export interface LeaderboardEntry {
  rank: number
  model_id: string
  model_name: string
  provider: string
  license_type: string
  score: number
  vote_count: number
  rank_spread: string
  input_price: number | null
  output_price: number | null
  context_length: number | null
  tasks: { task_id: string; score: number; failure_label: string }[]
}

export const api = {
  async getModels(): Promise<Model[]> {
    const res = await fetch(`${API_BASE}/api/models`)
    const data = await res.json()
    return data.models
  },
  async getTasks(): Promise<Task[]> {
    const res = await fetch(`${API_BASE}/api/tasks`)
    const data = await res.json()
    return data.tasks
  },
  async getResults(params?: { run_id?: string; model_id?: string; task_id?: string; limit?: number }): Promise<Result[]> {
    const sp = new URLSearchParams(params as any)
    const res = await fetch(`${API_BASE}/api/results?${sp}`)
    const data = await res.json()
    return data.results
  },
  async getLeaderboard(): Promise<LeaderboardEntry[]> {
    const res = await fetch(`${API_BASE}/api/leaderboard`)
    const data = await res.json()
    return data.leaderboard
  },
}
