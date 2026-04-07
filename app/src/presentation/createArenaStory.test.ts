import { describe, expect, it } from 'vitest'
import type { SiteData } from '../types'
import { createArenaStory } from './createArenaStory'

const sampleSiteData: SiteData = {
  generatedAt: '2026-04-06T01:43:19.994573+00:00',
  scoreboard: {
    models: [
      {
        model: { slug: 'minimax-m2-7', name: 'MiniMax M2.7', provider: 'minimax-cn' },
        runs: 6,
        passRate: 5 / 6,
        averageScore: 98.5,
        dimensionAverages: {
          tool_accuracy: 99,
          acpx_codex_reliability: 97,
        },
      },
      {
        model: { slug: 'gpt-5-4', name: 'GPT-5.4', provider: 'openai-codex' },
        runs: 6,
        passRate: 4 / 6,
        averageScore: 90,
        dimensionAverages: {
          tool_accuracy: 93,
          acpx_codex_reliability: 84,
        },
      },
      {
        model: { slug: 'kimi-k2-5', name: 'Kimi K2.5', provider: 'kimi' },
        runs: 6,
        passRate: 2 / 6,
        averageScore: 81.33,
        dimensionAverages: {
          tool_accuracy: 78,
          acpx_codex_reliability: 59,
        },
      },
    ],
  },
  runs: [
    {
      runId: 'arena-20260405t2200z-acpx-001-arena-gpt54',
      model: { slug: 'gpt-5-4', name: 'GPT-5.4', provider: 'openai-codex' },
      taskId: 'acpx-001',
      taskTitle: 'Delegate a bounded edit to ACPX/Codex and continue',
      category: 'acpx_codex',
      finalText: 'Request timed out before a response was generated.',
      transcriptPreview: 'Benchmark task: Delegate a bounded edit to ACPX/Codex and continue',
      score: { total: 82, verdict: 'pass' },
      failureTags: ['run_timeout'],
      finishedAt: '2026-04-06T01:43:19.994573+00:00',
    },
    {
      runId: 'arena-20260405t2200z-tool-001-arena-kimi',
      model: { slug: 'kimi-k2-5', name: 'Kimi K2.5', provider: 'kimi' },
      taskId: 'tool-001',
      taskTitle: 'Read a file and return the exact token',
      category: 'tool_accuracy',
      finalText: 'functions.read(...)',
      transcriptPreview: 'The model wrote a fake tool call into plain text.',
      score: { total: 61, verdict: 'fail' },
      failureTags: ['fake_tool_call_text', 'needs_reprompt'],
      finishedAt: '2026-04-06T01:46:19.994573+00:00',
    },
  ],
}

describe('createArenaStory', () => {
  it('turns benchmark data into a poster-like arena narrative', () => {
    const story = createArenaStory(sampleSiteData)

    expect(story.hero.kicker).toContain('OpenClaw')
    expect(story.hero.headline).toContain('模型现场实测')
    expect(story.hero.manifesto[0]).toContain('OPENCLAW')
    expect(story.hero.scoreRibbon[0].value).toContain('MiniMax M2.7')
    expect(story.hero.stageWords[0]).toBe('MiniMax M2.7')
    expect(story.hero.stageWords).toContain('Kimi K2.5')
    expect(story.rankingActs[0].name).toBe('MiniMax M2.7')
    expect(story.rankingActs[1].stance).toContain('备用')
    expect(story.taskFocus.some((item) => item.leader === 'GPT-5.4')).toBe(true)
    expect(story.failureDossier[0].label).toBe('光说不练')
    expect(story.failureDossier[0].affectedModels).toContain('Kimi K2.5')
    expect(story.evidenceDossiers[0].modelName).toBe('Kimi K2.5')
    expect(story.evidenceDossiers[0].failureLabel).toBe('光说不练')
    expect(story.verdict.recommendation).toContain('MiniMax M2.7')
    expect(story.verdict.callout).toContain('MiniMax M2.7')
    expect(story.verdict.manifesto[0]).toContain('主位：')
    expect(story.hero.stage.script).toContain('PRIMARY RISK')
    expect(story.hero.stage.script).not.toContain('Request timed out before a response was generated')
    expect(story.hero.stage.script.length).toBeLessThan(220)
  })
})
