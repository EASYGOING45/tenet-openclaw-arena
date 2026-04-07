#!/bin/bash
cd /Users/golden-tenet/claw-spaces/Phoebe/Projects/openclaw-model-arena
python3 -c "
import asyncio, json
from benchmark.parallel_runner import run_benchmark, load_yaml_tasks
from pathlib import Path

index = Path('data/benchmark/tasks/_index.yml')
tasks = load_yaml_tasks(index)
# 只跑 skill-dispatch-001
tasks = [t for t in tasks if t.get('task_id') == 'skill-dispatch-001']

print(f'Running: 1 agent x {len(tasks)} task')
result = asyncio.run(run_benchmark(
    agents=['arena-gpt54'],
    tasks=tasks,
    max_workers=1,
    dry_run=False,
))
print(json.dumps(result, indent=2, default=str))
"
