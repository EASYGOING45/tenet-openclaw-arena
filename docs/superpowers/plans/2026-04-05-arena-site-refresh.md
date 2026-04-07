# Arena Site Refresh Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rebuild the benchmark site into a Chinese, Pretext-inspired editorial page while preserving the existing benchmark payload and evidence-driven structure.

**Architecture:** Keep the current Vite + Vue app and scored `site-data.json` pipeline intact, but expand the normalized run shape so the UI can surface richer evidence such as task titles, excerpts, and transcript previews. Rewrite the landing page copy and section layouts into a Chinese editorial narrative with stronger typography, asymmetry, and evidence-first storytelling.

**Tech Stack:** Vue 3, TypeScript, Vite, Vitest, CSS variables

---

### Task 1: Expand the payload shape for richer storytelling

**Files:**
- Modify: `app/src/types.ts`
- Modify: `app/src/data/loadSiteData.ts`
- Modify: `app/src/data/loadSiteData.test.ts`

- [ ] **Step 1: Write the failing test**

```ts
expect(result.runs[0].taskTitle).toBe('Delegate a bounded edit to ACPX/Codex and continue')
expect(result.runs[0].finalText).toContain('Request timed out')
expect(result.runs[0].transcriptPreview).toContain('Benchmark task')
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npm test -- --run app/src/data/loadSiteData.test.ts`
Expected: FAIL because the normalized run does not yet expose `taskTitle`, `finalText`, or `transcriptPreview`.

- [ ] **Step 3: Write minimal implementation**

```ts
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
```

```ts
return {
  runId: ...,
  taskId: ...,
  taskTitle: typeof record.task_title === 'string' ? record.task_title : undefined,
  category: typeof record.category === 'string' ? record.category : undefined,
  finalText: typeof record.final_text === 'string' ? record.final_text : undefined,
  transcriptPreview:
    typeof asRecord(record.transcript).preview === 'string'
      ? (asRecord(record.transcript).preview as string)
      : undefined,
  ...
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `npm test -- --run app/src/data/loadSiteData.test.ts`
Expected: PASS

### Task 2: Rebuild the page into a Chinese editorial layout

**Files:**
- Modify: `app/src/App.vue`
- Modify: `app/src/components/HeroVerdict.vue`
- Modify: `app/src/components/MethodSection.vue`
- Modify: `app/src/components/ScoreboardSection.vue`
- Modify: `app/src/components/FailureAtlasSection.vue`
- Modify: `app/src/components/AcpxSection.vue`
- Modify: `app/src/components/EvidenceReaderSection.vue`
- Modify: `app/src/components/VerdictSection.vue`
- Modify: `app/src/styles/theme.css`

- [ ] **Step 1: Rewrite the page copy model in Chinese**

```ts
const heroHeadline = computed(() => '别凭感觉选模型，要看它在 OpenClaw 里是不是真的会动手。')
const verdictHeadline = computed(() => '本轮结论：MiniMax M2.7 第一，GPT-5.4 第二，Kimi K2.5 不适合做主执行模型。')
```

- [ ] **Step 2: Reshape the sections around an editorial narrative**

```vue
<HeroVerdict ... />
<MethodSection ... />
<ScoreboardSection ... />
<FailureAtlasSection ... />
<AcpxSection ... />
<EvidenceReaderSection ... />
<VerdictSection ... />
```

- [ ] **Step 3: Replace the current theme with a Pretext-inspired visual system**

```css
:root {
  --paper: oklch(...);
  --ink: oklch(...);
  --accent: oklch(...);
  --display: "Instrument Serif", serif;
  --body: "IBM Plex Sans", sans-serif;
}
```

```css
.hero-copy h1 {
  font-size: clamp(4rem, 12vw, 8rem);
  line-height: 0.88;
}
```

- [ ] **Step 4: Keep the layout responsive without amputating sections**

Run: `npm run build`
Expected: PASS with the new layout compiling cleanly for production.

### Task 3: Preserve verification and update project-facing docs

**Files:**
- Modify: `app/src/App.test.ts`
- Modify: `docs/PROGRESS_SUMMARY.md`

- [ ] **Step 1: Update the app-level test so it still checks the composition contract**

```ts
expect(source).toContain('HeroVerdict')
expect(source).toContain('ScoreboardSection')
expect(source).toContain('OpenClaw')
```

- [ ] **Step 2: Record the redesign in project docs**

```md
- Results website refreshed into a Chinese editorial presentation with Pretext-inspired direction while preserving the benchmark payload and evidence sections.
```

- [ ] **Step 3: Run the full frontend verification**

Run: `npm test && npm run build`
Expected: PASS
