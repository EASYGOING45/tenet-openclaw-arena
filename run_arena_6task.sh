#!/bin/bash
# 精简 benchmark：6任务 × 2 agents（M2.7 + K2P5）
cd /Users/golden-tenet/claw-spaces/Phoebe/Projects/openclaw-model-arena

python3 -c "
import asyncio, json, yaml
from benchmark.parallel_runner import run_benchmark, load_yaml_tasks
from pathlib import Path

index = Path('data/benchmark/tasks/_index.yml')
all_tasks = load_yaml_tasks(index)

# 每维度选第1个任务，组成6任务精简集
selected_ids = {'skill-dispatch-001','tool-chain-001','cli-001','computer-001','self-correction-001','delegation-001'}
tasks = [t for t in all_tasks if t.get('task_id') in selected_ids]
print(f'Tasks: {[t[\"task_id\"] for t in tasks]}')

agents = ['arena-m27', 'arena-k2p5']
print(f'Agents: {agents}')

result = asyncio.run(run_benchmark(
    agents=agents,
    tasks=tasks,
    max_workers=2,  # 并行2路
    dry_run=False,
))
print(json.dumps(result, indent=2, default=str))
" 2>&1
