from __future__ import annotations

import argparse
import json
from pathlib import Path
import re
import sys
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from benchmark.scoring import score_run
from benchmark.transcript_collector import classify_failure_tags
from benchmark.transcript_collector import collect_transcript_snapshot
from benchmark.transcript_collector import load_transcript


MODEL_BY_AGENT_ID: dict[str, dict[str, str]] = {
    "arena-gpt54": {"slug": "gpt-5.4", "name": "GPT-5.4"},
    "arena-m27": {"slug": "minimax-m2.7", "name": "MiniMax M2.7"},
    "arena-k2p5": {"slug": "k2.5", "name": "Kimi K2.5"},
}

SITE_KEYS = {
    "run_id",
    "task_id",
    "task_title",
    "category",
    "agent_id",
    "started_at",
    "completed_at",
    "session_id",
    "final_text",
    "fixture",
}

TEXT_TOOL_CALL_RE = re.compile(r"\b(read|write|edit|exec|apply_patch)\s*\{", re.IGNORECASE)


def _read_json(path: Path) -> dict[str, Any]:
    payload = json.loads(path.read_text())
    if not isinstance(payload, dict):
        raise ValueError(f"run artifact must contain an object: {path}")
    return payload


def _model_metadata(agent_id: str) -> dict[str, str]:
    metadata = MODEL_BY_AGENT_ID.get(agent_id)
    if metadata is not None:
        return {"agent_id": agent_id, **metadata}
    return {"agent_id": agent_id, "slug": agent_id, "name": agent_id}


def _snapshot_destination(run_payload: dict[str, Any], snapshot_root: Path) -> Path:
    run_id = str(run_payload.get("run_id") or run_payload.get("task_id") or "run")
    return snapshot_root / f"{run_id}.jsonl"


def _transcript_preview(snapshot_path: Path) -> str:
    preview_lines: list[str] = []
    for row in load_transcript(snapshot_path):
        message = row.get("message")
        if not isinstance(message, dict):
            continue
        content = message.get("content")
        if not isinstance(content, list):
            continue
        for item in content:
            if not isinstance(item, dict):
                continue
            text = item.get("text")
            if isinstance(text, str) and text.strip():
                preview_lines.append(text.strip())
    return "\n".join(preview_lines[:3])


def _site_ready_run_payload(run_payload: dict[str, Any]) -> dict[str, Any]:
    return {key: run_payload[key] for key in SITE_KEYS if key in run_payload}


def _heuristic_failure_tags(run_payload: dict[str, Any]) -> set[str]:
    text = str(
        run_payload.get("final_text")
        or run_payload.get("stdout")
        or ""
    )
    lowered = text.lower()
    tags: set[str] = set()

    if "request timed out before a response was generated" in lowered or "timed out" in lowered:
        tags.add("run_timeout")

    if TEXT_TOOL_CALL_RE.search(text):
        tags.add("fake_tool_call_text")

    if "didn't write the file" in lowered or "try the direct `acpx` path" in lowered:
        tags.add("delegate_recovery")

    return tags


def normalize_run_output(run_payload: dict[str, Any], *, snapshot_root: Path) -> dict[str, Any]:
    normalized = _site_ready_run_payload(run_payload)
    agent_id = str(run_payload.get("agent_id") or "unknown-agent")
    snapshot_path = collect_transcript_snapshot(
        run_payload,
        _snapshot_destination(run_payload, snapshot_root),
    )
    transcript_failure_tags = classify_failure_tags(snapshot_path)
    existing_failure_tags = {
        str(tag)
        for tag in run_payload.get("failure_tags", [])
        if tag is not None
    }
    heuristic_tags = _heuristic_failure_tags(run_payload)
    failure_tags = sorted(existing_failure_tags | transcript_failure_tags | heuristic_tags)
    score = score_run(
        {
            **run_payload,
            "failure_tags": failure_tags,
        }
    )

    normalized["model"] = _model_metadata(agent_id)
    normalized["failure_tags"] = failure_tags
    normalized["score"] = score
    normalized["transcript"] = {
        "path": str(snapshot_path),
        "preview": _transcript_preview(snapshot_path),
    }
    return normalized


def score_run_artifacts(
    artifact_paths: list[Path],
    *,
    output_dir: Path,
    snapshot_root: Path,
) -> list[dict[str, Any]]:
    output_dir.mkdir(parents=True, exist_ok=True)
    normalized_runs: list[dict[str, Any]] = []

    for path in sorted(artifact_paths):
        normalized = normalize_run_output(_read_json(path), snapshot_root=snapshot_root)
        normalized_runs.append(normalized)
        run_id = str(normalized.get("run_id") or path.stem)
        (output_dir / f"{run_id}.json").write_text(
            json.dumps(normalized, indent=2, sort_keys=True) + "\n"
        )

    normalized_runs.sort(key=lambda item: str(item.get("run_id", "")))
    return normalized_runs


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Normalize OpenClaw run artifacts.")
    parser.add_argument(
        "input_path",
        nargs="?",
        type=Path,
        default=Path("Projects/openclaw-model-arena/data/runs"),
        help="Run artifact JSON file or directory.",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("Projects/openclaw-model-arena/data/normalized"),
        help="Directory for normalized run JSON files.",
    )
    parser.add_argument(
        "--snapshot-root",
        type=Path,
        default=Path("Projects/openclaw-model-arena/data/normalized/transcripts"),
        help="Directory for copied transcript snapshots.",
    )
    return parser


def _resolve_artifact_paths(input_path: Path) -> list[Path]:
    if input_path.is_dir():
        return sorted(
            path
            for path in input_path.rglob("*.json")
            if path.name != "manifest.json" and "transcripts" not in path.parts
        )
    return [input_path]


def main() -> None:
    args = _build_parser().parse_args()
    score_run_artifacts(
        _resolve_artifact_paths(args.input_path),
        output_dir=args.output_dir,
        snapshot_root=args.snapshot_root,
    )


if __name__ == "__main__":
    main()
