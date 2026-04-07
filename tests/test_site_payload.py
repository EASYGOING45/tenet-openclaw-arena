from __future__ import annotations

import json
from pathlib import Path
import sys

from benchmark.site_payload import build_scoreboard
from benchmark.site_payload import build_site_payload
from scripts.build_site_data import build_site_data
from scripts.build_site_data import main


def test_build_scoreboard_rolls_up_model_metrics() -> None:
    scoreboard = build_scoreboard(
        [
            {
                "model": {"slug": "gpt-5.4", "name": "GPT-5.4"},
                "score": {
                    "total": 90,
                    "verdict": "pass",
                    "dimensions": {"tool_accuracy": 20, "autonomy_continuity": 15},
                },
            },
            {
                "model": {"slug": "gpt-5.4", "name": "GPT-5.4"},
                "score": {
                    "total": 70,
                    "verdict": "fail",
                    "dimensions": {"tool_accuracy": 10, "autonomy_continuity": 5},
                },
            },
            {
                "model": {"slug": "k2.5", "name": "Kimi K2.5"},
                "score": {
                    "total": 60,
                    "verdict": "fail",
                    "dimensions": {"tool_accuracy": 0, "autonomy_continuity": 0},
                },
            },
        ]
    )

    assert [row["model"]["name"] for row in scoreboard["models"]] == ["GPT-5.4", "Kimi K2.5"]
    assert scoreboard["models"][0]["runs"] == 2
    assert scoreboard["models"][0]["pass_rate"] == 0.5
    assert scoreboard["models"][0]["average_score"] == 80.0
    assert scoreboard["models"][0]["dimension_averages"] == {
        "autonomy_continuity": 10.0,
        "tool_accuracy": 15.0,
    }


def test_build_site_payload_orders_runs_and_embeds_scoreboard() -> None:
    payload = build_site_payload(
        [
            {
                "run_id": "run-b",
                "model": {"slug": "k2.5", "name": "Kimi K2.5"},
                "score": {
                    "total": 60,
                    "verdict": "fail",
                    "dimensions": {"tool_accuracy": 0},
                },
            },
            {
                "run_id": "run-a",
                "model": {"slug": "gpt-5.4", "name": "GPT-5.4"},
                "score": {
                    "total": 90,
                    "verdict": "pass",
                    "dimensions": {"tool_accuracy": 20},
                },
            },
        ]
    )

    assert [run["run_id"] for run in payload["runs"]] == ["run-a", "run-b"]
    assert payload["scoreboard"]["models"][0]["model"]["name"] == "GPT-5.4"


def test_build_site_data_reads_normalized_runs_and_writes_site_json(tmp_path: Path) -> None:
    normalized_dir = tmp_path / "normalized"
    normalized_dir.mkdir()
    (normalized_dir / "run-001.json").write_text(
        json.dumps(
            {
                "run_id": "run-001",
                "model": {"slug": "gpt-5.4", "name": "GPT-5.4"},
                "score": {
                    "total": 100,
                    "verdict": "pass",
                    "dimensions": {"tool_accuracy": 20},
                },
            }
        )
    )
    (normalized_dir / "run-002.json").write_text(
        json.dumps(
            {
                "run_id": "run-002",
                "model": {"slug": "k2.5", "name": "Kimi K2.5"},
                "score": {
                    "total": 50,
                    "verdict": "fail",
                    "dimensions": {"tool_accuracy": 0},
                },
            }
        )
    )

    output_path = tmp_path / "site" / "site-data.json"
    payload = build_site_data(normalized_dir=normalized_dir, output_path=output_path)

    assert output_path.exists()
    assert json.loads(output_path.read_text()) == payload
    assert [row["model"]["name"] for row in payload["scoreboard"]["models"]] == [
        "GPT-5.4",
        "Kimi K2.5",
    ]


def test_build_site_data_does_not_overwrite_public_snapshot_for_tmp_outputs(tmp_path: Path) -> None:
    normalized_dir = tmp_path / "normalized"
    normalized_dir.mkdir()
    (normalized_dir / "run-001.json").write_text(
        json.dumps(
            {
                "run_id": "run-001",
                "model": {"slug": "gpt-5.4", "name": "GPT-5.4"},
                "score": {
                    "total": 100,
                    "verdict": "pass",
                    "dimensions": {"tool_accuracy": 20},
                },
            }
        )
    )

    public_output_path = Path(__file__).resolve().parents[1] / "app" / "public" / "site-data.json"
    original_public_snapshot = public_output_path.read_text() if public_output_path.exists() else None

    output_path = tmp_path / "site" / "site-data.json"
    build_site_data(normalized_dir=normalized_dir, output_path=output_path)

    assert output_path.exists()
    if original_public_snapshot is None:
        assert not public_output_path.exists()
    else:
        assert public_output_path.read_text() == original_public_snapshot


def test_build_site_data_main_writes_cli_output(tmp_path: Path, monkeypatch) -> None:
    normalized_dir = tmp_path / "normalized"
    normalized_dir.mkdir()
    (normalized_dir / "run-001.json").write_text(
        json.dumps(
            {
                "run_id": "run-001",
                "model": {"slug": "gpt-5.4", "name": "GPT-5.4"},
                "score": {
                    "total": 100,
                    "verdict": "pass",
                    "dimensions": {"tool_accuracy": 20},
                },
            }
        )
    )

    output_path = tmp_path / "site" / "site-data.json"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "build_site_data.py",
            "--normalized-dir",
            str(normalized_dir),
            "--output-path",
            str(output_path),
        ],
    )

    main()

    assert output_path.exists()
    assert json.loads(output_path.read_text())["scoreboard"]["models"][0]["model"]["name"] == "GPT-5.4"


def test_build_site_data_recurses_into_batch_directories(tmp_path: Path) -> None:
    normalized_dir = tmp_path / "normalized"
    batch_dir = normalized_dir / "batch-001"
    transcript_dir = batch_dir / "transcripts"
    transcript_dir.mkdir(parents=True)
    (batch_dir / "run-001.json").write_text(
        json.dumps(
            {
                "run_id": "run-001",
                "model": {"slug": "gpt-5.4", "name": "GPT-5.4"},
                "score": {
                    "total": 100,
                    "verdict": "pass",
                    "dimensions": {"tool_accuracy": 20},
                },
            }
        )
    )
    (transcript_dir / "run-001.json").write_text('{"ignored":true}')

    output_path = tmp_path / "site" / "site-data.json"
    payload = build_site_data(normalized_dir=normalized_dir, output_path=output_path)

    assert [run["run_id"] for run in payload["runs"]] == ["run-001"]
