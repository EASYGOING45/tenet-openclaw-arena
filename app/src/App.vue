<script setup lang="ts">
import { computed, onMounted, onUnmounted, ref } from 'vue'
import PretextStageCanvas from './components/PretextStageCanvas.vue'
import { loadSiteData } from './data/loadSiteData'
import { createArenaStory } from './presentation/createArenaStory'
import type { SiteData } from './types'
import LeaderboardPage from './components/pages/LeaderboardPage.vue'

const currentPage = ref<'home' | 'leaderboard'>('home')

const EMPTY_SITE_DATA: SiteData = {
  generatedAt: null,
  scoreboard: { models: [] },
  runs: [],
}

function formatDate(value: string | null | undefined): string {
  if (!value) {
    return '-'
  }

  const parsed = new Date(value)
  if (Number.isNaN(parsed.getTime())) {
    return value
  }

  return new Intl.DateTimeFormat('zh-CN', {
    dateStyle: 'medium',
    timeStyle: 'short',
  }).format(parsed)
}

const siteData = ref<SiteData>(EMPTY_SITE_DATA)
const isLoading = ref(true)
const loadError = ref<string | null>(null)

const story = computed(() => createArenaStory(siteData.value))

const statusLabel = computed(() => {
  if (loadError.value) {
    return `${loadError.value}。当前页面展示的是降级版故事层。`
  }

  if (isLoading.value) {
    return '正在读取现场 evidence...'
  }

  return `数据时间 ${formatDate(siteData.value.generatedAt)}`
})

// Nav scroll listener
const nav = ref<HTMLElement | null>(null)
function onScroll() {
  if (nav.value) {
    nav.value.classList.toggle('scrolled', window.scrollY > 20)
  }
}
onMounted(async () => {
  window.addEventListener('scroll', onScroll, { passive: true })
  try {
    siteData.value = await loadSiteData()
  } catch (error) {
    loadError.value = error instanceof Error ? error.message : 'Failed to load site data'
  } finally {
    isLoading.value = false
  }
})
onUnmounted(() => {
  window.removeEventListener('scroll', onScroll)
})
</script>

<template>
  <div class="arena-page page-enter">
    <!-- Nav -->
    <header class="arena-nav" id="top-nav" ref="nav">
      <a class="nav-brand" href="#hero"><span>ARENA</span></a>
      <nav class="nav-links">
        <a href="#ranking" @click.prevent="currentPage = 'home'">排位</a>
        <a href="#tasks" @click.prevent="currentPage = 'home'">任务</a>
        <a href="#failures" @click.prevent="currentPage = 'home'">风险</a>
        <a href="#evidence" @click.prevent="currentPage = 'home'">记录</a>
        <a href="#" @click.prevent="currentPage = 'leaderboard'">数据表</a>
      </nav>
    </header>

    <main>
      <!-- Global ambient particles -->
      <div class="ambient-canvas" aria-hidden="true">
        <PretextStageCanvas :stage="story.hero.stage" />
      </div>

      <LeaderboardPage v-if="currentPage === 'leaderboard'" />

      <section id="hero" class="hero-section">
        <div class="hero-content">
          <p class="hero-kicker">{{ story.hero.kicker }}</p>
          <h1 class="hero-headline">{{ story.hero.headline }}</h1>
          <p class="hero-summary">{{ story.hero.summary }}</p>
          <div class="hero-kpis">
            <div class="hero-kpi" v-for="kpi in story.hero.kpis" :key="kpi.label">
              <span class="hero-kpi-value">{{ kpi.value }}</span>
              <span class="hero-kpi-label">{{ kpi.label }}</span>
            </div>
          </div>
        </div>
      </section>

      <!-- Score Ribbon -->
      <section class="score-ribbon">
        <div class="score-ribbon-item" v-for="item in story.hero.scoreRibbon" :key="item.label">
          <p class="score-ribbon-value">{{ item.value }}</p>
          <p class="score-ribbon-label">{{ item.label }}</p>
        </div>
      </section>

      <!-- Ranking Acts -->
      <section id="ranking" class="ranking-section section-gap">
        <div class="container">
          <div class="section-heading section-heading--row">
            <span class="section-heading-label">排位</span>
            <h2 class="section-title">{{ story.rankingSectionTitle }}</h2>
          </div>
          <div class="ranking-acts">
            <article class="ranking-act animate-in" v-for="item in story.rankingActs" :key="item.name">
              <p class="ranking-rank">{{ item.rank }}</p>
              <p class="ranking-provider">{{ item.provider }}</p>
              <h3 class="ranking-name">{{ item.name }}</h3>
              <p class="ranking-stance">{{ item.stance }}</p>
              <div class="ranking-divider" />
              <div class="ranking-stats">
                <div>
                  <span class="ranking-stat-label">Avg</span>
                  <span class="ranking-stat-value">{{ item.average }}</span>
                </div>
                <div>
                  <span class="ranking-stat-label">Win Rate</span>
                  <span class="ranking-stat-value">{{ item.passRate }}</span>
                </div>
              </div>
            </article>
          </div>
        </div>
      </section>

      <!-- Task Focus -->
      <section id="tasks" class="tasks-section section-gap">
        <div class="container">
          <div class="section-heading section-heading--row">
            <span class="section-heading-label">任务</span>
            <h2 class="section-title">{{ story.taskSectionTitle }}</h2>
          </div>
          <div class="task-focus-grid">
            <article class="task-focus-strip animate-in" v-for="item in story.taskFocus" :key="item.taskId">
              <div class="tf-meta">
                <span class="tf-task-label">{{ item.taskLabel }}</span>
                <span class="tf-leader">{{ item.leader }}</span>
              </div>
              <p class="tf-task-name">{{ item.taskName }}</p>
              <div class="tf-score">
                <span class="tf-verdict">{{ item.verdict }}</span>
                <span class="tf-score-num">{{ item.score }}</span>
              </div>
            </article>
          </div>
        </div>
      </section>

      <!-- Failure Dossier -->
      <section id="failures" class="failures-section section-gap">
        <div class="container">
          <div class="section-heading section-heading--row">
            <span class="section-heading-label">风险</span>
            <h2 class="section-title">{{ story.failureSectionTitle }}</h2>
          </div>
          <div class="failure-list">
            <div class="failure-row" v-for="item in story.failureDossier" :key="item.label">
              <span class="failure-num">{{ item.num }}</span>
              <div>
                <p class="failure-label">{{ item.label }}</p>
                <p class="failure-desc">{{ item.description }}</p>
              </div>
              <span class="failure-models">{{ item.affectedModels }}</span>
            </div>
          </div>
        </div>
      </section>

      <!-- Evidence Rail -->
      <section id="evidence" class="evidence-section section-gap">
        <div class="container">
          <div class="section-heading section-heading--row">
            <span class="section-heading-label">记录</span>
            <h2 class="section-title">{{ story.evidenceSectionTitle }}</h2>
          </div>
          <div class="evidence-rail">
            <article class="evidence-card" v-for="item in story.evidenceDossiers" :key="item.runId">
              <div class="evidence-card-topbar" :class="{ fail: item.isFailure }" />
              <div class="evidence-card-body">
                <div class="ev-topline">
                  <span class="ev-model">{{ item.modelName }}</span>
                  <span class="ev-tag" :class="{ fail: item.isFailure }">{{ item.failureLabel }}</span>
                </div>
                <p class="ev-task">{{ item.taskLabel }}</p>
                <blockquote class="ev-excerpt">{{ item.excerpt }}</blockquote>
                <div class="ev-score">{{ item.score }}</div>
              </div>
            </article>
          </div>
        </div>
      </section>

      <!-- Verdict -->
      <section id="verdict" class="verdict-section section-gap">
        <div class="verdict-canvas-wrap">
          <PretextStageCanvas :stage="story.verdict.stage" />
        </div>
        <div class="verdict-content container">
          <p class="verdict-recommendation">{{ story.verdict.recommendation }}</p>
          <p class="verdict-summary">{{ story.verdict.summary }}</p>
          <p class="verdict-callout">{{ story.verdict.callout }}</p>
        </div>
      </section>
    </main>
  </div>
</template>
