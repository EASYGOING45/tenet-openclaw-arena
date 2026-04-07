#!/usr/bin/env python3
"""Run 6-task benchmark for M27 and K2P5."""
import asyncio, json, time
from benchmark.parallel_runner import run_benchmark, load_yaml_tasks
from pathlib import Path

async def main():
    index = Path("data/benchmark/tasks/_index.yml")
    all_tasks = load_yaml_tasks(index)
    selected_ids = {"skill-dispatch-001","tool-chain-001","cli-001","computer-001","self-correction-001","delegation-001"}
    tasks = [t for t in all_tasks if t.get("task_id") in selected_ids]
    agents = ["arena-m27", "arena-k2p5"]
    print(f"Tasks: {[t['task_id'] for t in tasks]}")
    print(f"Agents: {agents}")

    result = await run_benchmark(agents=agents, tasks=tasks, max_workers=1, dry_run=False)

    out_path = Path("output/benchmark_results") / f"run_{time.strftime('%Y%m%dT%H%M%SZ')}.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(result, indent=2, default=str))
    print(f"Saved to {out_path}")

    agents_data = {}
    for r in result["results"]:
        a = r["agent_id"]
        if a not in agents_data:
            agents_data[a] = []
        agents_data[a].append(r)
    for agent, results in agents_data.items():
        scores = [r["score"] for r in results]
        print(f"\n【{agent}】avg={sum(scores)/len(scores):.1f}")
        for r in results:
            evs = len(r["events"])
            print(f"  {r['task_id']}: {r['score']} ({r['verdict']}) events={evs}")

if __name__ == "__main__":
    asyncio.run(main())
