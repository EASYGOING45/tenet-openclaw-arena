from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any, Iterable


def load_transcript(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for line in path.read_text().splitlines():
        if not line.strip():
            continue
        rows.append(json.loads(line))
    return rows


def _find_session_id(value: Any) -> str | None:
    if isinstance(value, dict):
        for key in ("sessionId", "session_id", "sessionID"):
            session_id = value.get(key)
            if session_id:
                return str(session_id)
        for nested in value.values():
            session_id = _find_session_id(nested)
            if session_id:
                return session_id
    elif isinstance(value, list):
        for item in value:
            session_id = _find_session_id(item)
            if session_id:
                return session_id
    return None


def _extract_session_id(run_payload: dict[str, Any]) -> str | None:
    response_json = run_payload.get("response_json") or {}
    session_id = _find_session_id(response_json)
    if session_id:
        return session_id
    for key in ("sessionId", "session_id", "sessionID"):
        value = run_payload.get(key)
        if value:
            return str(value)
    return None


def resolve_transcript_path(run_payload: dict[str, Any]) -> Path:
    session_id = _extract_session_id(run_payload)
    if not session_id:
        raise ValueError("run payload is missing session id metadata")

    agent_id = run_payload.get("agent_id")
    if not agent_id:
        raise ValueError("run payload is missing agent_id metadata")

    return (
        Path.home()
        / ".openclaw"
        / "agents"
        / str(agent_id)
        / "sessions"
        / f"{session_id}.jsonl"
    )


def collect_transcript_snapshot(run_payload: dict[str, Any], destination: Path) -> Path:
    destination.parent.mkdir(parents=True, exist_ok=True)
    source = resolve_transcript_path(run_payload)
    if source.exists():
        shutil.copy2(source, destination)
        return destination

    fallback_text = str(
        run_payload.get("final_text")
        or run_payload.get("stdout")
        or "Transcript missing; using synthetic assistant fallback."
    ).strip()
    synthetic_row = {
        "type": "message",
        "message": {
            "role": "assistant",
            "content": [
                {
                    "type": "text",
                    "text": fallback_text,
                }
            ],
        },
        "synthetic": True,
        "sourceMissing": True,
    }
    destination.write_text(json.dumps(synthetic_row, ensure_ascii=False) + "\n")
    return destination


def _iter_content_items(value: Any) -> Iterable[dict[str, Any]]:
    if isinstance(value, dict):
        content = value.get("content")
        if isinstance(content, list):
            for item in content:
                if isinstance(item, dict):
                    yield item
        for nested_key in ("message", "payload", "data"):
            nested = value.get(nested_key)
            if nested is not None:
                yield from _iter_content_items(nested)
    elif isinstance(value, list):
        for item in value:
            yield from _iter_content_items(item)


def classify_failure_tags(transcript: Path | list[dict[str, Any]]) -> set[str]:
    rows = load_transcript(transcript) if isinstance(transcript, Path) else transcript
    tags: set[str] = set()
    for row in rows:
        for content in _iter_content_items(row):
            content_type = content.get("type")
            text = content.get("text", "")
            if content_type == "text" and isinstance(text, str):
                if "<function_calls>" in text or "<tool_calls>" in text:
                    tags.add("fake_tool_call_text")

            if content_type in {"toolCall", "tool_call"}:
                arguments = content.get("arguments")
                args = content.get("args")
                if arguments in ({}, None, "", []) and args in ({}, None, "", []):
                    tags.add("empty_tool_args")
                elif arguments == {} or args == {}:
                    tags.add("empty_tool_args")
    return tags
