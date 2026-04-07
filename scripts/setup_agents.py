from __future__ import annotations

import json
import subprocess
from pathlib import Path


def build_agent_specs(workspace: str) -> list[dict[str, object]]:
    shared = {
        "workspace": workspace,
        "tools": {"alsoAllow": []},
    }
    return [
        {
            "id": "arena-gpt54",
            "model": {"primary": "openai-codex/gpt-5.4", "fallbacks": []},
            **shared,
        },
        {
            "id": "arena-m27",
            "model": {"primary": "minimax-cn/MiniMax-M2.7", "fallbacks": []},
            **shared,
        },
        {
            "id": "arena-k2p5",
            "model": {"primary": "kimi/k2p5", "fallbacks": []},
            **shared,
        },
    ]


def reconcile_agent_specs(
    existing_specs: list[dict[str, object]],
    desired_specs: list[dict[str, object]],
) -> list[dict[str, object]]:
    desired_by_id = {str(spec["id"]): spec for spec in desired_specs}
    reconciled: list[dict[str, object]] = []
    seen_desired_ids: set[str] = set()

    for spec in existing_specs:
        agent_id = str(spec.get("id", ""))
        replacement = desired_by_id.get(agent_id)
        if replacement is not None:
            reconciled.append(replacement)
            seen_desired_ids.add(agent_id)
        else:
            reconciled.append(spec)

    for spec in desired_specs:
        agent_id = str(spec["id"])
        if agent_id not in seen_desired_ids:
            reconciled.append(spec)

    return reconciled


def load_existing_agent_specs() -> list[dict[str, object]]:
    result = subprocess.run(
        ["openclaw", "config", "get", "agents.list", "--json"],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout or "[]")
    if isinstance(payload, dict):
        agents = payload.get("agents", [])
        if isinstance(agents, list):
            return list(agents)
        return []
    if isinstance(payload, list):
        return list(payload)
    return []


def sync_agent_specs(workspace: str) -> list[dict[str, object]]:
    desired_specs = build_agent_specs(workspace)
    existing_specs = load_existing_agent_specs()
    reconciled_specs = reconcile_agent_specs(existing_specs, desired_specs)
    subprocess.run(
        [
            "openclaw",
            "config",
            "set",
            "agents.list",
            json.dumps(reconciled_specs, ensure_ascii=False),
            "--strict-json",
        ],
        check=True,
    )
    return reconciled_specs


def main() -> None:
    workspace = str(Path.cwd().resolve().parents[1])
    sync_agent_specs(workspace)


if __name__ == "__main__":
    main()
