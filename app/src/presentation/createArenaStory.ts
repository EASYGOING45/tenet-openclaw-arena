import type { ArenaRun, ScoreboardModelRow, SiteData } from '../types'
import type { PretextStage } from '../stage/renderPretextStage'

interface NavLink {
  href: string
  label: string
}

interface ScoreRibbonItem {
  label: string
  value: string
  note: string
}

interface RankingAct {
  rank: string
  name: string
  provider: string
  average: string
  passRate: string
  leadDimension: {
    label: string
    value: string
  }
  stance: string
  signal: string
}

interface TaskFocusItem {
  taskId: string
  taskLabel: string
  taskName: string
  leader: string
  score: string
  verdict: string
}

interface FailureDossierItem {
  label: string
  description: string
  num: string
  affectedModels: string
}

interface EvidenceDossierItem {
  runId: string
  modelName: string
  taskLabel: string
  score: string
  verdict: string
  caption: string
  excerpt: string
  failureLabel: string
  isFailure: boolean
}

interface VerdictBlock {
  recommendation: string
  callout: string
  summary: string
  manifesto: string[]
  stage: PretextStage
}

export interface ArenaStory {
  navLinks: NavLink[]
  rankingSectionTitle: string
  taskSectionTitle: string
  failureSectionTitle: string
  evidenceSectionTitle: string
  hero: {
    kicker: string
    headline: string
    summary: string
    manifesto: string[]
    scoreRibbon: ScoreRibbonItem[]
    stageWords: string[]
    stage: PretextStage
    kpis: Array<{ label: string; value: string }>
  }
  rankingActs: RankingAct[]
  taskFocus: TaskFocusItem[]
  failureDossier: FailureDossierItem[]
  evidenceDossiers: EvidenceDossierItem[]
  verdict: VerdictBlock
}

const DIMENSION_LABELS: Record<string, string> = {
  task_completion: '任务完成度',
  tool_accuracy: '工具准确度',
  autonomy_continuity: '连续执行',
  recovery_behavior: '恢复动作',
  verification_honesty: '验证诚实度',
  acpx_codex_reliability: '委派可靠性',
  output_quality: '输出质量',
  latency_cost_efficiency: '时延 / 成本',
}

const FAILURE_LABELS: Record<string, { label: string; description: string; priority: number }> = {
  fake_tool_call_text: {
    label: '光说不练',
    description: '模型输出了工具调用的样子，但实际没有真正调。',
    priority: 100,
  },
  empty_tool_args: {
    label: '参数残缺',
    description: '工具调用发出了，但关键参数是空的，执行链在这里就断了。',
    priority: 80,
  },
  run_timeout: {
    label: '跑超时了',
    description: '思路方向可能没问题，但没在规定时间内跑完。',
    priority: 75,
  },
  needs_reprompt: {
    label: '半路卡住',
    description: '模型在中间步骤停了，需要再推一下才能继续。',
    priority: 60,
  },
  delegate_recovery: {
    label: '委派后自救',
    description: '委派出去的东西没跑回来，它自己去补了。',
    priority: 40,
  },
}

const TASK_LABELS: Record<string, string> = {
  'startup-001': '新会话启动纪律',
  'tool-001': '读取文件并返回精确 token',
  'auto-001': '多步任务不中断继续',
  'recovery-001': '错误路径后的恢复',
  'verify-001': '完成前显式验证',
  'acpx-001': 'ACPX / Codex 委派后继续执行',
}

function compareModels(left: ScoreboardModelRow, right: ScoreboardModelRow): number {
  return (
    right.averageScore - left.averageScore ||
    right.passRate - left.passRate ||
    right.runs - left.runs ||
    left.model.name.localeCompare(right.model.name)
  )
}

function formatPercent(value: number): string {
  return `${Math.round(value * 100)}%`
}

function formatScore(value: number | undefined): string {
  return typeof value === 'number' && Number.isFinite(value) ? value.toFixed(1) : '—'
}

function taskTitle(run: ArenaRun): string {
  return run.taskTitle ?? TASK_LABELS[run.taskId] ?? run.taskId
}

function summarizeRun(run: ArenaRun): string {
  if (run.failureTags.includes('fake_tool_call_text')) {
    return '看起来像执行，实际上只是把工具动作演出来。'
  }

  if (run.failureTags.includes('run_timeout')) {
    return '方向没跑偏，但长链路还是被超时切断。'
  }

  if (run.failureTags.includes('needs_reprompt')) {
    return '它会在半路停下，需要外部再推一把。'
  }

  if (run.failureTags.includes('delegate_recovery')) {
    return '它的价值不在首轮完美，而在于会补救。'
  }

  if (run.score.verdict === 'pass') {
    return '链路收束得比较干净，说明这类任务上更稳。'
  }

  return '这条样本说明它在 runtime 里依然有明显摩擦。'
}

function excerpt(run: ArenaRun): string {
  const text = (run.finalText ?? run.transcriptPreview ?? '')
    .replace(/\s+/g, ' ')
    .trim()

  if (text.length === 0) {
    return '暂无可展示的 transcript 摘录。'
  }

  return text.length > 180 ? `${text.slice(0, 180).trimEnd()}…` : text
}

function failureMeta(tag: string): { label: string; description: string; priority: number } {
  return FAILURE_LABELS[tag] ?? {
    label: tag,
    description: '这个 failure 还需要结合 transcript 才能准确定位。',
    priority: 0,
  }
}

function evidencePriority(run: ArenaRun): number {
  let score = 0

  if (run.failureTags.includes('fake_tool_call_text')) score += 12
  if (run.failureTags.includes('run_timeout')) score += 8
  if (run.failureTags.includes('needs_reprompt')) score += 6
  if (run.score.verdict === 'fail') score += 5
  if (/acpx|codex|delegate/i.test(`${run.taskId} ${run.category ?? ''}`)) score += 3
  if ((run.score.total ?? 0) < 80) score += 2

  return score
}

function leadDimension(model: ScoreboardModelRow): { label: string; value: string } {
  const entry = Object.entries(model.dimensionAverages).sort((left, right) => right[1] - left[1])[0]

  if (!entry) {
    return {
      label: '关键维度',
      value: '待补样本',
    }
  }

  return {
    label: DIMENSION_LABELS[entry[0]] ?? entry[0],
    value: formatScore(entry[1]),
  }
}

function modelRuns(siteData: SiteData, slug: string): ArenaRun[] {
  return siteData.runs.filter((run) => run.model.slug === slug)
}

function modelSignal(model: ScoreboardModelRow, index: number, runs: ArenaRun[]): string {
  const topRisk = Array.from(
    runs.reduce((map, run) => {
      run.failureTags.forEach((tag) => map.set(tag, (map.get(tag) ?? 0) + 1))
      return map
    }, new Map<string, number>()),
  )
    .sort((left, right) => right[1] - left[1])
    .map(([tag]) => failureMeta(tag).label)[0]

  if (index === 0) {
    return topRisk
      ? `主位可用，但要持续盯住 ${topRisk} 这一类风险。`
      : '主位候选，故障密度低，适合站在最前排。'
  }

  if (index === 1) {
    return '备用，适合接管需要更稳输出的链路。'
  }

  return topRisk
    ? `当前更像观察位，尤其要提防 ${topRisk} 这类摩擦。`
    : '当前样本仍偏弱，需要更多运行记录再上主链路。'
}

export function createArenaStory(siteData: SiteData): ArenaStory {
  const rankedModels = [...siteData.scoreboard.models].sort(compareModels)
  const champion = rankedModels[0] ?? null
  const runnerUp = rankedModels[1] ?? null

  const failureCounts = new Map<string, number>()
  const modelsByFailure = new Map<string, Set<string>>()
  const tasksByFailure = new Map<string, Set<string>>()

  siteData.runs.forEach((run) => {
    run.failureTags.forEach((tag) => {
      failureCounts.set(tag, (failureCounts.get(tag) ?? 0) + 1)

      if (!modelsByFailure.has(tag)) {
        modelsByFailure.set(tag, new Set<string>())
      }
      modelsByFailure.get(tag)?.add(run.model.name)

      if (!tasksByFailure.has(tag)) {
        tasksByFailure.set(tag, new Set<string>())
      }
      tasksByFailure.get(tag)?.add(taskTitle(run))
    })
  })

  const failureDossier = Array.from(failureCounts.entries())
    .map(([tag, count]) => {
      const meta = failureMeta(tag)
      const models = Array.from(modelsByFailure.get(tag) ?? []).sort()
      const tasks = Array.from(tasksByFailure.get(tag) ?? []).sort()

      return {
        label: meta.label,
        description: meta.description,
        priority: meta.priority,
        count,
        affectedModels: models.length > 0 ? models.join(' / ') : '暂无直接命中的模型',
        signal: tasks[0] ?? '等待更多样本',
      }
    })
    .sort(
      (left, right) =>
        right.count - left.count ||
        right.priority - left.priority ||
        left.label.localeCompare(right.label),
    )
    .slice(0, 4)

  const rankingActs = rankedModels.map((model, index) => {
    const lead = leadDimension(model)

    return {
      rank: `${index + 1}`.padStart(2, '0'),
      name: model.model.name,
      provider: model.model.provider ?? model.model.slug.replace(/-/g, ' '),
      average: formatScore(model.averageScore),
      passRate: formatPercent(model.passRate),
      leadDimension: lead,
      stance: index === 0 ? '主位' : index === 1 ? '备用' : '观察位',
      signal: modelSignal(model, index, modelRuns(siteData, model.model.slug)),
    }
  })

  const runsByTask = siteData.runs.reduce<Map<string, ArenaRun[]>>((map, run) => {
    if (!map.has(run.taskId)) {
      map.set(run.taskId, [])
    }

    map.get(run.taskId)?.push(run)
    return map
  }, new Map<string, ArenaRun[]>())

  const taskFocus = Array.from(runsByTask.entries())
    .map(([taskId, runs]) => {
      const sorted = [...runs].sort(
        (left, right) =>
          (right.score.total ?? 0) - (left.score.total ?? 0) ||
          left.model.name.localeCompare(right.model.name),
      )
      const lead = sorted[0]
      const stressed = [...runs].sort((left, right) => evidencePriority(right) - evidencePriority(left))[0]

      return {
        taskId,
        label: taskTitle(lead),
        leader: lead.model.name,
        score: formatScore(lead.score.total),
        verdict: lead.score.verdict ?? 'unknown',
        tension: summarizeRun(stressed),
      }
    })
    .sort((left, right) => left.label.localeCompare(right.label))

  const evidenceDossiers = [...siteData.runs]
    .sort((left, right) => {
      return (
        evidencePriority(right) - evidencePriority(left) ||
        (left.score.total ?? 0) - (right.score.total ?? 0) ||
        left.runId.localeCompare(right.runId)
      )
    })
    .slice(0, 6)
    .map((run) => ({
      runId: run.runId,
      modelName: run.model.name,
      taskLabel: taskTitle(run),
      score: formatScore(run.score.total),
      verdict: run.score.verdict ?? 'unknown',
      caption: summarizeRun(run),
      excerpt: excerpt(run),
      failureLabel: run.failureTags[0] ? failureMeta(run.failureTags[0]).label : 'Clean run',
    }))

  const stageWords = [
    champion?.model.name ?? 'MODEL',
    runnerUp?.model.name ?? 'BACKUP',
    rankedModels[2]?.model.name ?? 'SIGNAL',
    'OPENCLAW',
    'VERIFY',
    'RUNTIME',
  ]

  const stageScript = [
    'OPENCLAW LIVE SIGNAL.',
    champion ? `${champion.model.name.toUpperCase()} ON POINT.` : 'WAITING FOR LEADER.',
    runnerUp ? `${runnerUp.model.name.toUpperCase()} STANDS BY.` : '',
    failureDossier[0] ? `PRIMARY RISK ${failureDossier[0].label.toUpperCase()}.` : 'PRIMARY RISK PENDING.',
    `${siteData.runs.length} RUNS. ${rankedModels.length} MODELS.`,
  ]
    .filter(Boolean)
    .join(' ')

  const heroSummary = champion && runnerUp
    ? `${champion.model.name} 在多个真实任务链路上站住了，${runnerUp.model.name} 作为备用选项表现稳定。把它们扔进真实任务里，看的不是谁更会说，而是谁断链少、谁收得回来。`
    : '跑完一批任务后，这里会自动生成模型排名的现场解读。'

  const verdictStage: PretextStage = {
    headline: champion?.model.name ?? 'Runtime',
    accentLabel: failureDossier[0]?.label ?? 'Signal',
    script: stageScript,
    words: stageWords,
  }

  const verdict: VerdictBlock = champion
    ? {
        recommendation: `主位：${champion.model.name}。${runnerUp?.model.name ?? '更多样本待入'} 作为备用。`,
        callout: `${champion.model.name} 靠的不是最会说，而是断链少、收得回来。`,
        summary: '选模型别只看对话质感。看 failure tag、恢复能力、委派链路——这些才是生产环境里真正会发生的事。',
        manifesto: [
          `主位：${champion.model.name}`,
          `备用：${runnerUp?.model.name ?? '等待更多样本'}`,
          `首要风险：${failureDossier[0]?.label ?? '等待更多样本'}`,
        ],
        stage: verdictStage,
      }
    : {
        recommendation: '数据还不够，先跑几轮再说。',
        callout: '暂无足够的运行样本，不下结论。',
        summary: '把任务跑完，数据自然会长出来。',
        manifesto: [
          '主位：待定',
          '备用：待定',
          '首要风险：待补样本',
        ],
        stage: verdictStage,
      }

  const kpis = ([
    champion ? { label: champion.model.name, value: formatScore(champion.averageScore) } : null,
    runnerUp ? { label: runnerUp.model.name, value: formatScore(runnerUp.averageScore) } : null,
    { label: 'Live Runs', value: String(siteData.runs.length) },
  ]).filter((k): k is { label: string; value: string } => k !== null)

  return {
    navLinks: [
      { href: '#hero', label: '首页' },
      { href: '#ranking', label: '排位' },
      { href: '#tasks', label: '任务' },
      { href: '#failures', label: '风险' },
      { href: '#evidence', label: '记录' },
    ],
    rankingSectionTitle: '按平均分排列。点击可看详情。',
    taskSectionTitle: '每道题的得分和通过情况。',
    failureSectionTitle: '所有模型共同遇到的失败模式。',
    evidenceSectionTitle: '随机抽样六条原始记录，原文呈现。',
    hero: {
      kicker: 'OpenClaw Model Arena',
      headline: '模型现场实测，谁真正能打。',
      summary: heroSummary,
      manifesto: [
        'OPENCLAW MODEL ARENA',
        champion ? `${champion.model.name.toUpperCase()} LEADS THE RUNTIME.` : 'LIVE BOARD PENDING.',
        failureDossier[0] ? `PRIMARY RISK ${failureDossier[0].label.toUpperCase()}.` : 'PRIMARY RISK PENDING.',
      ],
      scoreRibbon: [
        {
          label: '主位选手',
          value: champion ? `${champion.model.name}` : '等待入场',
          note: champion ? `均分 ${formatScore(champion.averageScore)} / ${formatPercent(champion.passRate)} 通过` : '暂无数据',
        },
        {
          label: '备用选手',
          value: runnerUp ? `${runnerUp.model.name}` : '等待入场',
          note: runnerUp ? `均分 ${formatScore(runnerUp.averageScore)} / ${formatPercent(runnerUp.passRate)} 通过` : '暂无数据',
        },
        {
          label: '本次样本',
          value: `${siteData.runs.length} 条`,
          note: `${rankedModels.length} 个模型`,
        },
        {
          label: '首要风险',
          value: failureDossier[0]?.label ?? '暂无',
          note: failureDossier[0] ? `影响 ${failureDossier[0].count} 条` : '等待更多样本',
        },
      ],
      stageWords,
      stage: verdictStage,
      kpis,
    },
    rankingActs,
    taskFocus: taskFocus.map((item) => ({
      ...item,
      taskName: item.label,
      taskLabel: item.label,
    })),
    failureDossier: failureDossier.map((item, i) => ({
      ...item,
      num: String(i + 1),
    })),
    evidenceDossiers: evidenceDossiers.map((item) => ({
      ...item,
      isFailure: item.failureLabel === 'FAIL',
    })),
    verdict: {
      ...verdict,
      stage: verdictStage,
    },
  }
}
