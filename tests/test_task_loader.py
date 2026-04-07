from pathlib import Path

from benchmark.task_loader import load_tasks


def test_load_tasks_returns_named_benchmark_tasks() -> None:
    tasks = load_tasks(Path("Projects/openclaw-model-arena/data/tasks/benchmark_tasks.json"))

    assert len(tasks) >= 6
    assert len({task.task_id for task in tasks}) == len(tasks)
    assert {task.category for task in tasks} == {
        "startup_discipline",
        "tool_accuracy",
        "autonomy_continuity",
        "recovery_behavior",
        "verification_honesty",
        "acpx_codex",
    }
    assert all(task.title and task.prompt and task.success_criteria for task in tasks)
    assert tasks[0].task_id
