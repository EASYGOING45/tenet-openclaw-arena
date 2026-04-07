# TASK_phase4_publish_path_and_repo_ownership - 发布路径与仓库归属决策

**状态**：🟡待拍板
**创建时间**：2026-04-06 13:38
**更新时间**：2026-04-07 07:01

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

- [ ] 明确 repo 归属决策
- [ ] 明确发布目标
- [ ] 新建对应执行任务卡（如部署 / CI / 发布文档）
- [ ] 让统一执行链中的 gh / wrangler 验证对本项目真正生效

## 本次巡检记录

- 2026-04-06 13:30 CST：执行 `scripts/project_execute.sh openclaw-model-arena`，docs 骨架检查通过。
- 由于缺少独立 git / wrangler 配置，本次未进行有效 gh / Cloudflare 验证；该问题已上升为当前主阻塞。
