import json
from subprocess import CompletedProcess

from scripts.setup_agents import build_agent_specs
from scripts.setup_agents import reconcile_agent_specs
from scripts.setup_agents import sync_agent_specs


def test_build_agent_specs_contains_three_benchmark_agents() -> None:
    specs = build_agent_specs("/Users/golden-tenet/claw-spaces/Phoebe")

    assert [spec["id"] for spec in specs] == ["arena-gpt54", "arena-m27", "arena-k2p5"]
    assert specs[0]["model"]["primary"] == "openai-codex/gpt-5.4"


def test_reconcile_agent_specs_replaces_existing_arena_agents() -> None:
    desired = build_agent_specs("/Users/golden-tenet/claw-spaces/Phoebe")
    existing = [
        {"id": "other-agent", "model": {"primary": "x"}, "workspace": "keep"},
        {"id": "arena-gpt54", "model": {"primary": "old-model"}, "workspace": "old"},
        {"id": "arena-k2p5", "model": {"primary": "old-kimi"}, "workspace": "old"},
    ]

    reconciled = reconcile_agent_specs(existing, desired)

    assert [spec["id"] for spec in reconciled] == [
        "other-agent",
        "arena-gpt54",
        "arena-k2p5",
        "arena-m27",
    ]
    assert reconciled[1]["model"]["primary"] == "openai-codex/gpt-5.4"
    assert reconciled[2]["model"]["primary"] == "kimi/k2p5"
    assert reconciled.count(desired[0]) == 1


def test_sync_agent_specs_uses_full_list_replacement(monkeypatch) -> None:
    calls: list[list[str]] = []

    def fake_run(args, **kwargs):
        calls.append(list(args))
        if args[:4] == ["openclaw", "config", "get", "agents.list"]:
            return CompletedProcess(args=args, returncode=0, stdout=json.dumps([
                {"id": "arena-gpt54", "model": {"primary": "old-model"}, "workspace": "old"},
                {"id": "other-agent", "model": {"primary": "x"}, "workspace": "keep"},
            ]), stderr="")
        return CompletedProcess(args=args, returncode=0, stdout="", stderr="")

    monkeypatch.setattr("scripts.setup_agents.subprocess.run", fake_run)

    reconciled = sync_agent_specs("/Users/golden-tenet/claw-spaces/Phoebe")

    assert calls[0][:4] == ["openclaw", "config", "get", "agents.list"]
    assert calls[1][:4] == ["openclaw", "config", "set", "agents.list"]
    assert "agents.list[+]" not in calls[1]
    assert reconciled[0]["id"] == "arena-gpt54"
    assert reconciled[1]["id"] == "other-agent"
