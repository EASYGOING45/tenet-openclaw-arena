# Arena Stage Reset Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rebuild the OpenClaw arena site into a stage-like benchmark experience that uses `@chenglou/pretext` for real manual text layout instead of treating the redesign as a CSS-only reskin.

**Architecture:** Keep the existing Vite + Vue + `site-data.json` pipeline, but refactor the single-file landing page into a small presentation system. Introduce a `PretextStageCanvas` hero that lays out runtime evidence text with `@chenglou/pretext` on canvas, then reorganize the rest of the page into editorial strips for ranking, failures, evidence, and verdicts with stronger motion and a Persona-inspired black/cyan stage language.

**Tech Stack:** Vue 3, TypeScript, Vite, Vitest, CSS variables, Canvas 2D, `@chenglou/pretext`

---

## Creative Direction

**Visual thesis:** A midnight control room meets a theater poster: black velvet field, cyan signal light, acid-gold accents, gigantic condensed labels, and a live text stage that feels computed rather than decorated.

**Content plan:** Hero stage, ranking billboards, failure atlas, evidence reel, final verdict.

**Interaction thesis:**
- The hero canvas should feel alive through pulsing scanlines and slow parallax drift.
- Key sections should reveal with staggered motion so the page reads like acts in a performance.
- The evidence reel should auto-pan horizontally on large screens to create a sense of continuous runtime playback.

### Task 1: Lock the new story model with failing tests

**Files:**
- Create: `app/src/presentation/createArenaStory.test.ts`
- Modify: `app/src/App.test.ts`

- [ ] **Step 1: Write the failing story test**

```ts
expect(story.hero.kicker).toContain('OpenClaw')
expect(story.hero.headline).toContain('真的会执行')
expect(story.hero.stageWords[0]).toBe('MiniMax M2.7')
expect(story.verdict.recommendation).toContain('GPT-5.4')
```

- [ ] **Step 2: Run test to verify it fails**

Run: `npm test -- --run app/src/presentation/createArenaStory.test.ts app/src/App.test.ts`
Expected: FAIL because the story builder and the new stage composition do not exist yet.

- [ ] **Step 3: Expand the composition contract test**

```ts
expect(source).toContain('PretextStageCanvas')
expect(source).toContain('rankingBillboards')
expect(source).toContain('evidenceRail')
expect(source).toContain('failureAtlas')
```

- [ ] **Step 4: Re-run tests to confirm red**

Run: `npm test -- --run app/src/presentation/createArenaStory.test.ts app/src/App.test.ts`
Expected: FAIL with missing exports / missing component strings.

### Task 2: Add Pretext-powered layout primitives

**Files:**
- Modify: `app/package.json`
- Create: `app/src/stage/renderPretextStage.ts`
- Create: `app/src/components/PretextStageCanvas.vue`

- [ ] **Step 1: Install the runtime dependency**

Run: `npm install @chenglou/pretext`
Expected: `package.json` and lockfile record the dependency.

- [ ] **Step 2: Implement the manual layout helper**

```ts
setLocale('zh-CN')
const prepared = prepareWithSegments(stageText, font, { wordBreak: 'keep-all' })
const range = layoutNextLineRange(prepared, cursor, lineWidth)
const line = materializeLineRange(prepared, range)
```

- [ ] **Step 3: Build the hero canvas wrapper**

```vue
<canvas ref="canvasRef" class="stage-canvas"></canvas>
```

```ts
watchEffect(() => renderStage(canvasRef.value, props.stage))
```

- [ ] **Step 4: Verify the stage code compiles**

Run: `npm test -- --run app/src/presentation/createArenaStory.test.ts`
Expected: PASS for story tests after the new story/layout primitives land.

### Task 3: Rewrite the page around stage sections

**Files:**
- Create: `app/src/presentation/createArenaStory.ts`
- Modify: `app/src/App.vue`

- [ ] **Step 1: Create a story builder from raw site data**

```ts
const rankingBillboards = rankedModels.map((model, index) => ({
  rank: index + 1,
  name: model.model.name,
  average: formatScore(model.averageScore),
  passRate: formatPercent(model.passRate),
}))
```

- [ ] **Step 2: Replace the old panel grid with stage sections**

```vue
<section class="hero-stage">
  <PretextStageCanvas :stage="story.hero.stage" />
</section>
<section class="ranking-billboards">...</section>
<section class="failure-atlas">...</section>
<section class="evidence-rail">...</section>
<section class="final-verdict">...</section>
```

- [ ] **Step 3: Keep the loading/error behavior intact**

```ts
if (loadError.value) {
  return fallbackStory(loadError.value)
}
```

- [ ] **Step 4: Re-run app contract tests**

Run: `npm test -- --run app/src/App.test.ts`
Expected: PASS

### Task 4: Replace the visual system and add motion

**Files:**
- Modify: `app/src/styles/theme.css`

- [ ] **Step 1: Define the new tokens**

```css
:root {
  --bg: oklch(0.08 0.02 250);
  --bg-soft: oklch(0.13 0.03 247);
  --cyan: oklch(0.83 0.19 209);
  --gold: oklch(0.8 0.14 86);
  --display: "Bebas Neue", "Oswald", sans-serif;
  --body: "Noto Serif SC", serif;
}
```

- [ ] **Step 2: Turn the first viewport into a poster**

```css
.hero-stage {
  min-height: 100svh;
  display: grid;
  grid-template-columns: 0.9fr 1.1fr;
}
```

- [ ] **Step 3: Add restrained but visible motion**

```css
.reveal {
  animation: rise-in 700ms cubic-bezier(.22, 1, .36, 1) both;
}
```

- [ ] **Step 4: Verify responsive layout**

Run: `npm run build`
Expected: PASS with responsive CSS compiled successfully.

### Task 5: Ship verification and project docs

**Files:**
- Modify: `docs/PLAN.md`
- Modify: `docs/PROGRESS_SUMMARY.md`

- [ ] **Step 1: Record the redesign direction in project docs**

```md
- Phase 3 now centers a Pretext-powered stage hero, billboard ranking layout, and Persona-inspired motion language.
```

- [ ] **Step 2: Run full frontend verification**

Run: `npm test && npm run build`
Expected: PASS
