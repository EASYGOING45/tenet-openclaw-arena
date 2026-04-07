from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .schemas import BenchmarkTask


def _as_task(item: dict[str, Any]) -> BenchmarkTask:
    return BenchmarkTask(
        task_id=item["task_id"],
        title=item["title"],
        category=item["category"],
        prompt=item["prompt"],
        success_criteria=list(item["success_criteria"]),
    )


def load_tasks(path: str | Path) -> list[BenchmarkTask]:
    payload = json.loads(Path(path).read_text())
    return [_as_task(item) for item in payload["tasks"]]
