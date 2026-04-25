from __future__ import annotations

import pytest
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


def test_score_run_empty_transcript_still_scores() -> None:
    """Empty transcript string should not crash or change scoring — scoring uses failure_tags."""
    result = score_run({"transcript": "", "failure_tags": []})
    assert result["total"] == 100
    assert result["verdict"] == "pass"


def test_score_run_unknown_failure_tag_is_ignored() -> None:
    """Unknown failure tags are included in output but have no scoring effect."""
    result = score_run({"failure_tags": ["completely_unknown_tag", "fake_tool_call_text"]})
    # Unknown tags are NOT filtered out — they appear in failure_tags output
    assert "completely_unknown_tag" in result["failure_tags"]
    # fake_tool_call_text is known and applied (penalizes tool_accuracy)
    assert result["dimensions"]["tool_accuracy"] == 0


def test_score_run_all_penalties_total_not_negative() -> None:
    """Applying all penalties simultaneously should not produce a negative total."""
    result = score_run(
        {
            "failure_tags": [
                "fake_tool_call_text",
                "empty_tool_args",
                "needs_reprompt",
                "run_timeout",
                "delegate_recovery",
            ],
            "tool_errors": ["error1", "error2"],
        }
    )
    assert result["total"] >= 0, f"Total should not be negative, got {result['total']}"


def test_score_run_empty_failure_and_tool_errors_is_pass() -> None:
    """No failure_tags and no tool_errors should produce verdict='pass'."""
    result = score_run({"failure_tags": [], "tool_errors": []})
    assert result["verdict"] == "pass"


def test_score_run_negative_tool_errors_becomes_empty() -> None:
    """Falsy values in tool_errors (None, 0, empty string) become empty list."""
    result = score_run({"tool_errors": None})  # type: ignore[arg-type]
    assert result["tool_errors"] == []
    result2 = score_run({"tool_errors": 0})
    assert result2["tool_errors"] == []


def test_score_run_string_failure_tag_works() -> None:
    """A single string failure_tag (not a list) should work."""
    result = score_run({"failure_tags": "run_timeout"})
    assert "run_timeout" in result["failure_tags"]
    assert result["dimensions"]["task_completion"] == 0


def test_score_run_null_failure_tags_handled_gracefully() -> None:
    """Null/None failure_tags should be handled gracefully."""
    result = score_run({"failure_tags": None})  # type: ignore[arg-type]
    assert result["failure_tags"] == []
    assert result["verdict"] == "pass"
