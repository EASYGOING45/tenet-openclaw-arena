export interface ModelIdentity {
  slug: string
  name: string
  provider?: string
}

export interface ScoreBreakdown {
  total?: number
  verdict?: string
  dimensions?: Record<string, number>
}

export interface ScoreboardModelRow {
  model: ModelIdentity
  runs: number
  passRate: number
  averageScore: number
  dimensionAverages: Record<string, number>
}

export interface ArenaRun {
  runId: string
  model: ModelIdentity
  taskId: string
  taskTitle?: string
  category?: string
  finalText?: string
  transcriptPreview?: string
  score: ScoreBreakdown
  failureTags: string[]
  finishedAt?: string
}

export interface SiteData {
  generatedAt: string | null
  scoreboard: {
    models: ScoreboardModelRow[]
  }
  runs: ArenaRun[]
}
