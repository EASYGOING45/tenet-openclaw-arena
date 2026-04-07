from __future__ import annotations

import json
from pathlib import Path
from subprocess import CompletedProcess

from benchmark.schemas import BenchmarkTask
from scripts.reset_run import reset_generated_artifacts
from scripts.run_benchmark import build_run_matrix
from scripts.run_benchmark import orchestrate_benchmark


def _task(
    task_id: str,
    title: str,
    category: str,
    prompt: str,
) -> BenchmarkTask:
    return BenchmarkTask(
        task_id=task_id,
        title=title,
        category=category,  # type: ignore[arg-type]
        prompt=prompt,
        success_criteria=["criterion-a", "criterion-b"],
    )


def test_build_run_matrix_creates_concrete_runtime_prompts_and_fixtures(
    tmp_path: Path,
) -> None:
    workspace_root = tmp_path / "workspace"
    (workspace_root / "memory").mkdir(parents=True)
    (workspace_root / "SOUL.md").write_text("soul")
    (workspace_root / "USER.md").write_text("user")
    (workspace_root / "MEMORY.md").write_text("memory")
    (workspace_root / "memory" / "2026-04-05.md").write_text("today")
    (workspace_root / "memory" / "2026-04-04.md").write_text("yesterday")

    tasks = [
        _task(
            "startup-001",
            "Startup discipline on fresh session",
            "startup_discipline",
            "A new session was started. Follow workspace startup discipline before replying, then give a short greeting.",
        ),
        _task(
            "tool-001",
            "Read a file and return exact token",
            "tool_accuracy",
            "Use read to inspect a local file and reply with its exact token only.",
        ),
        _task(
            "auto-001",
            "Continue multi-step task without reprompt",
            "autonomy_continuity",
            "Inspect, modify, verify, and summarize in one turn.",
        ),
        _task(
            "recovery-001",
            "Recover from a forced invalid path",
            "recovery_behavior",
            "Diagnose a missing file path, locate the right file, and continue.",
        ),
        _task(
            "verify-001",
            "Run explicit verification before completion claim",
            "verification_honesty",
            "Make a small change, run verification, and only then claim completion.",
        ),
        _task(
            "acpx-001",
            "Delegate a bounded edit to ACPX/Codex and continue",
            "acpx_codex",
            "Use ACPX to delegate a bounded task to Codex, then inspect the result and continue the workflow.",
        ),
    ]

    matrix = build_run_matrix(
        tasks,
        agent_ids=["arena-gpt54", "arena-k2p5"],
        workspace_root=workspace_root,
        run_root=tmp_path / "runs",
        run_label="batch-001",
    )

    assert len(matrix) == 12

    startup_run = next(item for item in matrix if item["task_id"] == "startup-001")
    assert str(workspace_root / "SOUL.md") in startup_run["prompt"]
    assert str(workspace_root / "memory" / "2026-04-05.md") in startup_run["prompt"]
    assert startup_run["task_prompt_template"].startswith("A new session was started")

    tool_run = next(item for item in matrix if item["task_id"] == "tool-001")
    tool_fixture = tool_run["fixture"]
    assert Path(tool_fixture["token_file"]).read_text().strip() == tool_fixture["expected_token"]
    assert tool_fixture["token_file"] in tool_run["prompt"]

    recovery_run = next(item for item in matrix if item["task_id"] == "recovery-001")
    recovery_fixture = recovery_run["fixture"]
    assert recovery_fixture["missing_path"] in recovery_run["prompt"]
    assert recovery_fixture["search_root"] in recovery_run["prompt"]
    assert (
        Path(recovery_fixture["expected_target"]).read_text().strip()
        == recovery_fixture["expected_token"]
    )

    verification_run = next(item for item in matrix if item["task_id"] == "verify-001")
    verification_fixture = verification_run["fixture"]
    assert verification_fixture["verification_command"] in verification_run["prompt"]
    assert verification_fixture["target_file"] in verification_run["prompt"]

    acpx_run = next(item for item in matrix if item["task_id"] == "acpx-001")
    assert "ACPX/Codex delegation prompt" in acpx_run["prompt"]
    assert acpx_run["fixture"]["delegate_target"] in acpx_run["prompt"]


def test_orchestrate_benchmark_reconciles_agents_runs_tasks_and_builds_outputs(
    tmp_path: Path, monkeypatch
) -> None:
    workspace_root = tmp_path / "workspace"
    project_root = workspace_root / "Projects" / "openclaw-model-arena"
    tasks_dir = project_root / "data" / "tasks"
    tasks_dir.mkdir(parents=True)
    task_path = tasks_dir / "benchmark_tasks.json"
    task_path.write_text(
        json.dumps(
            {
                "version": 1,
                "tasks": [
                    {
                        "task_id": "tool-001",
                        "title": "Read a file and return exact token",
                        "category": "tool_accuracy",
                        "prompt": "Use read to inspect a local file and reply with its exact token only.",
                        "success_criteria": ["produces real tool call"],
                    }
                ],
            }
        )
    )

    order: list[str] = []
    normalized_calls: dict[str, object] = {}
    site_calls: dict[str, object] = {}

    def fake_sync(workspace: str) -> list[dict[str, object]]:
        order.append("sync")
        assert workspace == str(workspace_root)
        return [{"id": "arena-gpt54"}]

    def fake_run(command, capture_output, text, check):  # type: ignore[no-untyped-def]
        assert order == ["sync"]
        order.append("run")
        assert command[:4] == ["openclaw", "agent", "--agent", "arena-gpt54"]
        assert "--session-id" in command
        assert "batch-001-tool-001-arena-gpt54" in command
        return CompletedProcess(
            args=command,
            returncode=0,
            stdout='{"sessionId":"sess-tool-001","result":{"payloads":[{"text":"TOKEN-OK"}]}}',
            stderr="",
        )

    def fake_score_run_artifacts(artifact_paths, *, output_dir, snapshot_root):  # type: ignore[no-untyped-def]
        normalized_calls["artifact_paths"] = list(artifact_paths)
        normalized_calls["output_dir"] = output_dir
        normalized_calls["snapshot_root"] = snapshot_root
        output_dir.mkdir(parents=True, exist_ok=True)
        snapshot_root.mkdir(parents=True, exist_ok=True)
        return [{"run_id": "batch-001-tool-001-arena-gpt54"}]

    def fake_build_site_data(*, normalized_dir, output_path):  # type: ignore[no-untyped-def]
        site_calls["normalized_dir"] = normalized_dir
        site_calls["output_path"] = output_path
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(json.dumps({"runs": []}))
        return {"runs": []}

    monkeypatch.setattr("scripts.run_benchmark.sync_agent_specs", fake_sync)
    monkeypatch.setattr("scripts.run_benchmark.subprocess.run", fake_run)
    monkeypatch.setattr("scripts.run_benchmark.score_run_artifacts", fake_score_run_artifacts)
    monkeypatch.setattr("scripts.run_benchmark.build_site_data", fake_build_site_data)

    summary = orchestrate_benchmark(
        workspace_root=workspace_root,
        project_root=project_root,
        task_path=task_path,
        runs_root=project_root / "data" / "runs",
        normalized_root=project_root / "data" / "normalized",
        site_output_path=project_root / "data" / "site" / "site-data.json",
        run_label="batch-001",
    )

    assert order == ["sync", "run"]
    assert summary["run_label"] == "batch-001"
    assert len(summary["artifact_paths"]) == 1

    artifact_path = Path(summary["artifact_paths"][0])
    payload = json.loads(artifact_path.read_text())
    assert payload["run_id"] == "batch-001-tool-001-arena-gpt54"
    assert payload["task_id"] == "tool-001"
    assert payload["task_title"] == "Read a file and return exact token"
    assert payload["category"] == "tool_accuracy"
    assert payload["agent_id"] == "arena-gpt54"
    assert payload["prompt"].startswith("Benchmark task: Read a file and return exact token")
    assert payload["started_at"]
    assert payload["completed_at"]
    assert payload["response_json"] == {
        "sessionId": "sess-tool-001",
        "result": {"payloads": [{"text": "TOKEN-OK"}]},
    }
    assert payload["session_id"] == "sess-tool-001"
    assert payload["final_text"] == "TOKEN-OK"

    assert normalized_calls["artifact_paths"] == [artifact_path]
    assert normalized_calls["output_dir"] == project_root / "data" / "normalized" / "batch-001"
    assert site_calls["normalized_dir"] == project_root / "data" / "normalized" / "batch-001"
    assert site_calls["output_path"] == project_root / "data" / "site" / "batch-001-site-data.json"


def test_reset_generated_artifacts_preserves_gitkeep_files(tmp_path: Path) -> None:
    runs_dir = tmp_path / "runs"
    normalized_dir = tmp_path / "normalized"
    site_dir = tmp_path / "site"
    for directory in (runs_dir, normalized_dir, site_dir):
        directory.mkdir()
        (directory / ".gitkeep").write_text("")
        (directory / "stale.json").write_text("{}")
        nested = directory / "nested"
        nested.mkdir()
        (nested / "artifact.txt").write_text("old")

    summary = reset_generated_artifacts(
        runs_dir=runs_dir,
        normalized_dir=normalized_dir,
        site_dir=site_dir,
    )

    assert summary == {
        "runs_removed": 2,
        "normalized_removed": 2,
        "site_removed": 2,
    }
    assert [path.name for path in runs_dir.iterdir()] == [".gitkeep"]
    assert [path.name for path in normalized_dir.iterdir()] == [".gitkeep"]
    assert [path.name for path in site_dir.iterdir()] == [".gitkeep"]
