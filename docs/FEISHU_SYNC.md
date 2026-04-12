# OpenClaw Model Arena · 评测系统说明

> 本文档为 Arena Phase 4 飞书文档同步任务而建，记录题库结构、评测方法、模型计划，供长期参考。
> 
> 更新时间：2026-04-12

---

## 一、项目概览

**OpenClaw Model Arena** 是针对 OpenClaw Agent 运行时能力的一套客观量化评测系统。

- **Repo**：`https://github.com/EASYGOING45/tenet-openclaw-arena`
- **前端展示**：`https://1449b451.tenet-openclaw-arena.pages.dev`（Secrets 配置完成后自动恢复部署）
- **架构**：Vue 3 前端（Vite + TypeScript）+ Hono 后端（SQLite）+ Python Benchmark Runner
- **最新验证**：backend 运行于 `:3000`，API 响应正常

---

## 二、题库结构

**总计 18 道任务**，覆盖 **6 个能力维度**，每个维度有对应权重。

| 能力维度 | 权重 | 任务数 | 说明 |
|---|---|---|---|
| Tool Chain（工具链） | 25% | 4 | 工具调用顺序、参数质量、错误处理 |
| Skill Dispatch（技能调度） | 15% | 4 | 在正确时机调用正确的 skill |
| CLI Competence（命令行能力） | 15% | 3 | bash/git/npm/wrangler 等操作 |
| Computer Use（浏览器自动化） | 15% | 2 | 浏览器操作、截图、UI 自动化 |
| Self-Correction（自我修正） | 15% | 3 | 失败后分析日志并自主修复 |
| Delegation（任务分发） | 15% | 2 | 多任务并行调度与结果聚合 |

### 完整任务列表

#### Skill Dispatch（4题）
1. **skill-dispatch-001** · 需求分析阶段正确调用 `brainstorming` skill
2. **skill-dispatch-002** · Bug 报告后正确调用 `systematic-debugging` skill 而非直接修复
3. **skill-dispatch-003** · 需求明确后正确调用 `frontend-design` 进行设计
4. **skill-dispatch-004** · 任务完成后正确调用 `verification` skill 进行验收

#### Tool Chain（4题）
5. **tool-chain-001** · 先读取文件，理解内容、修改、验证的完整工具链
6. **tool-chain-002** · 信息搜索后正确处理多个 URL 的完整链路
7. **tool-chain-003** · 执行命令解析输出并写入文件的完整数据处理链
8. **tool-chain-004** · 读取多个文件对比差异并输出对比报告

#### CLI Competence（3题）
9. **cli-001** · 完整的 Git 提交流程
10. **cli-002** · 完整的 Cloudflare Wrangler 部署流程
11. **cli-003** · 正确的依赖安装和版本验证流程

#### Computer Use（2题）
12. **computer-001** · 用 Playwright 自动化打开网页并截图验证
13. **computer-002** · 在多个相关网页间导航并提取整合信息

#### Self-Correction（3题）
14. **self-correction-001** · 命令执行失败后分析错误并正确重试
15. **self-correction-002** · 路径错误后能自动找到正确路径并继续执行
16. **self-correction-003** · API 超时后能分析原因并制定重试策略

#### Delegation（2题）
17. **delegation-001** · 正确使用 `sessions_spawn` 并行调度多个子任务
18. **delegation-002** · 串行依赖的多步骤任务正确分解并用 subagent 执行

---

## 三、评测方法

### 计分机制

每道任务独立评分，最终得分按维度权重加权平均：

```
总得分 = Σ(维度得分 × 维度权重)
```

- 单任务：pass/fail 二值（辅以 evidence 证据截取）
- 评分事件：benchmark runner 通过检测 `passed` / `failed` 自定义事件判定
- 归一化：原始得分标准化为 0-100 分制

### Benchmark Runner

- **入口脚本**：`scripts/run_benchmark.py`
- **DB**：SQLite（`backend/data/arena.db`），三表结构：`agents` / `tasks` / `runs`
- **同步脚本**：`scripts/sync_tasks.py`（YAML 题库 → SQLite）
- **最新运行数据目录**：`data/runs/arena-20260405t2200z/`

### 最新评测结果（2026-04-05，6题子集）

| 模型 | 平均分 | 通过数 |
|---|---|---|
| MiniMax M2.7 | 98.5 | 5/6 |
| GPT-5.4 | 90.0 | 4/6 |
| Kimi K2.5 | 81.33 | 2/6 |

> 完整 18 题全量 benchmark 尚未执行，待 CI / Secrets 就绪后触发。

---

## 四、已注册模型

| Arena ID | 原始模型 | 提供商 | License | 输入价格（元/千token） | 输出价格 |
|---|---|---|---|---|---|
| arena-m27 | MiniMax-M2.7 | MiniMax | Proprietary | 0.3 | 1.2 |
| arena-k2p5 | Kimi-K2P5 | Moonshot | Proprietary | — | — |
| arena-gpt54 | GPT-5.4 | OpenAI | Proprietary | — | — |

> **下一步**：待接入 MiniMax-M2.5（模型 ID 待确认）

---

## 五、CI / 部署状态

- **GitHub Actions**：✅ Python 32 tests / Backend build / Frontend build+test 全部通过
- **Cloudflare Pages 部署**：⚠️ 阻塞中（缺少 `CLOUDFLARE_API_TOKEN` + `CF_ACCOUNT_ID` GitHub Secrets）
- **手动触发 benchmark**：Secrets 就绪后可通过 GitHub Actions `workflow_dispatch` 或本地 `scripts/run_benchmark.py` 触发

### 待用户手动完成（唯一阻塞）

1. 在 GitHub repo `Settings → Secrets` 中添加：
   - `CLOUDFLARE_API_TOKEN`：Cloudflare API Token（Edit Cloudflare Workers / Pages 权限）
   - `CF_ACCOUNT_ID`：Cloudflare Account ID
2. CI 自动重跑 → Deploy 步骤恢复 → Pages 恢复在线

---

## 六、相关文档

- 项目计划：`docs/PLAN.md`
- 进度总结：`docs/PROGRESS_SUMMARY.md`
- Phase 4 任务卡：`docs/TASK_CARDS/TASK_phase4_publish_path_and_repo_ownership.md`
- GitHub Repo：https://github.com/EASYGOING45/tenet-openclaw-arena

---

*本文档由菲比自动同步生成 · 2026-04-12*
