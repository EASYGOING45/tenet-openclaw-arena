#!/usr/bin/env python3
"""Run 6-task benchmark for M27 and K2P5 — writes to SQLite + JSON."""
import asyncio, json, time
from pathlib import Path
from datetime import datetime, timezone

# Ensure project root is on path
import sys
_PROJECT_ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(_PROJECT_ROOT))

from benchmark.parallel_runner import run_benchmark, load_yaml_tasks


async def main():
    arena_root = Path(__file__).resolve().parent
    index = arena_root / "data/benchmark/tasks/_index.yml"
    all_tasks = load_yaml_tasks(index)
    selected_ids = {"skill-dispatch-001","tool-chain-001","cli-001","computer-001","self-correction-001","delegation-001"}
    tasks = [t for t in all_tasks if t.get("task_id") in selected_ids]
    agents = ["arena-m27", "arena-k2p5"]
    print(f"Tasks: {[t['task_id'] for t in tasks]}")
    print(f"Agents: {agents}")

    result = await run_benchmark(
        agents=agents,
        tasks=tasks,
        max_workers=1,
        dry_run=False,
    )

    # Print summary
    by_agent = {}
    for r in result["results"]:
        a = r["agent_id"]
        if a not in by_agent:
            by_agent[a] = []
        by_agent[a].append(r)

    print()
    for agent, results in by_agent.items():
        scores = [r["score"] for r in results]
        avg = sum(scores) / len(scores)
        passed = sum(1 for r in results if r["verdict"] == "PASS")
        partial = sum(1 for r in results if r["verdict"] == "PARTIAL")
        print(f"【{agent}】avg={avg:.1f}  PASS={passed} PARTIAL={partial}")
        for r in sorted(results, key=lambda x: x["task_id"]):
            print(f"  {r['task_id']}: {r['score']:5.1f}  {r['verdict']:8s}  {len(r['events'])} events")

    print(f"\nResults also written to SQLite (backend/arena.db)")


if __name__ == "__main__":
    asyncio.run(main())
