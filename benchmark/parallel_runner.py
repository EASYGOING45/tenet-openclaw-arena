"""
Parallel benchmark runner for OpenClaw Model Arena.

Executes multiple agents × multiple tasks in parallel via ProcessPoolExecutor.
"""

from __future__ import annotations

import asyncio
import json
import subprocess
import sys
import time
from concurrent.futures import ProcessPoolExecutor, as_completed
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

# Ensure benchmark module is importable
_PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

from benchmark.event_parser import parse_events
from benchmark.scorer import score


@dataclass
class TaskResult:
    """Result of a single agent × task run."""
    run_id: str
    agent_id: str
    task_id: str
    score: float
    verdict: str
    events: list
    transcript: str
    duration_ms: int
    error: str | None

    def to_dict(self) -> dict[str, Any]:
        return {
            "run_id": self.run_id,
            "agent_id": self.agent_id,
            "task_id": self.task_id,
            "score": self.score,
            "verdict": self.verdict,
            "duration_ms": self.duration_ms,
            "error": self.error,
            "events": self.events,
        }


def _utc_ts() -> str:
    return datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def build_prompt(task: dict[str, Any]) -> str:
    """From YAML prompt dict, build a flat text prompt."""
    prompt_section = task.get("prompt", {})
    system = prompt_section.get("system", "") if isinstance(prompt_section, dict) else str(prompt_section)
    user = prompt_section.get("user", "") if isinstance(prompt_section, dict) else ""
    return f"[SYSTEM]\n{system}\n\n[USER]\n{user}"


def run_single_task(agent_id: str, task: dict[str, Any]) -> TaskResult:
    """
    Execute a single agent × task run and return the result.

    Runs synchronously (called from ProcessPoolExecutor workers).
    """
    run_id = f"run_{_utc_ts()}"
    task_id = task.get("task_id", "unknown")
    timeout = task.get("evaluation", {}).get("timeout_seconds", 90)

    prompt = build_prompt(task)

    start = time.monotonic()
    error_msg: str | None = None
    stdout = ""
    stderr = ""
    returncode = -1

    try:
        result = subprocess.run(
            [
                "openclaw", "agent",
                "--agent", agent_id,
                "--message", prompt,
                "--json",
                "--thinking", "low",
            ],
            capture_output=True,
            text=True,
            timeout=timeout,
            check=False,
        )
        returncode = result.returncode
        stdout = result.stdout
        stderr = result.stderr
    except subprocess.TimeoutExpired as exc:
        stdout = getattr(exc, "stdout", "") or ""
        stderr = getattr(exc, "stderr", "") or ""
        error_msg = f"Timeout after {timeout}s"
    except Exception as exc:
        error_msg = str(exc)

    duration_ms = int((time.monotonic() - start) * 1000)

    # Parse events
    events = parse_events(stdout, stderr)

    # Score
    try:
        score_val, verdict = score(events, task)
    except Exception:
        score_val = 0.0
        verdict = "ERROR"

    return TaskResult(
        run_id=run_id,
        agent_id=agent_id,
        task_id=task_id,
        score=score_val,
        verdict=verdict,
        events=events,
        transcript=stdout[:5000],
        duration_ms=duration_ms,
        error=error_msg or (stderr[:500] if returncode != 0 else None),
    )


async def run_benchmark_sweep(
    agents: list[str],
    tasks: list[dict[str, Any]],
    max_workers: int = 3,
) -> list[TaskResult]:
    """
    Run all agent × task combinations in parallel.

    Uses ProcessPoolExecutor to parallelize across CPU cores.
    """
    results: list[TaskResult] = []
    jobs = [(agent_id, task) for agent_id in agents for task in tasks]

    loop = asyncio.get_event_loop()

    with ProcessPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(run_single_task, agent_id, task): (agent_id, task.get("task_id", "unknown"))
            for agent_id, task in jobs
        }

        for future in as_completed(futures):
            agent_id, task_id = futures[future]
            try:
                result = future.result()
                results.append(result)
            except Exception as exc:
                results.append(TaskResult(
                    run_id=f"run_{_utc_ts()}",
                    agent_id=agent_id,
                    task_id=task_id,
                    score=0.0,
                    verdict="ERROR",
                    events=[],
                    transcript="",
                    duration_ms=0,
                    error=str(exc),
                ))

    return results


async def run_benchmark(
    *,
    agents: list[str],
    tasks: list[dict[str, Any]],
    max_workers: int = 3,
    output_dir: Path | None = None,
    dry_run: bool = False,
) -> dict[str, Any]:
    """
    Full benchmark orchestration: load, run, score, save.
    """
    import yaml

    output_dir = output_dir or (_PROJECT_ROOT / "output" / "benchmark_results")
    output_dir.mkdir(parents=True, exist_ok=True)

    run_label = f"run_{_utc_ts()}"

    if dry_run:
        print(f"[DRY RUN] Would run: {len(agents)} agents × {len(tasks)} tasks = {len(agents)*len(tasks)} runs")
        for task in tasks:
            for agent in agents:
                print(f"  - {agent} × {task.get('task_id')}")
        return {"run_id": run_label, "dry_run": True, "agents": agents, "total_tasks": len(tasks)}

    print(f"Starting benchmark: {len(agents)} agents × {len(tasks)} tasks = {len(agents)*len(tasks)} runs")
    results = await run_benchmark_sweep(agents, tasks, max_workers=max_workers)

    # Persist full results
    output: dict[str, Any] = {
        "run_id": run_label,
        "schema_version": 1,
        "agents": agents,
        "total_tasks": len(tasks),
        "results": [r.to_dict() for r in results],
    }

    output_path = output_dir / f"{run_label}.json"
    output_path.write_text(json.dumps(output, ensure_ascii=False, indent=2))
    print(f"Results saved to {output_path}")

    # Print summary
    from collections import defaultdict
    by_agent: dict[str, list[TaskResult]] = defaultdict(list)
    for r in results:
        by_agent[r.agent_id].append(r)

    for agent_id, res in by_agent.items():
        avg = sum(r.score for r in res) / len(res)
        passed = sum(1 for r in res if r.verdict == "PASS")
        partial = sum(1 for r in res if r.verdict == "PARTIAL")
        print(f"  {agent_id}: avg={avg:.1f}, PASS={passed}/{len(res)}, PARTIAL={partial}/{len(res)}")

    return output


def load_yaml_tasks(index_path: Path) -> list[dict[str, Any]]:
    """Load all active YAML tasks from the registry."""
    import yaml

    index = yaml.safe_load(index_path.read_text())
    tasks = []
    for entry in index.get("tasks", []):
        if not entry.get("is_active", True):
            continue
        yaml_path = index_path.parent / entry["yaml_path"]
        if yaml_path.exists():
            task = yaml.safe_load(yaml_path.read_text())
            tasks.append(task)
    return tasks


async def main() -> None:
    import argparse
    import yaml

    parser = argparse.ArgumentParser(description="Run OpenClaw benchmark sweep.")
    parser.add_argument("--category", type=str, default=None,
                        help="Filter tasks by capability/dimension")
    parser.add_argument("--agents", type=str, default=None,
                        help="Comma-separated agent IDs (default: arena-gpt54,arena-m27,main)")
    parser.add_argument("--new-only", action="store_true",
                        help="Only run tasks not in existing results")
    parser.add_argument("--max-workers", type=int, default=3)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--output-dir", type=Path, default=None)
    args = parser.parse_args()

    project_root = _PROJECT_ROOT
    index_path = project_root / "data" / "benchmark" / "tasks" / "_index.yml"

    # Load tasks
    all_tasks = load_yaml_tasks(index_path)

    # Filter by category
    if args.category:
        all_tasks = [t for t in all_tasks if t.get("capability") == args.category]

    # Filter new-only (stub: check existing output dir)
    if args.new_only:
        output_dir = project_root / "output" / "benchmark_results"
        if output_dir.exists():
            existing = set()
            for f in output_dir.glob("*.json"):
                data = json.loads(f.read_text())
                for r in data.get("results", []):
                    existing.add((r["agent_id"], r["task_id"]))
            all_tasks = [
                t for t in all_tasks
                if t.get("is_active", True)
            ]
            # Keep only if not all agents have run this task
            # (simplified: just filter out fully completed ones)
            pass  # Keep all for now

    agents = args.agents.split(",") if args.agents else ["arena-gpt54", "arena-m27", "main"]

    await run_benchmark(
        agents=agents,
        tasks=all_tasks,
        max_workers=args.max_workers,
        output_dir=args.output_dir,
        dry_run=args.dry_run,
    )


if __name__ == "__main__":
    asyncio.run(main())
