from __future__ import annotations

from collections import defaultdict
from datetime import datetime
from datetime import timezone
from typing import Any


def _aggregate_models(normalized_runs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, list[dict[str, Any]]] = defaultdict(list)
    metadata_by_slug: dict[str, dict[str, Any]] = {}

    for run in normalized_runs:
        model = run.get("model") or {}
        slug = str(model.get("slug") or "unknown")
        grouped[slug].append(run)
        metadata_by_slug[slug] = dict(model)

    scoreboard: list[dict[str, Any]] = []
    for slug, runs in grouped.items():
        totals = [float(run["score"]["total"]) for run in runs]
        pass_count = sum(1 for run in runs if run["score"]["verdict"] == "pass")
        dimension_totals: dict[str, float] = defaultdict(float)
        for run in runs:
            dimensions = run["score"].get("dimensions") or {}
            for key, value in dimensions.items():
                dimension_totals[str(key)] += float(value)

        scoreboard.append(
            {
                "model": metadata_by_slug[slug],
                "runs": len(runs),
                "pass_rate": pass_count / len(runs),
                "average_score": sum(totals) / len(totals),
                "dimension_averages": {
                    key: value / len(runs)
                    for key, value in sorted(dimension_totals.items())
                },
            }
        )

    scoreboard.sort(
        key=lambda row: (-float(row["average_score"]), str(row["model"].get("name", "")))
    )
    return scoreboard


def build_scoreboard(normalized_runs: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "models": _aggregate_models(normalized_runs),
    }


def build_site_payload(normalized_runs: list[dict[str, Any]]) -> dict[str, Any]:
    runs = sorted(normalized_runs, key=lambda item: str(item.get("run_id", "")))
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "scoreboard": build_scoreboard(runs),
        "runs": runs,
    }
