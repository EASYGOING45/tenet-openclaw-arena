# OpenClaw Capability Arena

> 不是"模型谁更强"，而是"模型在 OpenClaw Runtime 里能干得多好"。

**实时在线 Benchmark 系统**：通过监听 Agent 执行过程中的真实行为事件（skill 调用、工具链、subagent 调度等），对模型在 OpenClaw 工具生态下的实际工作能力进行量化评分。

**在线 Arena**：https://1449b451.tenet-openclaw-arena.pages.dev

---

## 核心思路

传统 benchmark（HumanEval、MMLU）看答案对错。

我们看**行为过程**：

```
给模型一个任务
    ↓
监听执行过程中的所有行为事件
    ↓
    skill_dispatch（调用了 brainstorming？）
    tool_call read/edit/write/exec
    subagent_spawn（启动了 subagent？）
    exec_command（执行了什么 shell 命令？）
    reasoning_output（有没有推理分析？）
    self_corrected（失败后自愈？）
    ...
    ↓
对照 YAML reference 逐条打分
```

**为什么看行为比看答案更有意义？**
- 同一个任务，解法往往不唯一
- "调了 brainstorming skill" 比 "给出了某个答案" 更能说明能力
- 过程透明 → 可以诊断模型弱点（工具链弱？自愈差？调度能力弱？）

---

## 架构

```
┌─────────────────────────────────────────────┐
│  Python Benchmark Runner                     │
│  ┌─────────────┐  ┌──────────┐  ┌────────┐ │
│  │openclaw_runner│→│event_parser│→│ scorer │ │
│  └─────────────┘  └──────────┘  └────────┘ │
│         ↓              ↓             ↓     │
│  subprocess.run()   12种事件类型   YAML规则   │
│  openclaw agent    解析stdout    量化打分    │
└─────────────────────────────────────────────┘
         ↓
┌─────────────────────────────────────────────┐
│  Backend API（Hono + SQLite）               │
│  GET /api/leaderboard                       │
│  GET /api/results/:run_id                   │
└─────────────────────────────────────────────┘
         ↓
┌─────────────────────────────────────────────┐
│  Frontend（Vue 3 + Pretext 粒子动效）         │
│  Home 页 + Leaderboard 多维排名              │
└─────────────────────────────────────────────┘
```

---

## 快速开始

### 1. 安装依赖

```bash
cd app && npm install
cd ../backend && npm install
```

### 2. 跑 Benchmark（6 任务精简版 ≈ 10 分钟）

```bash
# 方式 A：直接跑（需配置 openclaw agents）
python3 run_6task_v2.py

# 方式 B：通过 runner 脚本跑
python3 -c "
import asyncio, json
from benchmark.parallel_runner import run_benchmark, load_yaml_tasks
from pathlib import Path

index = Path('data/benchmark/tasks/_index.yml')
tasks = load_yaml_tasks(index)
# 选6个维度各1题
selected = [t for t in tasks if t['task_id'] in {
    'skill-dispatch-001','tool-chain-001','cli-001',
    'computer-001','self-correction-001','delegation-001'
}]
result = asyncio.run(run_benchmark(
    agents=['arena-m27', 'arena-k2p5'],
    tasks=selected,
    max_workers=2,
    dry_run=False,
))
print(json.dumps(result, default=str, indent=2))
"
```

### 3. 跑全量 18 任务

```bash
python3 scripts/run_benchmark.py --mode phase2 --agents arena-m27,arena-k2p5
```

### 4. 本地预览前端

```bash
cd app && npm run preview -- --port 4173
```

---

## 题库结构

**18 个标准化 YAML 任务**，覆盖 6 大能力维度：

| 维度 | 任务数 | 考察点 | 示例任务 |
|---|---|---|---|
| Skill Dispatch | 4 | 在正确时机调用正确的 skill | 需求分析 → brainstorming |
| Tool Chain | 4 | 工具调用顺序、参数、错误处理 | read → edit → exec 验证 |
| CLI Competence | 3 | bash/git/npm/wrangler 操作 | 完整 Git 提交流程 |
| Computer Use | 2 | Playwright 浏览器自动化 | 截图 + 多页面导航 |
| Self-Correction | 3 | 失败后分析日志 + 自主修复 | exec 失败 → stderr 分析 → 重试 |
| Delegation | 2 | 多 subagent 并行调度 | sessions_spawn 并行跑多个任务 |

### 添加新任务

在对应维度目录下创建 YAML 文件，例如 `data/benchmark/tasks/skill_dispatch/skill-dispatch-005.yml`：

```yaml
task_id: skill-dispatch-005
schema_version: 1
title: 你的任务标题

capability: skill_dispatch    # 维度
difficulty: medium            # easy / medium / hard

tags:
  - skill_dispatch
  - your_tag

prompt:
  system: |
    You are an expert assistant running inside OpenClaw.
  user: |
    你的任务描述...

evaluation:
  type: behavior_trace
  timeout_seconds: 180        # 建议 ≥180s

  scoring:
    rules:
      - event: skill_dispatch
        condition: '"brainstorming" in line'
        score: +40
        note: "调用了 brainstorming skill"
      - event: tool_call
        condition: 'tool == "read"'
        score: +20
        note: "先读取文件"
      - event: completion_claim
        condition: "True"
        score: +10
        note: "声称完成"
    min_score: 0
    max_score: 100

  pass_threshold: 70
  fail_threshold: 40
```

---

## 事件类型

解析器从 `openclaw agent --json` 的 stdout 中识别以下 12 种行为事件：

| 事件类型 | 触发条件 | 示例 |
|---|---|---|
| `skill_dispatch` | 调用 skill（如 sessions_spawn） | `sessions_spawn`, `skill_invoked` |
| `tool_call` | 工具调用 | `read`, `edit`, `write`, `exec` |
| `subagent_spawn` | 启动 subagent | `spawn`, `subagent` |
| `exec_command` | 执行 shell 命令 | `git status`, `npm run build` |
| `error_occurred` | 出现错误 | `Error`, `failed`, `Exception` |
| `self_corrected` | 失败后自愈 | `retry`, `重试`, `recover` |
| `reasoning_output` | 推理/分析输出 | `reasoning`, `分析` |
| `completion_claim` | 声称完成 | `complete`, `done` |
| `verification_output` | 验证/检查输出 | `verify`, `验证` |
| `write_operation` | 写文件 | `写入文件`, `file written` |
| `retry_exec` | 重试执行 | `retry` 关键词 |
| `direct_code_write` | 直接写代码块 | 代码块 ``` 出现 |

---

## 注册新 Agent

```bash
# 在 OpenClaw workspace 中注册
openclaw agents register arena-myagent \
  --model <model_name> \
  --provider <provider>
```

当前已注册：

| Agent ID | 模型 | 用途 |
|---|---|---|
| `arena-gpt54` | GPT-5.4 | Benchmark 对比主力 |
| `arena-m27` | MiniMax-M2.7 | Benchmark 对比主力 |
| `arena-k2p5` | Kimi-K2P5 | Benchmark 对比主力 |
| `main` | MiniMax-M2.7 | 默认执行 agent |

---

## CI / 定时跑

配置 GitHub Actions 定时跑 benchmark：

```yaml
# .github/workflows/benchmark.yml
on:
  schedule:
    - cron: '0 6 * * *'  # 每天 06:00 UTC
  workflow_dispatch:       # 也可手动触发
```

---

## 目录结构

```
tenet-openclaw-arena/
├── app/                        # Vue 3 前端
│   ├── src/
│   │   ├── api/client.ts       # API 层
│   │   └── components/pages/
│   │       └── LeaderboardPage.vue
│   └── dist/                   # 构建产物（部署到 Cloudflare Pages）
├── backend/                   # Hono + SQLite 后端
│   └── src/
│       └── index.ts           # API: /api/leaderboard, /api/results, ...
├── data/benchmark/tasks/       # 18 个 YAML 任务定义
│   ├── _index.yml             # 题库注册表
│   ├── skill_dispatch/         # 4 任务
│   ├── tool_chain/            # 4 任务
│   ├── cli_competence/         # 3 任务
│   ├── computer_use/           # 2 任务
│   ├── self_correction/         # 3 任务
│   └── delegation/             # 2 任务
├── benchmark/                  # Python Benchmark Runner
│   ├── event_parser.py         # 12种事件类型解析
│   ├── scorer.py              # YAML规则打分引擎
│   ├── parallel_runner.py      # ProcessPoolExecutor 并行执行
│   ├── openclaw_runner.py     # openclaw agent subprocess 调用
│   └── schemas.py             # YAML task schema 定义
├── output/benchmark_results/  # Benchmark 结果存档（JSON）
├── scripts/
│   └── run_benchmark.py        # CLI 入口
└── docs/                      # 设计文档
```

---

## 设计参考

- Pretext 粒子动态效果：https://chenglou.me/pretext/variable-typographic-ascii/
- Arena 排名风格：https://arena.ai/leaderboard/code
- 深色舞台型设计：https://persona.atlant.com/p3r/index.html
