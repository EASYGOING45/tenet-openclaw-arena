"""
Scoring engine for behavior-trace evaluation tasks.

Takes parsed events + task definition → score + verdict.
"""

from __future__ import annotations

import re
from typing import Any


def score(events: list[dict[str, Any]], task: dict[str, Any]) -> tuple[float, str]:
    """
    Score a run based on evaluation.scoring.rules.

    Args:
        events: List of parsed event dicts from parse_events()
        task: Full task dict loaded from YAML

    Returns:
        (score, verdict) where verdict is "PASS" | "PARTIAL" | "FAIL"
    """
    eval_config = task.get("evaluation", {})
    scoring_config = eval_config.get("scoring", {})

    rules = scoring_config.get("rules", [])
    min_score = scoring_config.get("min_score", 0)
    max_score = scoring_config.get("max_score", 100)
    pass_threshold = eval_config.get("pass_threshold", 70)
    # fail_threshold defaults to half of pass_threshold if not set
    fail_threshold = eval_config.get("fail_threshold", pass_threshold / 2)

    total = 0.0

    for rule in rules:
        matched = _check_rule(rule, events)
        if matched:
            raw_score = rule.get("score", 0)
            # score can be "+40", "-20", "40", "+40", etc.
            if isinstance(raw_score, str):
                raw_score = float(raw_score.lstrip("+"))
            total += raw_score

    # Clamp to [min_score, max_score]
    clamped = max(min_score, min(max_score, total))

    # Determine verdict
    if clamped >= pass_threshold:
        verdict = "PASS"
    elif clamped >= fail_threshold:
        verdict = "PARTIAL"
    else:
        verdict = "FAIL"

    return clamped, verdict


def _check_rule(rule: dict[str, Any], events: list[dict[str, Any]]) -> bool:
    """
    Check if a scoring rule matches any event in the event list.

    Rule fields:
      - event: event type to match (e.g., "skill_dispatch", "direct_code_write")
      - condition: optional Python eval condition (e.g., 'skill == "brainstorming"')
      - skill: optional shortcut for skill == value
      - tool: optional shortcut for tool == value
    """
    event_type = rule.get("event", "")
    condition = rule.get("condition", "")
    rule_skill = rule.get("skill")
    rule_tool = rule.get("tool")

    for evt in events:
        # Type match
        if event_type and evt.get("type") != event_type:
            continue

        # Skill shortcut match
        if rule_skill is not None:
            if evt.get("skill") != rule_skill:
                continue

        # Tool shortcut match
        if rule_tool is not None:
            if evt.get("tool") != rule_tool:
                continue

        # Condition eval
        if condition:
            try:
                # Build safe eval context from event fields
                ctx = {
                    "skill": evt.get("skill") or "",
                    "tool": evt.get("tool") or "",
                    "type": evt.get("type") or "",
                    "line": evt.get("line") or "",
                    "source": evt.get("source") or "",
                    "content_preview": evt.get("content_preview") or "",
                }
                # Also allow checking rule-level fields
                if not eval(condition, {"__builtins__": {}}, ctx):
                    continue
            except Exception:
                # If eval fails, skip this event
                continue

        # All checks passed → rule matches
        return True

    return False


def score_with_breakdown(
    events: list[dict[str, Any]], task: dict[str, Any]
) -> tuple[float, str, list[dict[str, Any]]]:
    """
    Score with per-rule match details for debugging.

    Returns:
        (score, verdict, breakdown) where breakdown is a list of
        matched rule summaries.
    """
    eval_config = task.get("evaluation", {})
    scoring_config = eval_config.get("scoring", {})
    rules = scoring_config.get("rules", [])
    min_score = scoring_config.get("min_score", 0)
    max_score = scoring_config.get("max_score", 100)
    pass_threshold = eval_config.get("pass_threshold", 70)
    fail_threshold = eval_config.get("fail_threshold", pass_threshold / 2)

    total = 0.0
    breakdown = []

    for rule in rules:
        matched = False
        matched_event = None
        raw_score = rule.get("score", 0)
        if isinstance(raw_score, str):
            raw_score = float(raw_score.lstrip("+"))

        for evt in events:
            if evt.get("type") == rule.get("event"):
                skill_ok = rule.get("skill") is None or evt.get("skill") == rule.get("skill")
                tool_ok = rule.get("tool") is None or evt.get("tool") == rule.get("tool")
                cond_ok = True
                if rule.get("condition"):
                    ctx = {
                        "skill": evt.get("skill") or "",
                        "tool": evt.get("tool") or "",
                        "type": evt.get("type") or "",
                        "line": evt.get("line") or "",
                    }
                    try:
                        cond_ok = eval(rule["condition"], {"__builtins__": {}}, ctx)
                    except Exception:
                        cond_ok = False
                if skill_ok and tool_ok and cond_ok:
                    matched = True
                    matched_event = evt
                    break

        if matched:
            total += raw_score
            breakdown.append({
                "rule": rule.get("note", rule.get("event", "")),
                "score_delta": raw_score,
                "matched": True,
                "matched_event": matched_event,
            })
        else:
            breakdown.append({
                "rule": rule.get("note", rule.get("event", "")),
                "score_delta": 0,
                "matched": False,
                "matched_event": None,
            })

    clamped = max(min_score, min(max_score, total))

    if clamped >= pass_threshold:
        verdict = "PASS"
    elif clamped >= fail_threshold:
        verdict = "PARTIAL"
    else:
        verdict = "FAIL"

    return clamped, verdict, breakdown
