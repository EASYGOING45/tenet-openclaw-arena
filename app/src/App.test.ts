import { readFileSync } from 'node:fs'
import { describe, expect, it } from 'vitest'
import { fileURLToPath } from 'node:url'
import { dirname, join } from 'node:path'

const __dirname = dirname(fileURLToPath(import.meta.url))
const appSourcePath = join(__dirname, 'App.vue')

describe('App arena landing page', () => {
  it('keeps the page as a poster-style composition shell', () => {
    const source = readFileSync(appSourcePath, 'utf8')

    expect(source).toContain('PretextStageCanvas')
    expect(source).toContain('hero-section')
    expect(source).toContain('arena-nav')
    expect(source).toContain('score-ribbon')
    expect(source).toContain('task-focus-grid')
    expect(source).toContain('evidence-rail')
    expect(source).toContain('verdict-section')
    expect(source).toContain('failure-list')
    expect(source).toContain('ranking-acts')
  })

  it('still loads site data and derives benchmark-driven story content', () => {
    const source = readFileSync(appSourcePath, 'utf8')

    expect(source).toContain('loadSiteData')
    expect(source).toContain('createArenaStory')
    expect(source).toContain('story.hero')
    expect(source).toContain('story.taskFocus')
    expect(source).toContain('story.evidenceDossiers')
  })
})
