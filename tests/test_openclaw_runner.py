from __future__ import annotations

import json
from subprocess import CompletedProcess

from benchmark.openclaw_runner import build_agent_command, run_agent


def test_build_agent_command_uses_explicit_agent_and_json() -> None:
    command = build_agent_command("arena-gpt54", "run prompt")
    assert command[:4] == ["openclaw", "agent", "--agent", "arena-gpt54"]
    assert "--message" in command
    assert "run prompt" in command
    assert "--json" in command
    assert "--thinking" in command
    assert command[-1] == "low"


def test_build_agent_command_accepts_explicit_session_id() -> None:
    command = build_agent_command(
        "arena-gpt54",
        "run prompt",
        session_id="benchmark-run-001",
    )

    assert command[-2:] == ["--session-id", "benchmark-run-001"]


def test_run_agent_persists_raw_artifact_and_parses_response_json(
    tmp_path, monkeypatch
) -> None:
    def fake_run(command, capture_output, text, check):  # type: ignore[no-untyped-def]
        assert command == build_agent_command(
            "arena-gpt54",
            "run prompt",
            session_id="benchmark-run-001",
        )
        assert capture_output is True
        assert text is True
        assert check is False
        return CompletedProcess(
            args=command,
            returncode=0,
            stdout='{"sessionId":"abc-123"}',
            stderr="tool warning",
        )

    monkeypatch.setattr("benchmark.openclaw_runner.subprocess.run", fake_run)

    artifact = run_agent(
        "arena-gpt54",
        "run prompt",
        tmp_path,
        session_id="benchmark-run-001",
    )
    payload = json.loads(artifact.read_text())

    assert payload["agent_id"] == "arena-gpt54"
    assert payload["prompt"] == "run prompt"
    assert payload["returncode"] == 0
    assert payload["stdout"] == '{"sessionId":"abc-123"}'
    assert payload["stderr"] == "tool warning"
    assert payload["command"] == build_agent_command(
        "arena-gpt54",
        "run prompt",
        session_id="benchmark-run-001",
    )
    assert payload["response_json"] == {"sessionId": "abc-123"}


def test_run_agent_leaves_response_json_empty_for_non_json_stdout(
    tmp_path, monkeypatch
) -> None:
    def fake_run(command, capture_output, text, check):  # type: ignore[no-untyped-def]
        return CompletedProcess(
            args=command,
            returncode=1,
            stdout="plain text output",
            stderr="boom",
        )

    monkeypatch.setattr("benchmark.openclaw_runner.subprocess.run", fake_run)

    artifact = run_agent("arena-gpt54", "run prompt", tmp_path)
    payload = json.loads(artifact.read_text())

    assert payload["response_json"] is None
