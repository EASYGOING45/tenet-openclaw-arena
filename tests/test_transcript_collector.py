from __future__ import annotations

import json
from pathlib import Path

from benchmark.transcript_collector import (
    classify_failure_tags,
    collect_transcript_snapshot,
    load_transcript,
    resolve_transcript_path,
)


def test_load_transcript_reads_jsonl_rows(tmp_path: Path) -> None:
    transcript = tmp_path / "sample.jsonl"
    transcript.write_text(
        "\n".join(
            [
                '{"type":"message","id":"one"}',
                "",
                '{"type":"message","id":"two"}',
            ]
        )
        + "\n"
    )

    rows = load_transcript(transcript)

    assert rows == [
        {"type": "message", "id": "one"},
        {"type": "message", "id": "two"},
    ]


def test_resolve_transcript_path_uses_agent_and_session_id() -> None:
    path = resolve_transcript_path(
        {
            "agent_id": "arena-gpt54",
            "response_json": {"sessionId": "abc-123"},
        }
    )

    assert str(path).endswith(".openclaw/agents/arena-gpt54/sessions/abc-123.jsonl")


def test_resolve_transcript_path_reads_nested_session_id_metadata() -> None:
    path = resolve_transcript_path(
        {
            "agent_id": "arena-gpt54",
            "response_json": {
                "result": {
                    "meta": {
                        "agentMeta": {
                            "sessionId": "nested-456",
                        }
                    }
                }
            },
        }
    )

    assert str(path).endswith(".openclaw/agents/arena-gpt54/sessions/nested-456.jsonl")


def test_collect_transcript_snapshot_copies_source_transcript(
    tmp_path: Path, monkeypatch
) -> None:
    source = tmp_path / "source.jsonl"
    source.write_text('{"type":"message","id":"one"}\n')
    destination = tmp_path / "artifacts" / "snapshot.jsonl"

    monkeypatch.setattr(
        "benchmark.transcript_collector.resolve_transcript_path",
        lambda run_payload: source,
    )

    copied = collect_transcript_snapshot(
        {"agent_id": "arena-gpt54", "response_json": {"sessionId": "abc-123"}},
        destination,
    )

    assert copied == destination
    assert destination.read_text() == source.read_text()


def test_collect_transcript_snapshot_falls_back_to_synthetic_text_when_source_missing(
    tmp_path: Path, monkeypatch
) -> None:
    destination = tmp_path / "artifacts" / "snapshot.jsonl"

    monkeypatch.setattr(
        "benchmark.transcript_collector.resolve_transcript_path",
        lambda run_payload: tmp_path / "missing.jsonl",
    )

    copied = collect_transcript_snapshot(
        {
            "agent_id": "arena-gpt54",
            "response_json": {"sessionId": "abc-123"},
            "final_text": "Synthetic fallback text",
        },
        destination,
    )

    assert copied == destination
    row = json.loads(destination.read_text())
    assert row["synthetic"] is True
    assert row["message"]["content"][0]["text"] == "Synthetic fallback text"


def test_classify_failure_tags_detects_fake_tool_and_empty_args(
    tmp_path: Path,
) -> None:
    transcript = tmp_path / "sample.jsonl"
    transcript.write_text(
        "\n".join(
            [
                '{"type":"message","message":{"role":"assistant","content":[{"type":"text","text":"<function_calls><invoke name=\\"memory_search\\">"}]}}',
                '{"type":"message","message":{"role":"assistant","content":[{"type":"toolCall","name":"exec","arguments":{}}]}}',
            ]
        )
        + "\n"
    )

    tags = classify_failure_tags(transcript)

    assert "fake_tool_call_text" in tags
    assert "empty_tool_args" in tags
