from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

TaskCategory = Literal[
    "startup_discipline",
    "tool_accuracy",
    "autonomy_continuity",
    "recovery_behavior",
    "verification_honesty",
    "acpx_codex",
]


@dataclass
class BenchmarkTask:
    task_id: str
    title: str
    category: TaskCategory
    prompt: str
    success_criteria: list[str]
