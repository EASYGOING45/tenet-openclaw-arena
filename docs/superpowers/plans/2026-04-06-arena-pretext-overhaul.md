# Arena Pretext Overhaul Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Rebuild the OpenClaw arena frontend into a dramatic benchmark poster that uses `@chenglou/pretext` as a real typographic engine rather than a decorative reference.

**Architecture:** Keep the existing Vite + Vue + `site-data.json` pipeline, but replace the current stage shell with a new presentation system that treats the page like an editorial campaign: a full-bleed hero canvas, tape-like score strips, asymmetrical ranking acts, task focus panels, transcript dossiers, and a closing verdict. Move more storytelling logic into `createArenaStory.ts` so the Vue template stays compositional and the canvas renderer can stay focused on typography, density, and motion.

**Tech Stack:** Vue 3, TypeScript, Vite, Vitest, CSS variables, Canvas 2D, `@chenglou/pretext`

---

## Creative Direction

**Visual thesis:** A benchmark control room printed like a Persona poster: electric blue floodlight, black stage void, ivory paper, hazard-gold tape, slashed diagonals, and dense pretext-set typography that feels measured instead of guessed.

**Content plan:** Poster hero, live score ribbon, ranking acts, task focus wall, failure dossier, transcript evidence rail, final verdict.

**Interaction thesis:**
- The hero should feel alive with slow drift, scanline shimmer, and layered typography that reflows like a stage cue sheet.
- Section headers should arrive like act cards, using staggered reveals and clipped separators instead of generic card entrances.
- Transcript evidence should feel like a moving film strip on desktop while remaining readable stacks on mobile.

## File Map

- Modify: `app/src/presentation/createArenaStory.ts`
- Modify: `app/src/presentation/createArenaStory.test.ts`
- Modify: `app/src/App.vue`
- Modify: `app/src/App.test.ts`
- Modify: `app/src/stage/renderPretextStage.ts`
- Modify: `app/src/components/PretextStageCanvas.vue`
- Modify: `app/src/styles/theme.css`
- Modify: `docs/PLAN.md`
- Modify: `docs/INTRO.md`
- Modify: `docs/PROGRESS_SUMMARY.md`

### Task 1: Lock the new story contract in tests

**Files:**
- Modify: `app/src/presentation/createArenaStory.test.ts`
- Modify: `app/src/App.test.ts`

- [ ] Add failing assertions for the new story shape: hero manifest lines, score ribbon content, task focus blocks, failure dossier entries, evidence dossier labels, and stronger verdict copy.
- [ ] Update the app contract test so it expects the new composition markers such as `score-ribbon`, `task-focus-wall`, `evidence-dossiers`, and `closing-manifesto`.
- [ ] Run `npm test -- --run src/presentation/createArenaStory.test.ts src/App.test.ts` from `app/`.
- [ ] Confirm the suite fails for the expected missing structure rather than syntax or path errors.

### Task 2: Rebuild the story layer around editorial sections

**Files:**
- Modify: `app/src/presentation/createArenaStory.ts`

- [ ] Expand the story builder so it computes a more expressive hero, a model ranking act for each contender, grouped task-focus summaries, richer failure dossiers, and transcript evidence items with short captions.
- [ ] Keep the logic pure and derived entirely from `SiteData`, so loading, fallback states, and the public JSON contract stay stable.
- [ ] Preserve resilient behavior for empty data by returning graceful placeholders instead of breaking the template.
- [ ] Re-run `npm test -- --run src/presentation/createArenaStory.test.ts` from `app/` and make it pass before touching the page structure.

### Task 3: Replace the page composition with a poster-style layout

**Files:**
- Modify: `app/src/App.vue`
- Modify: `app/src/App.test.ts`

- [ ] Rebuild the template into a full-bleed poster flow with a hero manifesto, score ribbon, ranking acts, task focus wall, failure dossier, transcript evidence rail, and closing verdict.
- [ ] Keep data loading and fallback logic intact while simplifying the template so each section only renders what the story layer already decided.
- [ ] Reduce card dependency: prefer strips, dividers, tapes, and columns over boxed dashboards.
- [ ] Re-run `npm test -- --run src/App.test.ts` from `app/` and make the updated composition contract pass.

### Task 4: Rework the Pretext stage and full visual system

**Files:**
- Modify: `app/src/stage/renderPretextStage.ts`
- Modify: `app/src/components/PretextStageCanvas.vue`
- Modify: `app/src/styles/theme.css`

- [ ] Redesign the canvas renderer around larger scale typography, layered script columns, diagonal light planes, and a clearer relationship between hero copy and the `pretext`-measured text field.
- [ ] Replace the current theme with a new token set and responsive layout language that mirrors the reference sites: darker poster field, brighter blue anchor, ivory body text, gold utility accents, and stronger typographic contrast.
- [ ] Add purposeful motion for hero presence, section reveal timing, and horizontal evidence movement without letting mobile performance collapse.
- [ ] Run `npm run build` from `app/` to verify the composition compiles cleanly after the visual reset.

### Task 5: Verify and document the new direction

**Files:**
- Modify: `docs/PLAN.md`
- Modify: `docs/INTRO.md`
- Modify: `docs/PROGRESS_SUMMARY.md`

- [ ] Update project docs so Phase 3 reflects the new Pretext-first poster direction and its evidence-driven section flow.
- [ ] Run `npm test` and `npm run build` from `app/`.
- [ ] Capture local browser validation for desktop and mobile so the final claim is backed by rendered evidence, not only by static tests.
