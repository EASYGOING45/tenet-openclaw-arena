# TASK_phase4_publish_path_and_repo_ownership - 发布路径与仓库归属决策

**状态**：🔄 进行中（Phase 4 收尾）
**创建时间**：2026-04-06 13:38
**更新时间**：2026-04-12 13:30

## 🎯 任务目标

为 OpenClaw Model Arena 确定可持续的发布与验证路径，避免项目停留在“结果已完成、但无法形成正式交付链路”的状态。

## 背景

当前项目已经完成：
- benchmark runner、归一化、站点数据生成
- 结果站点重构与本地验证
- 全量 benchmark 对比结果产出

但本次中段巡检确认：
- `Projects/openclaw-model-arena` 目前不是独立 git 仓库
- 项目内没有 `wrangler.toml` / `wrangler.json` / `wrangler.jsonc`
- 因此 `scripts/project_execute.sh` 的 gh / wrangler 验证链路当前无法真正落地

## 需要拍板的问题

1. **仓库归属**
   - 方案 A：把 `Projects/openclaw-model-arena` 升级为独立 repo，后续走标准 gh 流程
   - 方案 B：继续作为工作区内项目，仅保留本地 docs + artifact 管理

2. **发布方式**
   - 方案 A：Cloudflare Pages（最适合当前静态 evidence site）
   - 方案 B：其他静态托管
   - 方案 C：不公开部署，仅保留本地构建与导出归档

3. **验收链路**
   - 若公开部署：补 `wrangler` / CI / 发布文档
   - 若仅本地：补导出/归档说明，明确不用 gh / wrangler 作为必经验证

## 建议默认方向

优先建议：**独立 repo + Cloudflare Pages**。

理由：
- 项目已经具备清晰的“可展示结果页”属性
- 现有数据产物和前端构建都适合静态托管
- 这样后续 `project_execute.sh` 里的 gh / wrangler 验证才有实际意义

## 验收标准

- [x] 明确 repo 归属决策 → 新仓库 `https://github.com/EASYGOING45/tenet-openclaw-arena`
- [x] 明确发布目标 → Cloudflare Pages
- [x] GitHub Actions CI 配置 → ✅ 推送并验证（Python 32 tests ✅ / Backend build ✅ / Frontend build+test ✅）
  - ⚠️ Deploy 步骤因缺少 `CLOUDFLARE_API_TOKEN` + `CF_ACCOUNT_ID` 而失败（预期阻塞，需用户手动配置）
  - CI history: 5 次 push，Deploy 均 failure（secrets 缺失）
- [x] 清理 untracked plan artifact（`docs/superpowers/plans/`）
- [x] 飞书文档：题库说明/评测方法/模型计划（本文档）
- [ ] **阻塞：需手动配置 GitHub Secrets**：`CLOUDFLARE_API_TOKEN` + `CF_ACCOUNT_ID`（配置好后 CI Deploy 自动恢复）
- [ ] 全量 benchmark 运行（18任务 × 3 agents，可手动 `workflow_dispatch` 或 CI 触发）

## 已完成记录

- 2026-04-07：确定使用独立 repo `tenet-openclaw-arena` + Cloudflare Pages
- 2026-04-07 11:57：首次 push 到 main 分支
- 2026-04-07 12:16：提交 utility scripts（run_arena_m27.sh 等）

## 本次巡检记录

- 2026-04-06 13:30 CST：执行 `scripts/project_execute.sh openclaw-model-arena`，docs 骨架检查通过。
- 由于缺少独立 git / wrangler 配置，本次未进行有效 gh / Cloudflare 验证；该问题已上升为当前主阻塞。

### 2026-04-12 13:30 CST（中段巡检）
- ✅ 确认 Arena backend 仍在运行（`:3000`，`npm start`）
- ✅ CI 已完整推送（4轮迭代），Test + Build 全部通过，Deploy 步骤因 Secrets 缺失而失败（预期）
- ✅ 清理 stale plan artifact（`docs/superpowers/plans/2026-04-12-arena-phase4-ci-cfd-pages.md`）
- ✅ 完成飞书文档同步（本文档）
- ⚠️ 当前唯一阻塞：**需用户手动在 GitHub repo Secrets 配置 `CLOUDFLARE_API_TOKEN` + `CF_ACCOUNT_ID`**
- 🔜 CI Deploy 恢复后，可手动或 CI 触发全量 benchmark
