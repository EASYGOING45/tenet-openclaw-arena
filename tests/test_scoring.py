from __future__ import annotations

from benchmark.scoring import score_run


def test_score_run_returns_base_rubric_for_clean_run() -> None:
    result = score_run({})

    assert result["dimensions"] == {
        "task_completion": 20,
        "tool_accuracy": 20,
        "autonomy_continuity": 15,
        "recovery_behavior": 10,
        "verification_honesty": 10,
        "acpx_codex_reliability": 15,
        "output_quality": 5,
        "latency_cost_efficiency": 5,
    }
    assert result["total"] == 100


def test_score_run_penalizes_fake_tool_text_empty_args_and_reprompt() -> None:
    result = score_run(
        {
            "failure_tags": [
                "fake_tool_call_text",
                "empty_tool_args",
                "needs_reprompt",
            ],
            "tool_errors": ["Validation failed"],
        }
    )

    assert result["dimensions"]["tool_accuracy"] == 0
    assert result["dimensions"]["autonomy_continuity"] == 0
    assert result["dimensions"]["recovery_behavior"] == 6
    assert result["total"] == 61


def test_score_run_penalizes_timeouts_and_delegate_recovery() -> None:
    result = score_run(
        {
            "failure_tags": ["run_timeout", "delegate_recovery"],
        }
    )

    assert result["dimensions"]["task_completion"] == 0
    assert result["dimensions"]["latency_cost_efficiency"] == 0
    assert result["dimensions"]["output_quality"] == 0
    assert result["dimensions"]["acpx_codex_reliability"] == 6
    assert result["verdict"] == "fail"
