<template>
  <div class="leaderboard-page page-enter">
    <!-- Pretext 动态背景 -->
    <div class="lb-canvas-wrap">
      <PretextStageCanvas :stage="lightStage" />
    </div>

    <!-- 页面标题区 -->
    <div class="lb-header container">
      <p class="section-tag">Leaderboard</p>
      <h1 class="lb-headline">Model Arena</h1>
      <p class="lb-sub">Real-online benchmark results, updated continuously.</p>
    </div>

    <!-- 过滤面板 -->
    <div class="lb-filters container">
      <!-- 分类筛选 -->
      <div class="filter-group">
        <span class="filter-label">Category</span>
        <div class="filter-chips">
          <button
            v-for="cat in categories"
            :key="cat"
            class="filter-chip"
            :class="{ active: activeCategory === cat }"
            @click="activeCategory = cat"
          >{{ cat }}</button>
        </div>
      </div>

      <!-- License 筛选 -->
      <div class="filter-group">
        <span class="filter-label">License</span>
        <div class="filter-chips">
          <button
            v-for="lic in licenses"
            :key="lic"
            class="filter-chip"
            :class="{ active: activeLicense === lic }"
            @click="activeLicense = lic"
          >{{ lic }}</button>
        </div>
      </div>
    </div>

    <!-- 排名表格 -->
    <div class="lb-table-wrap container">
      <div v-if="loading" class="lb-loading">Loading...</div>
      <div v-else-if="error" class="lb-error">{{ error }}</div>
      <table v-else class="lb-table">
        <thead>
          <tr>
            <th>Rank</th>
            <th>Model</th>
            <th>Score</th>
            <th>Votes</th>
            <th>Input Price</th>
            <th>Output Price</th>
            <th>Context</th>
          </tr>
        </thead>
        <tbody>
          <tr
            v-for="entry in filteredLeaderboard"
            :key="entry.model_id"
            class="lb-row animate-in"
          >
            <td class="td-rank">
              <span class="rank-num">{{ entry.rank }}</span>
              <span class="rank-spread">{{ entry.rank_spread }}</span>
            </td>
            <td class="td-model">
              <p class="model-name">{{ entry.model_name }}</p>
              <p class="model-meta">{{ entry.provider }} · {{ entry.license_type }}</p>
            </td>
            <td class="td-score">
              <span class="score-num">{{ entry.score.toFixed(1) }}</span>
            </td>
            <td class="td-votes">
              <span class="votes-num">{{ entry.vote_count }}</span>
            </td>
            <td class="td-price">
              <span v-if="entry.input_price !== null">${{ entry.input_price.toFixed(2) }}</span>
              <span v-else class="na">N/A</span>
            </td>
            <td class="td-price">
              <span v-if="entry.output_price !== null">${{ entry.output_price.toFixed(2) }}</span>
              <span v-else class="na">N/A</span>
            </td>
            <td class="td-context">
              <span v-if="entry.context_length !== null">{{ formatContext(entry.context_length) }}</span>
              <span v-else class="na">N/A</span>
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { api, type LeaderboardEntry } from '../../api/client'
import PretextStageCanvas from '../PretextStageCanvas.vue'

// Minimal light stage for background — reuses the existing stage system
const lightStage = computed(() => ({
  nodes: [],
  width: 0,
  height: 0,
  meta: { preset: 'ambient' },
}))

const loading = ref(true)
const error = ref('')
const leaderboard = ref<LeaderboardEntry[]>([])
const activeCategory = ref('All')
const activeLicense = ref('All')

const categories = ['All', 'Coding', 'Reasoning', 'Tool Use', 'Agentic']
const licenses = ['All', 'Proprietary', 'Open Source']

const filteredLeaderboard = computed(() => {
  return leaderboard.value.filter((entry) => {
    const matchLicense =
      activeLicense.value === 'All' ||
      entry.license_type === activeLicense.value

    // Category filter: infer from task mix (Coding / Reasoning / Tool Use / Agentic / Delegation)
    // Based on which category of tasks this model scored highest in.
    const taskCategories = entry.tasks?.map((t) => {
      if (!t.task_id) return 'Other'
      const id = t.task_id
      if (id.startsWith('skill-') || id.startsWith('acpx-') || id.startsWith('verify-') || id.startsWith('startup-')) return 'Agentic'
      if (id.startsWith('delegation-')) return 'Delegation'
      if (id.startsWith('tool-') || id.startsWith('cli-')) return 'Tool Use'
      if (id.startsWith('computer-')) return 'Computer Use'
      if (id.startsWith('self-')) return 'Self-Correction'
      if (id.startsWith('coding-') || id.startsWith('json-')) return 'Coding'
      if (id.startsWith('context-') || id.startsWith('multi-')) return 'Reasoning'
      if (id === 'file-search' || id === 'readme-audit') return 'Tool Use' // legacy tasks
      return 'Other'
    }) ?? []

    const uniqueCategories = [...new Set(taskCategories)]
    const matchCategory =
      activeCategory.value === 'All' || uniqueCategories.includes(activeCategory.value)

    return matchLicense && matchCategory
  })
})

function formatContext(n: number): string {
  if (n >= 1000000) return `${(n / 1000000).toFixed(0)}M`
  if (n >= 1000) return `${(n / 1000).toFixed(0)}K`
  return String(n)
}

onMounted(async () => {
  try {
    leaderboard.value = await api.getLeaderboard()
  } catch (e: any) {
    error.value = 'Failed to load leaderboard data'
    console.error(e)
  } finally {
    loading.value = false
  }
})
</script>

<style scoped>
.lb-canvas-wrap {
  position: absolute;
  inset: 0;
  z-index: 0;
  pointer-events: none;
  opacity: 0.07;
}

.lb-header {
  position: relative;
  z-index: 1;
  padding-top: calc(var(--nav-h, 60px) + 4rem);
  padding-bottom: 3rem;
  text-align: center;
}

.lb-headline {
  font-family: var(--font-display);
  font-size: clamp(2.5rem, 6vw, 4rem);
  font-weight: 400;
  color: var(--text-primary);
  letter-spacing: 0.05em;
  margin-bottom: 0.75rem;
}

.lb-sub {
  font-family: var(--font-ui);
  font-size: 1rem;
  color: var(--text-muted);
}

.lb-filters {
  position: relative;
  z-index: 1;
  display: flex;
  gap: 2.5rem;
  padding-block: 1.5rem;
  border-top: 1px solid var(--border);
  border-bottom: 1px solid var(--border);
  margin-bottom: 2.5rem;
  flex-wrap: wrap;
}

.filter-group {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}

.filter-label {
  font-family: var(--font-ui);
  font-size: 0.75rem;
  color: var(--text-muted);
  letter-spacing: 0.08em;
  text-transform: uppercase;
  white-space: nowrap;
}

.filter-chips {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
}

.filter-chip {
  font-family: var(--font-ui);
  font-size: 0.8rem;
  padding: 0.25rem 0.75rem;
  border: 1px solid var(--border);
  border-radius: 100px;
  background: transparent;
  color: var(--text-muted);
  cursor: pointer;
  transition: all 0.2s;
}
.filter-chip:hover { border-color: var(--border-hover); color: var(--text-primary); }
.filter-chip.active {
  background: var(--blue-soft);
  border-color: var(--blue);
  color: var(--blue);
}

.lb-table-wrap { position: relative; z-index: 1; }

.lb-loading, .lb-error {
  text-align: center;
  padding: 4rem;
  font-family: var(--font-ui);
  color: var(--text-muted);
}

.lb-table {
  width: 100%;
  border-collapse: collapse;
  font-family: var(--font-ui);
}

.lb-table thead th {
  font-size: 0.72rem;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--text-muted);
  padding: 0.75rem 1rem;
  text-align: left;
  border-bottom: 1px solid var(--border);
  font-weight: 400;
}

.lb-row td {
  padding: 1rem;
  border-bottom: 1px solid var(--border);
  vertical-align: middle;
}

.lb-row:hover td { background: rgba(255,255,255,0.02); }

.td-rank { white-space: nowrap; }
.rank-num {
  font-family: var(--font-display);
  font-size: 1.8rem;
  color: var(--blue);
  display: block;
  line-height: 1;
}
.rank-spread {
  font-size: 0.7rem;
  color: var(--text-muted);
}

.td-model .model-name {
  font-weight: 600;
  font-size: 0.95rem;
  color: var(--text-primary);
  margin-bottom: 0.15rem;
}
.td-model .model-meta {
  font-size: 0.75rem;
  color: var(--text-muted);
}

.td-score .score-num {
  font-family: var(--font-display);
  font-size: 1.5rem;
  font-weight: 700;
  color: var(--gold);
}

.td-votes .votes-num { font-size: 0.9rem; color: var(--text-muted); }
.td-price { font-size: 0.85rem; color: var(--text-primary); }
.na { color: var(--text-muted); }
.td-context { font-size: 0.85rem; color: var(--text-primary); }

@media (max-width: 768px) {
  .lb-table th:nth-child(5),
  .lb-table th:nth-child(6),
  .lb-table td:nth-child(5),
  .lb-table td:nth-child(6) { display: none; }
}
</style>
