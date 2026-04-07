# Task List

- [x] Phase 1: scaffold project and task corpus
- [x] Phase 2: benchmark runner and scoring pipeline
- [x] Phase 3: results website and verification
- [ ] Phase 4: publishing, repo ownership, and deployment handoff

## Task 10 Integration Wrap-Up

- [x] Reconcile the three arena agents against live OpenClaw config before benchmark runs
- [x] Build a real run matrix with concrete per-task prompts and runtime fixtures
- [x] Persist raw run metadata needed for later normalization and site display
- [x] Make `python3 Projects/openclaw-model-arena/scripts/run_benchmark.py` runnable from workspace root
- [x] Add safe generated-artifact cleanup in `scripts/reset_run.py` without deleting `.gitkeep`
- [x] Add orchestration coverage in `tests/test_run_benchmark.py`
- [x] Verify Python tests, frontend tests/build, and a 1-task live smoke benchmark
- [x] Run the full multi-agent benchmark sweep and publish comparative results

## Phase 4 Focus

- [ ] Decide whether `Projects/openclaw-model-arena` should become an independent git repo or remain a workspace-only artifact
- [ ] Decide the public publishing path for the evidence site (Cloudflare Pages / other static host / local-only archive)
- [ ] Add a release-oriented task card and acceptance checklist for the chosen publish path
- [ ] After the above decision, wire the matching gh / wrangler verification path into the project workflow
