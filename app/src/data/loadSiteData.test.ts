import { describe, expect, it } from 'vitest'
import { normalizeSiteData } from './loadSiteData'

describe('normalizeSiteData', () => {
  it('returns scoreboard models and runs from the plan shape', () => {
    const result = normalizeSiteData({
      scoreboard: {
        models: [{ model: 'gpt-5.4', averageTotal: 91, runCount: 2 }],
      },
      runs: [{ model: 'gpt-5.4' }],
    })

    expect(result.scoreboard.models[0].model.slug).toBe('gpt-5-4')
    expect(result.scoreboard.models[0].averageScore).toBe(91)
    expect(result.scoreboard.models[0].runs).toBe(2)
    expect(result.runs).toHaveLength(1)
    expect(result.runs[0].model.name).toBe('gpt-5.4')
  })

  it('normalizes the backend payload shape used by the site builder', () => {
    const result = normalizeSiteData({
      generated_at: '2026-04-05T12:00:00Z',
      scoreboard: {
        models: [
          {
            model: { slug: 'openai-codex-gpt-5-4', name: 'GPT-5.4', provider: 'openai-codex' },
            runs: 2,
            pass_rate: 0.5,
            average_score: 80,
            dimension_averages: { tool_accuracy: 90 },
          },
        ],
      },
      runs: [
        {
          run_id: 'arena-gpt54-task-01',
          task_id: 'task-01',
          task_title: 'Delegate a bounded edit to ACPX/Codex and continue',
          category: 'acpx_codex',
          model: { slug: 'openai-codex-gpt-5-4', name: 'GPT-5.4' },
          final_text: 'Request timed out before a response was generated.',
          score: {
            total: 82,
            verdict: 'pass',
            dimensions: { tool_accuracy: 90 },
          },
          failure_tags: ['fallback_recovery'],
          finished_at: '2026-04-05T12:30:00Z',
          transcript: {
            preview: 'Benchmark task: Delegate a bounded edit to ACPX/Codex and continue',
          },
        },
      ],
    })

    expect(result.generatedAt).toBe('2026-04-05T12:00:00Z')
    expect(result.scoreboard.models[0].model.name).toBe('GPT-5.4')
    expect(result.scoreboard.models[0].passRate).toBe(0.5)
    expect(result.scoreboard.models[0].dimensionAverages.tool_accuracy).toBe(90)
    expect(result.runs[0].runId).toBe('arena-gpt54-task-01')
    expect(result.runs[0].taskTitle).toBe('Delegate a bounded edit to ACPX/Codex and continue')
    expect(result.runs[0].category).toBe('acpx_codex')
    expect(result.runs[0].finalText).toContain('Request timed out')
    expect(result.runs[0].transcriptPreview).toContain('Benchmark task')
    expect(result.runs[0].failureTags).toEqual(['fallback_recovery'])
    expect(result.runs[0].score.verdict).toBe('pass')
  })
})
