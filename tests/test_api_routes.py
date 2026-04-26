"""
test_api_routes.py

API integration tests for the OpenClaw Model Arena backend.
Tests /api/tasks, /api/results, and /api/leaderboard endpoints.

Requires the backend to be running at http://localhost:3000.
Run with: pytest tests/test_api_routes.py -v
"""

import pytest
import urllib.request
import urllib.parse
import urllib.error
import json
from typing import Any


BASE_URL = "http://localhost:3000"


def api_get(path: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
    """Make a GET request to the backend API."""
    url = f"{BASE_URL}{path}"
    if params:
        url += "?" + "&".join(f"{k}={v}" for k, v in params.items())
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        return json.loads(resp.read().decode("utf-8"))


class TestTasksEndpoint:
    """Tests for GET /api/tasks."""

    def test_tasks_returns_list(self):
        """Response should be a dict with a 'tasks' key containing a list."""
        data = api_get("/api/tasks")
        assert "tasks" in data
        assert isinstance(data["tasks"], list)

    def test_tasks_has_minimum_fields(self):
        """Each task should have required fields."""
        data = api_get("/api/tasks")
        for task in data["tasks"]:
            assert "id" in task, "Task missing 'id'"
            assert "name" in task, "Task missing 'name'"
            assert "category" in task, "Task missing 'category'"
            assert "difficulty" in task, "Task missing 'difficulty'"
            assert "description" in task, "Task missing 'description'"
            assert "capability" in task, "Task missing 'capability'"

    def test_tasks_includes_yaml_corpus(self):
        """After YAML sync, should have ≥ 18 tasks (Phase 2 corpus)."""
        data = api_get("/api/tasks")
        assert len(data["tasks"]) >= 18, (
            f"Expected ≥18 tasks from YAML corpus, got {len(data['tasks'])}"
        )

    def test_yaml_tasks_have_capability(self):
        """Phase 2 YAML tasks should have a non-null capability field."""
        data = api_get("/api/tasks")
        yaml_tasks = [t for t in data["tasks"] if t["id"].startswith(("skill-", "tool-", "cli-", "computer-", "self-", "delegation-"))]
        assert len(yaml_tasks) >= 18, f"Expected ≥18 YAML tasks, got {len(yaml_tasks)}"
        for task in yaml_tasks:
            assert task["capability"] is not None, (
                f"Task {task['id']} has null capability"
            )

    def test_task_difficulty_values(self):
        """Difficulty should be one of the expected levels."""
        valid_difficulties = {"easy", "medium", "hard"}
        data = api_get("/api/tasks")
        for task in data["tasks"]:
            assert task["difficulty"] in valid_difficulties, (
                f"Task {task['id']} has invalid difficulty: {task['difficulty']}"
            )

    def test_task_capability_matches_category(self):
        """For YAML tasks, capability should equal category (both set to dimension)."""
        data = api_get("/api/tasks")
        yaml_tasks = [t for t in data["tasks"] if t.get("capability") is not None]
        for task in yaml_tasks:
            assert task["capability"] == task["category"], (
                f"Task {task['id']}: capability={task['capability']} != category={task['category']}"
            )


class TestResultsEndpoint:
    """Tests for GET /api/results."""

    def test_results_returns_list(self):
        """Response should be a dict with a 'results' key containing a list."""
        data = api_get("/api/results")
        assert "results" in data
        assert isinstance(data["results"], list)

    def test_results_has_required_fields(self):
        """Each result should have required fields."""
        data = api_get("/api/results")
        if len(data["results"]) == 0:
            pytest.skip("No results in DB yet")
        for result in data["results"]:
            assert "run_id" in result, "Result missing 'run_id'"
            assert "model_id" in result, "Result missing 'model_id'"
            assert "task_id" in result, "Result missing 'task_id'"
            assert "score" in result, "Result missing 'score'"
            assert "failure_label" in result, "Result missing 'failure_label'"

    def test_results_filter_by_run_id(self):
        """Filtering by run_id should return only matching results."""
        # First get a run_id from the full results
        all_results = api_get("/api/results")
        if len(all_results["results"]) == 0:
            pytest.skip("No results in DB")
        sample_run_id = all_results["results"][0]["run_id"]
        filtered = api_get("/api/results", params={"run_id": sample_run_id})
        for r in filtered["results"]:
            assert r["run_id"] == sample_run_id, (
                f"Expected run_id={sample_run_id}, got {r['run_id']}"
            )

    def test_results_filter_by_model_id(self):
        """Filtering by model_id should return only that model's results."""
        filtered = api_get("/api/results", params={"model_id": "gpt-5.4"})
        for r in filtered["results"]:
            assert r["model_id"] == "gpt-5.4", (
                f"Expected model_id=gpt-5.4, got {r['model_id']}"
            )

    def test_results_filter_by_task_id(self):
        """Filtering by task_id should return only that task's results."""
        filtered = api_get("/api/results", params={"task_id": "coding-loop"})
        for r in filtered["results"]:
            assert r["task_id"] == "coding-loop"

    def test_results_limit(self):
        """The limit parameter should cap the number of returned results."""
        data = api_get("/api/results", params={"limit": 3})
        assert len(data["results"]) <= 3, f"Expected ≤3 results, got {len(data['results'])}"


class TestLeaderboardEndpoint:
    """Tests for GET /api/leaderboard."""

    def test_leaderboard_returns_list(self):
        """Response should be a dict with a 'leaderboard' key containing a list."""
        data = api_get("/api/leaderboard")
        assert "leaderboard" in data
        assert isinstance(data["leaderboard"], list)

    def test_leaderboard_models_tracked(self):
        """Leaderboard should track the three benchmark models."""
        data = api_get("/api/leaderboard")
        model_ids = {entry["model_id"] for entry in data["leaderboard"]}
        assert "gpt-5.4" in model_ids
        assert "kimi-k2p5" in model_ids
        assert "minimax-m2.7" in model_ids

    def test_leaderboard_entry_fields(self):
        """Each entry should have required fields."""
        data = api_get("/api/leaderboard")
        if len(data["leaderboard"]) == 0:
            pytest.skip("No leaderboard entries")
        for entry in data["leaderboard"]:
            assert "rank" in entry
            assert "model_id" in entry
            assert "model_name" in entry
            assert "provider" in entry
            assert "license_type" in entry
            assert "score" in entry
            assert isinstance(entry["score"], (int, float))

    def test_leaderboard_rank_order(self):
        """Entries should be ordered by rank (1, 2, 3)."""
        data = api_get("/api/leaderboard")
        ranks = [entry["rank"] for entry in data["leaderboard"]]
        assert ranks == sorted(ranks), f"Ranks not sorted: {ranks}"

    def test_leaderboard_score_reasonable(self):
        """All scores should be between 0 and 100."""
        data = api_get("/api/leaderboard")
        for entry in data["leaderboard"]:
            assert 0 <= entry["score"] <= 100, (
                f"Model {entry['model_id']} has out-of-range score: {entry['score']}"
            )


class TestHealthEndpoint:
    """Tests for GET /health."""

    def test_health_returns_ok(self):
        """Health endpoint should return {status: 'ok'}."""
        req = urllib.request.Request(f"{BASE_URL}/health")
        with urllib.request.urlopen(req, timeout=5) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        assert data.get("status") == "ok"
