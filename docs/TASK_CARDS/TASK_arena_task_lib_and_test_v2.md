# TASK_arena_task_lib_and_test_v2 - 题库完善 & 测试流程增强

**状态**：✅ 完成
**创建时间**：2026-04-25 21:17
**完成时间**：2026-04-26 01:35 CST（commit `9c77724`）
**主人**：易行
**执行代理**：codex（ACP）

---

## 🎯 任务目标

完善 OpenClaw Model Arena 的题库体系和测试流程，重点两项：

### 目标 A：题库 v2 — 让 Phase 2 YAML 任务接入后端 API

**现状问题：**
- Backend (`init.ts`) 只 hardcode 了 6 个旧任务（coding-loop / readme-audit 等）存入 SQLite
- `data/benchmark/tasks/` 下已有完整的 18 个 YAML 任务（6维度），但**未接入后端**
- Phase 1 runner (`benchmark_tasks.json`) 和 Phase 2 runner（YAML）使用不同的任务定义

**目标：**
- 新增 `backend/src/db/seed_yaml_tasks.ts` 脚本：从 `data/benchmark/tasks/_index.yml` 读取所有 18 个 YAML 任务，补全 SQLite tasks 表
- 修改 `backend/src/db/init.ts`：增加 `--reinit-tasks` CLI 参数，支持只重载任务不重建数据库
- 修改 `backend/src/routes/tasks.ts`：返回时附加 `capability`（维度）和 `difficulty` 字段（来自 YAML metadata）
- 修改 `backend/src/routes/results.ts`：确保 task_id 映射到新的 YAML task_id（如 `skill-dispatch-001`）
- 新增 `scripts/sync_yaml_tasks_to_db.py`：独立的任务同步脚本，可单独运行
- 验证：`curl http://localhost:3000/api/tasks` 应返回 18 个任务，包含 capability 和 difficulty 字段

### 目标 B：测试流程增强

**现状问题：**
- API 集成测试缺失（后端 API endpoint 没有直接测试）
- 评分 pipeline 的 edge case 测试覆盖不足
- 前端 LeaderboardPage 的筛选器是假的（`filteredLeaderboard` 直接返回全部）

**目标：**
- 新增 `tests/test_api_routes.py`：测试 backend `/api/tasks`、`/api/results`、`/api/leaderboard` 的关键路径（用 `httpx` 或 `requests` 发真实 HTTP 请求）
- 增强 `tests/test_scoring.py`：补充以下 case
  - transcript 为空字符串时的评分
  - score 超出 0-100 范围的边界
  - failure_tag 未知时的 fallback 行为
- 修复 `app/src/components/pages/LeaderboardPage.vue` 的筛选逻辑：让 Category 和 License 筛选真正生效
- 新增 `tests/test_leaderboard_filters.test.ts`：测试筛选逻辑（可用 Vitest）
- 所有测试必须通过后再提交

---

## 📁 涉及文件

### 目标 A（题库）

**创建：**
- `backend/src/db/seed_yaml_tasks.ts` — YAML → SQLite 任务导入脚本
- `scripts/sync_yaml_tasks_to_db.py` — 独立同步脚本（Python）

**修改：**
- `backend/src/db/init.ts` — 增加 `--reinit-tasks` 参数
- `backend/src/routes/tasks.ts` — 返回 capability / difficulty 字段
- `backend/src/routes/results.ts` — 确保 task_id 映射正确
- `backend/src/db/schema.ts` — 检查 tasks 表 schema 是否需要扩展

### 目标 B（测试）

**创建：**
- `tests/test_api_routes.py` — API 集成测试
- `app/src/components/pages/LeaderboardPage.test.ts` — 前端筛选器测试

**修改：**
- `tests/test_scoring.py` — 补充 edge case
- `app/src/components/pages/LeaderboardPage.vue` — 修复筛选逻辑

---

## ✅ 验收标准

### 目标 A
- [x] `curl http://localhost:3000/api/tasks` 返回 24 个任务（含 18 YAML 任务）
- [x] 每个任务含 `id`、`name`、`category`、`difficulty`、`capability`（维度）字段
- [x] `python3 scripts/sync_yaml_tasks_to_db.py` 运行成功，无报错
- [x] Backend 重启后数据持久化正常

### 目标 B
- [x] `uv run pytest tests/test_api_routes.py -v` — 18 个 API 集成测试全部通过
- [x] `uv run pytest tests/test_scoring.py -v` — 所有现有测试 + 新增 7 个 edge case 通过
- [x] `npm test`（app 目录）全部通过 — 32 个前端测试（含新增 27 个筛选器测试）
- [x] `LeaderboardPage` 筛选器：License + Category 双重筛选真正生效

---

## ⚠️ 注意事项

- Backend 在 `localhost:3000`，测试需要先确保 backend 运行中
- YAML 任务的 `task_id` 格式是 `skill-dispatch-001`（含横线），注意和旧 task_id 格式区分
- 后端用 TypeScript + Hono，前端用 Vue 3 + Vitest，Python 测试用 pytest
- 不要删除旧的 6 任务 seed 数据（保持向后兼容），新任务**追加**进去

---

## 执行建议

1. 先做目标 A（题库），因为目标 B 的 API 测试依赖正确的任务数据
2. Backend 重启用：`cd backend && npm run dev` 或 `node dist/index.js`
3. 测试筛选器时不需要 backend 运行，纯前端逻辑
