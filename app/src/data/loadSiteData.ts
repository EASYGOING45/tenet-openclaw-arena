import type {
  ArenaRun,
  ModelIdentity,
  ScoreBreakdown,
  ScoreboardModelRow,
  SiteData,
} from '../types'

type RecordLike = Record<string, unknown>

function asRecord(value: unknown): RecordLike {
  return value !== null && typeof value === 'object' ? (value as RecordLike) : {}
}

function toNumber(value: unknown, fallback = 0): number {
  return typeof value === 'number' && Number.isFinite(value) ? value : fallback
}

function slugifyName(value: string): string {
  return value
    .trim()
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '') || 'unknown'
}

function normalizeModelIdentity(value: unknown): ModelIdentity {
  if (typeof value === 'string') {
    return {
      slug: slugifyName(value),
      name: value,
    }
  }

  const record = asRecord(value)
  const name =
    typeof record.name === 'string'
      ? record.name
      : typeof record.slug === 'string'
        ? record.slug
        : 'Unknown model'

  return {
    slug:
      typeof record.slug === 'string' && record.slug.length > 0
        ? record.slug
        : slugifyName(name),
    name,
    provider: typeof record.provider === 'string' ? record.provider : undefined,
  }
}

function normalizeDimensions(value: unknown): Record<string, number> {
  const record = asRecord(value)
  return Object.fromEntries(
    Object.entries(record).map(([key, entry]) => [key, toNumber(entry)]),
  )
}

function normalizeScore(value: unknown): ScoreBreakdown {
  const record = asRecord(value)
  return {
    total: toNumber(record.total, undefined),
    verdict: typeof record.verdict === 'string' ? record.verdict : undefined,
    dimensions: normalizeDimensions(record.dimensions),
  }
}

function normalizeScoreboardModelRow(value: unknown): ScoreboardModelRow {
  const record = asRecord(value)

  return {
    model: normalizeModelIdentity(record.model),
    runs: toNumber(record.runs ?? record.runCount),
    passRate: toNumber(record.pass_rate ?? record.passRate),
    averageScore: toNumber(record.average_score ?? record.averageScore ?? record.averageTotal),
    dimensionAverages: normalizeDimensions(
      record.dimension_averages ?? record.dimensionAverages,
    ),
  }
}

function normalizeRun(value: unknown, index: number): ArenaRun {
  const record = asRecord(value)
  const model = normalizeModelIdentity(record.model)
  const transcript = asRecord(record.transcript)

  return {
    runId:
      typeof record.run_id === 'string'
        ? record.run_id
        : typeof record.runId === 'string'
          ? record.runId
          : `run-${index + 1}`,
    model,
    taskId:
      typeof record.task_id === 'string'
        ? record.task_id
        : typeof record.taskId === 'string'
          ? record.taskId
          : 'unknown-task',
    taskTitle:
      typeof record.task_title === 'string'
        ? record.task_title
        : typeof record.taskTitle === 'string'
          ? record.taskTitle
          : undefined,
    category:
      typeof record.category === 'string'
        ? record.category
        : undefined,
    finalText:
      typeof record.final_text === 'string'
        ? record.final_text
        : typeof record.finalText === 'string'
          ? record.finalText
          : undefined,
    transcriptPreview:
      typeof transcript.preview === 'string'
        ? transcript.preview
        : undefined,
    score: normalizeScore(record.score),
    failureTags: Array.isArray(record.failure_tags)
      ? record.failure_tags.filter(
          (entry): entry is string => typeof entry === 'string',
        )
      : Array.isArray(record.failureTags)
        ? record.failureTags.filter(
            (entry): entry is string => typeof entry === 'string',
          )
        : [],
    finishedAt:
      typeof record.finished_at === 'string'
        ? record.finished_at
        : typeof record.finishedAt === 'string'
          ? record.finishedAt
          : undefined,
  }
}

export function normalizeSiteData(payload: unknown): SiteData {
  const record = asRecord(payload)
  const scoreboard = asRecord(record.scoreboard)
  const rawModels = Array.isArray(scoreboard.models) ? scoreboard.models : []
  const rawRuns = Array.isArray(record.runs) ? record.runs : []

  return {
    generatedAt:
      typeof record.generated_at === 'string'
        ? record.generated_at
        : typeof record.generatedAt === 'string'
          ? record.generatedAt
          : null,
    scoreboard: {
      models: rawModels.map(normalizeScoreboardModelRow),
    },
    runs: rawRuns.map(normalizeRun),
  }
}

export async function loadSiteData(url = '/site-data.json'): Promise<SiteData> {
  const response = await fetch(url)

  if (!response.ok) {
    throw new Error(`Failed to load site data: ${response.status}`)
  }

  return normalizeSiteData(await response.json())
}
