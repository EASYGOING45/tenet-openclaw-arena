from __future__ import annotations

import json
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def build_agent_command(
    agent_id: str,
    prompt: str,
    *,
    session_id: str | None = None,
    thinking: str = "low",
    timeout_seconds: int | None = None,
) -> list[str]:
    command = [
        "openclaw",
        "agent",
        "--agent",
        agent_id,
        "--message",
        prompt,
        "--json",
        "--thinking",
        thinking,
    ]
    if session_id:
        command.extend(["--session-id", session_id])
    if timeout_seconds is not None:
        command.extend(["--timeout", str(timeout_seconds)])
    return command


def _parse_response_json(stdout: str) -> object | None:
    text = stdout.strip()
    if not text:
        return None
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return None


def extract_assistant_text(response_json: Any, *, fallback_stdout: str = "") -> str:
    if isinstance(response_json, dict):
        result = response_json.get("result")
        if isinstance(result, dict):
            payloads = result.get("payloads")
            if isinstance(payloads, list):
                texts = [
                    item.get("text", "").strip()
                    for item in payloads
                    if isinstance(item, dict) and isinstance(item.get("text"), str)
                ]
                joined = "\n".join(text for text in texts if text)
                if joined:
                    return joined
    return fallback_stdout.strip()


def run_agent(
    agent_id: str,
    prompt: str,
    output_dir: str | Path,
    *,
    session_id: str | None = None,
    thinking: str = "low",
    timeout_seconds: int | None = None,
) -> Path:
    command = build_agent_command(
        agent_id,
        prompt,
        session_id=session_id,
        thinking=thinking,
        timeout_seconds=timeout_seconds,
    )
    completed = subprocess.run(command, capture_output=True, text=True, check=False)
    run_id = f"{agent_id}-{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')}"
    destination = Path(output_dir) / f"{run_id}.json"
    response_json = _parse_response_json(completed.stdout)
    payload = {
        "agent_id": agent_id,
        "prompt": prompt,
        "returncode": completed.returncode,
        "stdout": completed.stdout,
        "stderr": completed.stderr,
        "command": command,
        "response_json": response_json,
        "final_text": extract_assistant_text(response_json, fallback_stdout=completed.stdout),
    }
    destination.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n")
    return destination
