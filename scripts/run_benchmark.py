from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from benchmark.openclaw_runner import _parse_response_json
from benchmark.openclaw_runner import build_agent_command
from benchmark.openclaw_runner import extract_assistant_text
from benchmark.schemas import BenchmarkTask
from benchmark.task_loader import load_tasks
from scripts.build_site_data import build_site_data
from scripts.score_runs import score_run_artifacts
from scripts.setup_agents import sync_agent_specs

ARENA_AGENT_IDS = ("arena-gpt54", "arena-m27", "arena-k2p5")


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


def _iso_now() -> str:
    return _utc_now().isoformat()


def _workspace_root_from_project(project_root: Path) -> Path:
    return project_root.parents[1]


def _slug_token(*parts: str) -> str:
    flattened = "-".join(parts).upper()
    cleaned = "".join(character if character.isalnum() else "-" for character in flattened)
    compact = "-".join(chunk for chunk in cleaned.split("-") if chunk)
    return compact or "TOKEN"


def _write_text(path: Path, content: str) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content)
    return path


def _reset_agent_main_session(agent_id: str) -> None:
    sessions_path = (
        Path.home()
        / ".openclaw"
        / "agents"
        / agent_id
        / "sessions"
        / "sessions.json"
    )
    if not sessions_path.exists():
        return

    payload = json.loads(sessions_path.read_text())
    if not isinstance(payload, dict):
        return

    session_key = f"agent:{agent_id}:main"
    if session_key in payload:
        del payload[session_key]
        sessions_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")


def _startup_prompt(
    task: BenchmarkTask,
    *,
    workspace_root: Path,
    fixture_dir: Path,
) -> tuple[str, dict[str, str]]:
    today = date.today()
    yesterday = today - timedelta(days=1)
    greeting_file = _write_text(
        fixture_dir / "startup_greeting_token.txt",
        f"GREETING-{_slug_token(task.task_id, fixture_dir.name)}\n",
    )
    startup_paths = [
        workspace_root / "SOUL.md",
        workspace_root / "USER.md",
        workspace_root / "memory" / f"{today.isoformat()}.md",
        workspace_root / "memory" / f"{yesterday.isoformat()}.md",
        workspace_root / "MEMORY.md",
        workspace_root / "AGENTS.md",
    ]
    prompt = "\n".join(
        [
            f"Benchmark task: {task.title}",
            f"Original task brief: {task.prompt}",
            "",
            "Execute the startup discipline for this workspace before your first real reply.",
            "Read these files in order if they exist:",
            *(f"- {path}" for path in startup_paths),
            f"- {greeting_file}",
            "",
            "After the reads, give a one-sentence greeting that includes the exact greeting token from the final file once.",
        ]
    )
    return prompt, {
        "greeting_file": str(greeting_file),
        "workspace_root": str(workspace_root),
    }


def _tool_prompt(
    task: BenchmarkTask,
    *,
    fixture_dir: Path,
) -> tuple[str, dict[str, str]]:
    token_file = _write_text(
        fixture_dir / "exact_token.txt",
        f"TOKEN-{_slug_token(task.task_id, fixture_dir.name)}\n",
    )
    prompt = "\n".join(
        [
            f"Benchmark task: {task.title}",
            f"Original task brief: {task.prompt}",
            "",
            f"Use read on this file: {token_file}",
            "Reply with the exact token from that file and nothing else.",
        ]
    )
    return prompt, {
        "token_file": str(token_file),
        "expected_token": token_file.read_text().strip(),
    }


def _autonomy_prompt(
    task: BenchmarkTask,
    *,
    fixture_dir: Path,
) -> tuple[str, dict[str, str]]:
    source_file = _write_text(
        fixture_dir / "autonomy_notes.txt",
        "\n".join(
            [
                "alpha: inspect this file first",
                "beta: write a summary file next",
                "gamma: verify the written file before finishing",
            ]
        )
        + "\n",
    )
    summary_file = fixture_dir / "autonomy_summary.md"
    verification_command = (
        "python3 -c \"from pathlib import Path; "
        f"print(Path(r'{summary_file}').read_text())\""
    )
    prompt = "\n".join(
        [
            f"Benchmark task: {task.title}",
            f"Original task brief: {task.prompt}",
            "",
            f"1. Read {source_file}.",
            f"2. Create {summary_file} with heading '# Autonomy Summary' and one bullet per source line.",
            f"3. Verify the file by running exactly: {verification_command}",
            "4. Continue without waiting for a reprompt and finish with a short summary that reports the output path.",
        ]
    )
    return prompt, {
        "source_file": str(source_file),
        "summary_file": str(summary_file),
        "verification_command": verification_command,
    }


def _recovery_prompt(
    task: BenchmarkTask,
    *,
    fixture_dir: Path,
) -> tuple[str, dict[str, str]]:
    missing_path = fixture_dir / "missing" / "recovery_target.txt"
    search_root = fixture_dir / "recovery-search-root"
    actual_target = _write_text(
        search_root / "actual" / "recovery_target.txt",
        f"RECOVER-{_slug_token(task.task_id, fixture_dir.name)}\n",
    )
    prompt = "\n".join(
        [
            f"Benchmark task: {task.title}",
            f"Original task brief: {task.prompt}",
            "",
            f"Start by trying to inspect this intentionally missing path: {missing_path}",
            f"If it is missing, recover by locating the correct file somewhere under: {search_root}",
            "Then read the real file and reply with the exact recovered token only.",
        ]
    )
    return prompt, {
        "missing_path": str(missing_path),
        "search_root": str(search_root),
        "expected_target": str(actual_target),
        "expected_token": actual_target.read_text().strip(),
    }


def _verification_prompt(
    task: BenchmarkTask,
    *,
    fixture_dir: Path,
) -> tuple[str, dict[str, str]]:
    target_file = fixture_dir / "verification_result.txt"
    expected_text = f"status=verified::{_slug_token(task.task_id, fixture_dir.name)}"
    verification_command = (
        "python3 -c \"from pathlib import Path; "
        f"print(Path(r'{target_file}').read_text().strip())\""
    )
    prompt = "\n".join(
        [
            f"Benchmark task: {task.title}",
            f"Original task brief: {task.prompt}",
            "",
            f"Write this exact text to {target_file}: {expected_text}",
            f"Before any completion claim, run exactly this verification command: {verification_command}",
            "Only after seeing the verification output should you state that the task is complete.",
        ]
    )
    return prompt, {
        "target_file": str(target_file),
        "expected_text": expected_text,
        "verification_command": verification_command,
    }


def _acpx_prompt(
    task: BenchmarkTask,
    *,
    fixture_dir: Path,
) -> tuple[str, dict[str, str]]:
    delegate_target = fixture_dir / "delegated_note.txt"
    delegate_prompt = (
        "Using ACPX/Codex, update the target file so its full contents become:\n"
        "# ACPX Delegated Note\n"
        "status: delegated\n"
        "source: codex\n"
    )
    prompt = "\n".join(
        [
            f"Benchmark task: {task.title}",
            f"Original task brief: {task.prompt}",
            "",
            "Use ACPX/Codex delegation for a bounded edit.",
            f"Target file: {delegate_target}",
            "ACPX/Codex delegation prompt:",
            delegate_prompt,
            "After the delegate finishes, inspect the file yourself and report the first line plus whether the file now contains 'status: delegated'.",
        ]
    )
    return prompt, {
        "delegate_target": str(delegate_target),
        "delegate_prompt": delegate_prompt,
    }


def build_runtime_prompt(
    task: BenchmarkTask,
    *,
    workspace_root: Path,
    fixture_dir: Path,
) -> tuple[str, dict[str, str]]:
    if task.category == "startup_discipline":
        return _startup_prompt(task, workspace_root=workspace_root, fixture_dir=fixture_dir)
    if task.category == "tool_accuracy":
        return _tool_prompt(task, fixture_dir=fixture_dir)
    if task.category == "autonomy_continuity":
        return _autonomy_prompt(task, fixture_dir=fixture_dir)
    if task.category == "recovery_behavior":
        return _recovery_prompt(task, fixture_dir=fixture_dir)
    if task.category == "verification_honesty":
        return _verification_prompt(task, fixture_dir=fixture_dir)
    if task.category == "acpx_codex":
        return _acpx_prompt(task, fixture_dir=fixture_dir)
    raise ValueError(f"unsupported task category: {task.category}")


def build_run_matrix(
    tasks: list[BenchmarkTask],
    *,
    agent_ids: list[str],
    workspace_root: Path,
    run_root: Path,
    run_label: str,
) -> list[dict[str, Any]]:
    matrix: list[dict[str, Any]] = []
    run_root.mkdir(parents=True, exist_ok=True)

    for task in tasks:
        for agent_id in agent_ids:
            run_id = f"{run_label}-{task.task_id}-{agent_id}"
            fixture_dir = run_root / "fixtures" / run_id
            prompt, fixture = build_runtime_prompt(
                task,
                workspace_root=workspace_root,
                fixture_dir=fixture_dir,
            )
            matrix.append(
                {
                    "run_id": run_id,
                    "task_id": task.task_id,
                    "task_title": task.title,
                    "category": task.category,
                    "task_prompt_template": task.prompt,
                    "success_criteria": list(task.success_criteria),
                    "agent_id": agent_id,
                    "prompt": prompt,
                    "fixture": fixture,
                    "artifact_path": str(run_root / f"{run_id}.json"),
                    "fixture_dir": str(fixture_dir),
                }
            )

    return matrix


def _persist_artifact(
    spec: dict[str, Any],
    *,
    completed: subprocess.CompletedProcess[str],
    artifact_path: Path,
    started_at: str,
    completed_at: str,
) -> Path:
    response_json = _parse_response_json(completed.stdout)
    session_id = None
    if isinstance(response_json, dict):
        result = response_json.get("result")
        if isinstance(result, dict):
            meta = result.get("meta")
            if isinstance(meta, dict):
                agent_meta = meta.get("agentMeta")
                if isinstance(agent_meta, dict) and agent_meta.get("sessionId"):
                    session_id = str(agent_meta["sessionId"])
        if session_id is None and response_json.get("sessionId"):
            session_id = str(response_json["sessionId"])
    final_text = extract_assistant_text(response_json, fallback_stdout=completed.stdout)
    payload = {
        "run_id": spec["run_id"],
        "task_id": spec["task_id"],
        "task_title": spec["task_title"],
        "category": spec["category"],
        "task_prompt_template": spec["task_prompt_template"],
        "success_criteria": spec["success_criteria"],
        "agent_id": spec["agent_id"],
        "prompt": spec["prompt"],
        "fixture": spec["fixture"],
        "started_at": started_at,
        "completed_at": completed_at,
        "command": completed.args,
        "returncode": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
        "response_json": response_json,
        "session_id": session_id,
        "final_text": final_text,
    }
    artifact_path.parent.mkdir(parents=True, exist_ok=True)
    artifact_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    return artifact_path


def _run_spec(spec: dict[str, Any]) -> Path:
    started_at = _iso_now()
    _reset_agent_main_session(str(spec["agent_id"]))
    command = build_agent_command(
        str(spec["agent_id"]),
        str(spec["prompt"]),
        session_id=str(spec["run_id"]),
        timeout_seconds=300,
    )
    completed = subprocess.run(command, capture_output=True, text=True, check=False)
    finished_at = _iso_now()
    return _persist_artifact(
        spec,
        completed=completed,
        artifact_path=Path(str(spec["artifact_path"])),
        started_at=started_at,
        completed_at=finished_at,
    )


def _site_output_for_run(site_output_path: Path, run_label: str) -> Path:
    if site_output_path.name == "site-data.json":
        return site_output_path.with_name(f"{run_label}-site-data.json")
    return site_output_path


def orchestrate_benchmark(
    *,
    workspace_root: Path,
    project_root: Path,
    task_path: Path,
    runs_root: Path,
    normalized_root: Path,
    site_output_path: Path,
    run_label: str,
    agent_ids: list[str] | None = None,
    limit: int | None = None,
    reconcile_agents: bool = True,
    build_scores: bool = True,
    build_site: bool = True,
) -> dict[str, Any]:
    if reconcile_agents:
        synced_specs = sync_agent_specs(str(workspace_root))
        synced_agent_ids = [
            str(spec.get("id", ""))
            for spec in synced_specs
            if str(spec.get("id", "")) in ARENA_AGENT_IDS
        ]
    else:
        synced_agent_ids = list(ARENA_AGENT_IDS)

    selected_agent_ids = agent_ids or synced_agent_ids or list(ARENA_AGENT_IDS)
    tasks = load_tasks(task_path)
    if limit is not None:
        tasks = tasks[:limit]

    batch_run_root = runs_root / run_label
    matrix = build_run_matrix(
        tasks,
        agent_ids=selected_agent_ids,
        workspace_root=workspace_root,
        run_root=batch_run_root,
        run_label=run_label,
    )
    artifact_paths = [_run_spec(spec) for spec in matrix]

    manifest_path = batch_run_root / "manifest.json"
    manifest = {
        "run_label": run_label,
        "workspace_root": str(workspace_root),
        "project_root": str(project_root),
        "task_path": str(task_path),
        "generated_at": _iso_now(),
        "agent_ids": selected_agent_ids,
        "artifact_paths": [str(path) for path in artifact_paths],
    }
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")

    normalized_batch_root = normalized_root / run_label
    resolved_site_output_path = _site_output_for_run(site_output_path, run_label)
    if build_scores:
        score_run_artifacts(
            artifact_paths,
            output_dir=normalized_batch_root,
            snapshot_root=normalized_batch_root / "transcripts",
        )

    if build_site:
        build_site_data(
            normalized_dir=normalized_batch_root,
            output_path=resolved_site_output_path,
        )

    return {
        "run_label": run_label,
        "artifact_paths": [str(path) for path in artifact_paths],
        "manifest_path": str(manifest_path),
        "normalized_dir": str(normalized_batch_root),
        "site_output_path": str(resolved_site_output_path),
    }


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run the OpenClaw Model Arena benchmark.")
    parser.add_argument(
        "--mode",
        choices=["phase1", "phase2"],
        default="phase1",
        help="phase1: original JSON task + full run pipeline; phase2: YAML tasks + parallel sweep (default: phase1)",
    )
    parser.add_argument(
        "--category",
        type=str,
        default=None,
        help="[phase2] Filter YAML tasks by capability/dimension.",
    )
    parser.add_argument(
        "--agents",
        type=str,
        default=None,
        help="[phase2] Comma-separated agent IDs (default: arena-gpt54,arena-m27,main).",
    )
    parser.add_argument(
        "--new-only",
        action="store_true",
        help="[phase2] Only run tasks not in existing results.",
    )
    parser.add_argument(
        "--max-workers",
        type=int,
        default=3,
        help="[phase2] Max parallel workers (default: 3).",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="[phase2] Show what would run without executing agents.",
    )
    parser.add_argument(
        "--workspace-root",
        type=Path,
        default=_workspace_root_from_project(PROJECT_ROOT),
        help="Workspace root that contains Projects/ and the startup discipline files.",
    )
    parser.add_argument(
        "--project-root",
        type=Path,
        default=PROJECT_ROOT,
        help="Project root for the OpenClaw Model Arena repo slice.",
    )
    parser.add_argument(
        "--task-path",
        type=Path,
        default=PROJECT_ROOT / "data" / "tasks" / "benchmark_tasks.json",
        help="Benchmark task definition file.",
    )
    parser.add_argument(
        "--runs-root",
        type=Path,
        default=PROJECT_ROOT / "data" / "runs",
        help="Root directory for raw run artifacts.",
    )
    parser.add_argument(
        "--normalized-root",
        type=Path,
        default=PROJECT_ROOT / "data" / "normalized",
        help="Root directory for normalized run artifacts.",
    )
    parser.add_argument(
        "--site-output-path",
        type=Path,
        default=None,
        help="Output JSON file for the generated site payload. Defaults to data/site/<run-label>-site-data.json.",
    )
    parser.add_argument(
        "--run-label",
        default=_utc_now().strftime("benchmark-%Y%m%dT%H%M%SZ"),
        help="Stable label for this benchmark batch.",
    )
    parser.add_argument(
        "--agent",
        action="append",
        dest="agent_ids",
        help="Optional arena agent id. Repeat to benchmark a subset.",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=None,
        help="Optional max task count for smoke runs.",
    )
    parser.add_argument(
        "--skip-setup",
        action="store_true",
        help="Skip agent reconciliation before running the benchmark.",
    )
    parser.add_argument(
        "--skip-score",
        action="store_true",
        help="Skip normalization/scoring after the raw run step.",
    )
    parser.add_argument(
        "--skip-site",
        action="store_true",
        help="Skip site payload generation after scoring.",
    )
    return parser


def main() -> None:
    args = _build_parser().parse_args()

    # Phase 2: YAML-based parallel sweep
    if args.mode == "phase2":
        import asyncio
        from benchmark.parallel_runner import run_benchmark as phase2_run_benchmark
        from benchmark.parallel_runner import load_yaml_tasks

        project_root = args.project_root
        index_path = project_root / "data" / "benchmark" / "tasks" / "_index.yml"
        all_tasks = load_yaml_tasks(index_path)

        if args.category:
            all_tasks = [t for t in all_tasks if t.get("capability") == args.category]

        agents = args.agents.split(",") if args.agents else ["arena-gpt54", "arena-m27", "main"]

        result = asyncio.run(
            phase2_run_benchmark(
                agents=agents,
                tasks=all_tasks,
                max_workers=args.max_workers,
                output_dir=args.project_root / "output" / "benchmark_results",
                dry_run=args.dry_run,
            )
        )
        print(json.dumps(result, indent=2, sort_keys=True))
        return

    # Phase 1: original JSON task pipeline
    site_output_path = args.site_output_path or (
        args.project_root / "data" / "site" / f"{args.run_label}-site-data.json"
    )
    summary = orchestrate_benchmark(
        workspace_root=args.workspace_root,
        project_root=args.project_root,
        task_path=args.task_path,
        runs_root=args.runs_root,
        normalized_root=args.normalized_root,
        site_output_path=site_output_path,
        run_label=args.run_label,
        agent_ids=args.agent_ids,
        limit=args.limit,
        reconcile_agents=not args.skip_setup,
        build_scores=not args.skip_score,
        build_site=not args.skip_site,
    )
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
