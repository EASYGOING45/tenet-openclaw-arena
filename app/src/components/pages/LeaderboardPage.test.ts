/**
 * LeaderboardPage.test.ts
 *
 * Tests the LeaderboardPage component filter logic.
 * Uses Vitest + Vue Test Utils.
 */

import { describe, it, expect, vi, beforeEach } from 'vitest'
import { ref, computed } from 'vue'

// Replicate the filter logic from LeaderboardPage.vue
// (copied here so tests are isolated from the component internals)

type LeaderboardEntry = {
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

function taskIdToCategory(taskId: string): string {
  if (!taskId) return 'Other'
  if (taskId.startsWith('skill-') || taskId.startsWith('acpx-') || taskId.startsWith('verify-') || taskId.startsWith('startup-')) return 'Agentic'
  if (taskId.startsWith('delegation-')) return 'Delegation'
  if (taskId.startsWith('tool-') || taskId.startsWith('cli-')) return 'Tool Use'
  if (taskId.startsWith('computer-')) return 'Computer Use'
  if (taskId.startsWith('self-')) return 'Self-Correction'
  if (taskId.startsWith('coding-') || taskId.startsWith('json-')) return 'Coding'
  if (taskId.startsWith('context-') || taskId.startsWith('multi-')) return 'Reasoning'
  if (taskId === 'file-search' || taskId === 'readme-audit') return 'Tool Use' // legacy tasks
  return 'Other'
}

function filterLeaderboard(
  entries: LeaderboardEntry[],
  activeCategory: string,
  activeLicense: string
): LeaderboardEntry[] {
  return entries.filter((entry) => {
    const matchLicense =
      activeLicense === 'All' || entry.license_type === activeLicense

    const taskCategories = entry.tasks?.map((t) => taskIdToCategory(t.task_id)) ?? []
    const uniqueCategories = [...new Set(taskCategories)]
    const matchCategory =
      activeCategory === 'All' || uniqueCategories.includes(activeCategory)

    return matchLicense && matchCategory
  })
}

const MOCK_ENTRIES: LeaderboardEntry[] = [
  {
    rank: 1,
    model_id: 'gpt-5.4',
    model_name: 'GPT-5.4',
    provider: 'OpenAI',
    license_type: 'Proprietary',
    score: 90.63,
    vote_count: 12,
    rank_spread: '+0/-2',
    input_price: 5,
    output_price: 25,
    context_length: 1000000,
    tasks: [
      { task_id: 'coding-loop', score: 91, failure_label: 'PASS' },
      { task_id: 'readme-audit', score: 88, failure_label: 'PASS' },
      { task_id: 'context-summary', score: 90, failure_label: 'PASS' },
      { task_id: 'json-extract', score: 97, failure_label: 'PASS' },
      { task_id: 'multi-step-reasoning', score: 89, failure_label: 'PASS' },
      { task_id: 'file-search', score: 93, failure_label: 'PASS' },
    ],
  },
  {
    rank: 2,
    model_id: 'kimi-k2p5',
    model_name: 'Kimi-K2.5',
    provider: 'Moonshot',
    license_type: 'Modified MIT',
    score: 83.96,
    vote_count: 12,
    rank_spread: '+1/-1',
    input_price: 0.6,
    output_price: 3,
    context_length: 262144,
    tasks: [
      { task_id: 'coding-loop', score: 88, failure_label: 'PASS' },
      { task_id: 'readme-audit', score: 75, failure_label: 'PASS' },
      { task_id: 'context-summary', score: 82, failure_label: 'PASS' },
      { task_id: 'json-extract', score: 95, failure_label: 'PASS' },
      { task_id: 'multi-step-reasoning', score: 83, failure_label: 'PASS' },
      { task_id: 'file-search', score: 85, failure_label: 'PASS' },
    ],
  },
  {
    rank: 3,
    model_id: 'minimax-m2.7',
    model_name: 'MiniMax-M2.7',
    provider: 'MiniMax',
    license_type: 'Proprietary',
    score: 82.75,
    vote_count: 12,
    rank_spread: '+0/-2',
    input_price: 0.3,
    output_price: 1.2,
    context_length: 204800,
    tasks: [
      { task_id: 'coding-loop', score: 85, failure_label: 'PASS' },
      { task_id: 'readme-audit', score: 72, failure_label: 'PASS' },
      { task_id: 'context-summary', score: 78, failure_label: 'FAIL' },
      { task_id: 'json-extract', score: 92, failure_label: 'PASS' },
      { task_id: 'multi-step-reasoning', score: 80, failure_label: 'PASS' },
      { task_id: 'file-search', score: 88, failure_label: 'PASS' },
    ],
  },
]

describe('LeaderboardPage Filter Logic', () => {
  describe('License filter', () => {
    it('All license returns all entries', () => {
      const result = filterLeaderboard(MOCK_ENTRIES, 'All', 'All')
      expect(result).toHaveLength(3)
    })

    it('Proprietary filter returns only gpt-5.4 and minimax-m2.7', () => {
      const result = filterLeaderboard(MOCK_ENTRIES, 'All', 'Proprietary')
      expect(result).toHaveLength(2)
      expect(result.map((e) => e.model_id)).toEqual(['gpt-5.4', 'minimax-m2.7'])
    })

    it('Unknown license returns empty', () => {
      const result = filterLeaderboard(MOCK_ENTRIES, 'All', 'Open Source')
      expect(result).toHaveLength(0)
    })

    it('Modified MIT filter returns only kimi-k2p5', () => {
      const result = filterLeaderboard(MOCK_ENTRIES, 'All', 'Modified MIT')
      expect(result).toHaveLength(1)
      expect(result[0].model_id).toBe('kimi-k2p5')
    })
  })

  describe('Category filter (inferred from task_ids)', () => {
    it('Coding filter returns entries that have coding-loop tasks', () => {
      const result = filterLeaderboard(MOCK_ENTRIES, 'Coding', 'All')
      expect(result).toHaveLength(3) // all 3 have coding-loop
    })

    it('Reasoning filter returns entries with context-summary / multi-step-reasoning', () => {
      const result = filterLeaderboard(MOCK_ENTRIES, 'Reasoning', 'All')
      expect(result).toHaveLength(3) // all 3 have these
    })

    it('Agentic filter returns empty (no Agentic tasks in legacy benchmark)', () => {
      const result = filterLeaderboard(MOCK_ENTRIES, 'Agentic', 'All')
      expect(result).toHaveLength(0)
    })

    it('Tool Use filter returns entries with file-search tasks', () => {
      const result = filterLeaderboard(MOCK_ENTRIES, 'Tool Use', 'All')
      expect(result).toHaveLength(3) // all 3 have file-search
    })
  })

  describe('Combined filters', () => {
    it('Proprietary + Coding returns gpt-5.4 and minimax-m2.7', () => {
      const result = filterLeaderboard(MOCK_ENTRIES, 'Coding', 'Proprietary')
      expect(result).toHaveLength(2)
      expect(result.map((e) => e.model_id).sort()).toEqual(['gpt-5.4', 'minimax-m2.7'])
    })

    it('Modified MIT + Reasoning returns only kimi-k2p5', () => {
      const result = filterLeaderboard(MOCK_ENTRIES, 'Reasoning', 'Modified MIT')
      expect(result).toHaveLength(1)
      expect(result[0].model_id).toBe('kimi-k2p5')
    })

    it('Proprietary + Agentic returns empty', () => {
      const result = filterLeaderboard(MOCK_ENTRIES, 'Agentic', 'Proprietary')
      expect(result).toHaveLength(0)
    })
  })

  describe('Empty and null task lists', () => {
    const entryWithNoTasks: LeaderboardEntry = {
      ...MOCK_ENTRIES[0],
      tasks: [],
    }

    it('Entry with no tasks returns empty category match (All still matches)', () => {
      const result = filterLeaderboard([entryWithNoTasks], 'All', 'All')
      expect(result).toHaveLength(1)
    })

    it('Entry with no tasks does not match any specific category', () => {
      const result = filterLeaderboard([entryWithNoTasks], 'Coding', 'All')
      expect(result).toHaveLength(0)
    })
  })
})

describe('taskIdToCategory', () => {
  it('maps skill-dispatch-* to Agentic', () => {
    expect(taskIdToCategory('skill-dispatch-001')).toBe('Agentic')
  })
  it('maps delegation-* to Delegation', () => {
    expect(taskIdToCategory('delegation-001')).toBe('Delegation')
  })
  it('maps tool-chain-* to Tool Use', () => {
    expect(taskIdToCategory('tool-chain-001')).toBe('Tool Use')
  })
  it('maps cli-* to Tool Use', () => {
    expect(taskIdToCategory('cli-001')).toBe('Tool Use')
  })
  it('maps computer-* to Computer Use', () => {
    expect(taskIdToCategory('computer-001')).toBe('Computer Use')
  })
  it('maps self-correction-* to Self-Correction', () => {
    expect(taskIdToCategory('self-correction-001')).toBe('Self-Correction')
  })
  it('maps coding-loop to Coding', () => {
    expect(taskIdToCategory('coding-loop')).toBe('Coding')
  })
  it('maps json-extract to Coding', () => {
    expect(taskIdToCategory('json-extract')).toBe('Coding')
  })
  it('maps context-summary to Reasoning', () => {
    expect(taskIdToCategory('context-summary')).toBe('Reasoning')
  })
  it('maps multi-step-reasoning to Reasoning', () => {
    expect(taskIdToCategory('multi-step-reasoning')).toBe('Reasoning')
  })
  it('maps file-search to Tool Use (legacy task)', () => {
    expect(taskIdToCategory('file-search')).toBe('Tool Use')
  })
  it('maps readme-audit to Tool Use (legacy task)', () => {
    expect(taskIdToCategory('readme-audit')).toBe('Tool Use')
  })
  it('maps unknown task_id to Other', () => {
    expect(taskIdToCategory('unknown-task')).toBe('Other')
  })
  it('handles empty string', () => {
    expect(taskIdToCategory('')).toBe('Other')
  })
})
