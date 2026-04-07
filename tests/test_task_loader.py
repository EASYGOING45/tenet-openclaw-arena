from pathlib import Path

from benchmark.task_loader import load_tasks

TASK_FILE = Path(__file__).parent.parent / "data/tasks/benchmark_tasks.json"


def test_load_tasks_returns_named_benchmark_tasks() -> None:
    tasks = load_tasks(TASK_FILE)

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
