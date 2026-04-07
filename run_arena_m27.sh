#!/bin/bash
cd /Users/golden-tenet/claw-spaces/Phoebe/Projects/openclaw-model-arena
python3 -c "
import asyncio, json
from benchmark.parallel_runner import run_benchmark, load_yaml_tasks
from pathlib import Path

index = Path('data/benchmark/tasks/_index.yml')
tasks = load_yaml_tasks(index)
agents = ['arena-m27']

print(f'Running: {len(agents)} agent x {len(tasks)} tasks')
result = asyncio.run(run_benchmark(
    agents=agents,
    tasks=tasks,
    max_workers=1,
    dry_run=False,
))
print(json.dumps(result, indent=2, default=str))
"
