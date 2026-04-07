#!/usr/bin/env python3
"""
Sync tasks from YAML task library to SQLite database.
Reads data/benchmark/tasks/_index.yml and all *.yml task files,
then upserts them into the SQLite tasks table.

Usage:
    python3 scripts/sync_tasks.py
"""
import sqlite3, json, yaml, sys
from pathlib import Path

ARENA_ROOT = Path(__file__).parent.parent
INDEX_PATH = ARENA_ROOT / "data/benchmark/tasks/_index.yml"
DB_PATH = ARENA_ROOT / "backend/arena.db"


def load_tasks_from_yaml() -> list[dict]:
    """Load all tasks from YAML library."""
    index = yaml.safe_load(INDEX_PATH.read_text())
    tasks = []
    for entry in index.get("tasks", []):
        if not entry.get("is_active"):
            continue
        task_id = entry["task_id"]
        yaml_path = ARENA_ROOT / "data/benchmark/tasks" / entry["yaml_path"]
        if not yaml_path.exists():
            print(f"  SKIP {task_id}: file not found {yaml_path}", file=sys.stderr)
            continue

        task_data = yaml.safe_load(yaml_path.read_text())
        eval_config = task_data.get("evaluation", {})
        scoring = eval_config.get("scoring", {})

        tasks.append({
            "task_id": task_id,
            "title": entry.get("title", task_id),
            "capability": entry.get("capability", ""),
            "difficulty": entry.get("difficulty", "medium"),
            "description": task_data.get("prompt", {}).get("user", "")[:500],
            "yaml_path": entry["yaml_path"],
            "tags": json.dumps(entry.get("tags", [])),
            "timeout_seconds": eval_config.get("timeout_seconds", 180),
            "scoring_rules": json.dumps(scoring.get("rules", [])),
            "pass_threshold": scoring.get("pass_threshold", 70.0),
            "fail_threshold": scoring.get("fail_threshold", 40.0),
            "is_active": 1,
        })
    return tasks


def sync_agents() -> list[dict]:
    """Load known agents — hardcoded mapping from OpenClaw agents."""
    return [
        {
            "agent_id": "arena-m27",
            "model_id": "minimax-m2.7",
            "provider": "MiniMax",
            "model_name": "MiniMax-M2.7",
            "license_type": "Proprietary",
            "input_price": 0.30,
            "output_price": 1.20,
            "context_length": 204800,
            "is_active": 1,
        },
        {
            "agent_id": "arena-k2p5",
            "model_id": "kimi-k2p5",
            "provider": "Moonshot",
            "model_name": "Kimi-K2P5",
            "license_type": "Modified MIT",
            "input_price": 0.60,
            "output_price": 3.00,
            "context_length": 262144,
            "is_active": 1,
        },
        {
            "agent_id": "arena-gpt54",
            "model_id": "gpt-5.4",
            "provider": "OpenAI",
            "model_name": "GPT-5.4",
            "license_type": "Proprietary",
            "input_price": 5.00,
            "output_price": 25.00,
            "context_length": 1000000,
            "is_active": 1,
        },
    ]


def main():
    conn = sqlite3.connect(str(DB_PATH))
    cur = conn.cursor()

    # Ensure schema is up to date
    cur.execute("DROP TABLE IF EXISTS runs")
    cur.execute("DROP TABLE IF EXISTS tasks")
    cur.execute("DROP TABLE IF EXISTS agents")

    cur.execute(
        "CREATE TABLE agents ("
        "agent_id TEXT PRIMARY KEY,"
        "model_id TEXT NOT NULL,"
        "provider TEXT NOT NULL,"
        "model_name TEXT NOT NULL,"
        "license_type TEXT NOT NULL,"
        "input_price REAL,"
        "output_price REAL,"
        "context_length INTEGER,"
        "is_active INTEGER DEFAULT 1"
        ")"
    )
    cur.execute(
        "CREATE TABLE tasks ("
        "task_id TEXT PRIMARY KEY,"
        "title TEXT NOT NULL,"
        "capability TEXT NOT NULL,"
        "difficulty TEXT NOT NULL,"
        "description TEXT NOT NULL,"
        "yaml_path TEXT NOT NULL,"
        "tags TEXT NOT NULL,"
        "timeout_seconds INTEGER DEFAULT 180,"
        "scoring_rules TEXT NOT NULL,"
        "pass_threshold REAL DEFAULT 70,"
        "fail_threshold REAL DEFAULT 40,"
        "is_active INTEGER DEFAULT 1"
        ")"
    )
    cur.execute(
        "CREATE TABLE runs ("
        "run_id TEXT NOT NULL,"
        "run_group TEXT NOT NULL,"
        "agent_id TEXT NOT NULL,"
        "task_id TEXT NOT NULL,"
        "score REAL NOT NULL,"
        "verdict TEXT NOT NULL,"
        "duration_ms INTEGER,"
        "events TEXT NOT NULL,"
        "error TEXT,"
        "created_at TEXT NOT NULL,"
        "PRIMARY KEY (run_id, agent_id, task_id)"
        ")"
    )
    cur.execute("CREATE INDEX idx_runs_agent ON runs(agent_id)")
    cur.execute("CREATE INDEX idx_runs_task ON runs(task_id)")
    cur.execute("CREATE INDEX idx_runs_group ON runs(run_group)")

    # Sync agents
    agents = sync_agents()
    for a in agents:
        cur.execute(
            "INSERT OR REPLACE INTO agents "
            "(agent_id,model_id,provider,model_name,license_type,"
            "input_price,output_price,context_length,is_active) "
            "VALUES (?,?,?,?,?,?,?,?,?)",
            (a["agent_id"], a["model_id"], a["provider"], a["model_name"],
             a["license_type"], a["input_price"], a["output_price"],
             a["context_length"], a["is_active"]),
        )

    # Sync tasks
    tasks = load_tasks_from_yaml()
    for t in tasks:
        cur.execute(
            "INSERT OR REPLACE INTO tasks "
            "(task_id,title,capability,difficulty,description,yaml_path,"
            "tags,timeout_seconds,scoring_rules,pass_threshold,fail_threshold,is_active) "
            "VALUES (?,?,?,?,?,?,?,?,?,?,?,?)",
            (t["task_id"], t["title"], t["capability"], t["difficulty"],
             t["description"], t["yaml_path"], t["tags"], t["timeout_seconds"],
             t["scoring_rules"], t["pass_threshold"], t["fail_threshold"],
             t["is_active"]),
        )

    conn.commit()

    # Verify
    n_tasks = cur.execute("SELECT COUNT(*) FROM tasks WHERE is_active = 1").fetchone()[0]
    n_agents = cur.execute("SELECT COUNT(*) FROM agents WHERE is_active = 1").fetchone()[0]
    print(f"Synced {n_agents} agents and {n_tasks} tasks to {DB_PATH}")
    conn.close()


if __name__ == "__main__":
    main()
