from __future__ import annotations

import json
from pathlib import Path
import sys

from scripts.score_runs import main
from scripts.score_runs import normalize_run_output
from scripts.score_runs import score_run_artifacts


def test_normalize_run_output_maps_model_attaches_snapshot_and_score(
    tmp_path: Path, monkeypatch
) -> None:
    transcript = tmp_path / "session.jsonl"
    transcript.write_text(
        "\n".join(
            [
                '{"type":"message","message":{"role":"assistant","content":[{"type":"text","text":"<function_calls><invoke name=\\"exec\\">"}]}}',
                '{"type":"message","message":{"role":"assistant","content":[{"type":"text","text":"Final answer after retry"}]}}',
            ]
        )
        + "\n"
    )
    snapshot_destination = tmp_path / "snapshots" / "run-001.jsonl"

    monkeypatch.setattr(
        "scripts.score_runs.collect_transcript_snapshot",
        lambda run_payload, destination: (
            destination.parent.mkdir(parents=True, exist_ok=True),
            destination.write_text(transcript.read_text()),
            destination,
        )[-1],
    )

    normalized = normalize_run_output(
        {
            "run_id": "run-001",
            "agent_id": "arena-gpt54",
            "task_id": "task-boot",
            "task_title": "Startup discipline",
            "response_json": {"sessionId": "sess-123"},
            "tool_errors": [],
            "failure_tags": ["needs_reprompt"],
            "final_text": 'I will now do it. read{"file_path":"/tmp/token.txt"}',
        },
        snapshot_root=tmp_path / "snapshots",
    )

    assert normalized["model"] == {
        "agent_id": "arena-gpt54",
        "slug": "gpt-5.4",
        "name": "GPT-5.4",
    }
    assert normalized["transcript"]["path"] == str(snapshot_destination)
    assert normalized["transcript"]["preview"] == "<function_calls><invoke name=\"exec\">\nFinal answer after retry"
    assert normalized["failure_tags"] == ["fake_tool_call_text", "needs_reprompt"]
    assert normalized["score"]["verdict"] == "fail"
    assert normalized["score"]["total"] == 65
    assert "response_json" not in normalized


def test_score_run_artifacts_writes_normalized_payloads(tmp_path: Path, monkeypatch) -> None:
    runs_dir = tmp_path / "runs"
    runs_dir.mkdir()
    artifacts = [
        runs_dir / "run-001.json",
        runs_dir / "run-002.json",
    ]
    artifacts[0].write_text(
        json.dumps(
            {
                "run_id": "run-001",
                "agent_id": "arena-gpt54",
                "task_id": "task-1",
                "response_json": {"sessionId": "sess-1"},
            }
        )
    )
    artifacts[1].write_text(
        json.dumps(
            {
                "run_id": "run-002",
                "agent_id": "arena-k2p5",
                "task_id": "task-2",
                "response_json": {"sessionId": "sess-2"},
            }
        )
    )

    snapshots: dict[str, str] = {
        "run-001": '{"type":"message","message":{"content":[{"type":"text","text":"Clean transcript"}]}}\n',
        "run-002": '{"type":"message","message":{"content":[{"type":"toolCall","name":"exec","arguments":{}}]}}\n',
    }

    def fake_collect(run_payload: dict[str, object], destination: Path) -> Path:
        run_id = str(run_payload["run_id"])
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(snapshots[run_id])
        return destination

    monkeypatch.setattr("scripts.score_runs.collect_transcript_snapshot", fake_collect)

    normalized = score_run_artifacts(
        artifacts,
        output_dir=tmp_path / "normalized",
        snapshot_root=tmp_path / "snapshots",
    )

    assert [item["run_id"] for item in normalized] == ["run-001", "run-002"]
    assert [item["score"]["verdict"] for item in normalized] == ["pass", "fail"]
    assert json.loads((tmp_path / "normalized" / "run-002.json").read_text())["model"][
        "name"
    ] == "Kimi K2.5"


def test_score_runs_main_normalizes_directory_inputs(tmp_path: Path, monkeypatch) -> None:
    runs_dir = tmp_path / "runs"
    runs_dir.mkdir()
    (runs_dir / "run-001.json").write_text(
        json.dumps(
            {
                "run_id": "run-001",
                "agent_id": "arena-gpt54",
                "response_json": {"sessionId": "sess-1"},
            }
        )
    )

    snapshot = '{"type":"message","message":{"content":[{"type":"text","text":"CLI transcript"}]}}\n'

    def fake_collect(run_payload: dict[str, object], destination: Path) -> Path:
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(snapshot)
        return destination

    monkeypatch.setattr("scripts.score_runs.collect_transcript_snapshot", fake_collect)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "score_runs.py",
            str(runs_dir),
            "--output-dir",
            str(tmp_path / "normalized"),
            "--snapshot-root",
            str(tmp_path / "snapshots"),
        ],
    )

    main()

    normalized_path = tmp_path / "normalized" / "run-001.json"
    assert normalized_path.exists()
    assert json.loads(normalized_path.read_text())["transcript"]["preview"] == "CLI transcript"


def test_score_runs_main_defaults_to_project_runs_directory(
    tmp_path: Path, monkeypatch
) -> None:
    runs_dir = tmp_path / "Projects" / "openclaw-model-arena" / "data" / "runs"
    runs_dir.mkdir(parents=True)
    (runs_dir / "run-001.json").write_text(
        json.dumps(
            {
                "run_id": "run-001",
                "agent_id": "arena-gpt54",
                "response_json": {"sessionId": "sess-1"},
            }
        )
    )

    snapshot = '{"type":"message","message":{"content":[{"type":"text","text":"Default CLI transcript"}]}}\n'

    def fake_collect(run_payload: dict[str, object], destination: Path) -> Path:
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(snapshot)
        return destination

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("scripts.score_runs.collect_transcript_snapshot", fake_collect)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "score_runs.py",
            "--output-dir",
            str(tmp_path / "normalized"),
            "--snapshot-root",
            str(tmp_path / "snapshots"),
        ],
    )

    main()

    normalized_path = tmp_path / "normalized" / "run-001.json"
    assert normalized_path.exists()
    assert json.loads(normalized_path.read_text())["transcript"]["preview"] == "Default CLI transcript"


def test_score_runs_main_recurses_into_batch_directories_and_ignores_manifests(
    tmp_path: Path, monkeypatch
) -> None:
    runs_root = tmp_path / "Projects" / "openclaw-model-arena" / "data" / "runs"
    batch_dir = runs_root / "batch-001"
    batch_dir.mkdir(parents=True)
    (batch_dir / "manifest.json").write_text('{"run_label":"batch-001"}')
    (batch_dir / "run-001.json").write_text(
        json.dumps(
            {
                "run_id": "run-001",
                "agent_id": "arena-gpt54",
                "response_json": {"sessionId": "sess-1"},
            }
        )
    )

    def fake_collect(run_payload: dict[str, object], destination: Path) -> Path:
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text('{"type":"message","message":{"content":[{"type":"text","text":"Nested batch"}]}}\n')
        return destination

    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr("scripts.score_runs.collect_transcript_snapshot", fake_collect)
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "score_runs.py",
            "--output-dir",
            str(tmp_path / "normalized"),
            "--snapshot-root",
            str(tmp_path / "snapshots"),
        ],
    )

    main()

    assert (tmp_path / "normalized" / "run-001.json").exists()
    assert not (tmp_path / "normalized" / "manifest.json").exists()


def test_normalize_run_output_marks_timeouts_and_delegate_recovery(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setattr(
        "scripts.score_runs.collect_transcript_snapshot",
        lambda run_payload, destination: (
            destination.parent.mkdir(parents=True, exist_ok=True),
            destination.write_text('{"type":"message","message":{"content":[{"type":"text","text":"Fallback"}]}}\n'),
            destination,
        )[-1],
    )

    normalized = normalize_run_output(
        {
            "run_id": "run-acpx",
            "agent_id": "arena-m27",
            "task_id": "acpx-001",
            "final_text": "Request timed out before a response was generated. The Codex session didn't write the file.",
            "response_json": {"sessionId": "sess-acpx"},
        },
        snapshot_root=tmp_path / "snapshots",
    )

    assert "run_timeout" in normalized["failure_tags"]
    assert "delegate_recovery" in normalized["failure_tags"]
    assert normalized["score"]["dimensions"]["task_completion"] == 0
