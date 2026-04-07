from __future__ import annotations

from collections.abc import Iterable
from typing import Any


DIMENSION_BASE: dict[str, int] = {
    "task_completion": 20,
    "tool_accuracy": 20,
    "autonomy_continuity": 15,
    "recovery_behavior": 10,
    "verification_honesty": 10,
    "acpx_codex_reliability": 15,
    "output_quality": 5,
    "latency_cost_efficiency": 5,
}


def _coerce_failure_tags(value: Any) -> set[str]:
    if isinstance(value, str):
        return {value}
    if isinstance(value, Iterable):
        return {str(item) for item in value if item is not None}
    return set()


def _coerce_tool_errors(value: Any) -> list[str]:
    if not value:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, Iterable):
        return [str(item) for item in value if item is not None]
    return [str(value)]


def _clamp(value: int) -> int:
    return max(0, value)


def score_run(run: dict[str, Any]) -> dict[str, Any]:
    dimensions = dict(DIMENSION_BASE)
    failure_tags = _coerce_failure_tags(run.get("failure_tags"))
    tool_errors = _coerce_tool_errors(run.get("tool_errors"))

    if "fake_tool_call_text" in failure_tags:
        dimensions["tool_accuracy"] = 0
        dimensions["autonomy_continuity"] = _clamp(dimensions["autonomy_continuity"] - 8)

    if "empty_tool_args" in failure_tags:
        dimensions["tool_accuracy"] = _clamp(dimensions["tool_accuracy"] - 10)

    if "needs_reprompt" in failure_tags:
        dimensions["autonomy_continuity"] = _clamp(dimensions["autonomy_continuity"] - 7)

    if "run_timeout" in failure_tags:
        dimensions["task_completion"] = 0
        dimensions["latency_cost_efficiency"] = 0
        dimensions["output_quality"] = 0

    if "delegate_recovery" in failure_tags:
        dimensions["acpx_codex_reliability"] = _clamp(
            dimensions["acpx_codex_reliability"] - 9
        )

    if tool_errors:
        dimensions["recovery_behavior"] = _clamp(dimensions["recovery_behavior"] - 4)

    total = sum(dimensions.values())
    verdict = "fail" if failure_tags or tool_errors else "pass"

    return {
        "dimensions": dimensions,
        "total": total,
        "failure_tags": sorted(failure_tags),
        "tool_errors": tool_errors,
        "verdict": verdict,
    }
