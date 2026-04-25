#!/usr/bin/env python3
"""
sync_yaml_tasks_to_db.py

Reads the Phase 2 YAML task corpus (data/benchmark/tasks/_index.yml) and
upserts all active tasks into the backend SQLite database (backend/arena.db).

Can be run standalone:
    python3 scripts/sync_yaml_tasks_to_db.py

Or via npm:
    cd backend && npm run db:seed-yaml   # tsx version

This script is the Python equivalent of backend/src/db/seed_yaml_tasks.ts.
"""

import json
import sqlite3
import sys
from pathlib import Path

ARENA_ROOT = Path(__file__).resolve().parents[1]  # Projects/openclaw-model-arena
INDEX_YAML = ARENA_ROOT / "data" / "benchmark" / "tasks" / "_index.yml"
DB_PATH = ARENA_ROOT / "backend" / "arena.db"


def parse_simple_yaml(content: str) -> dict:
    """
    Minimal YAML parser for the _index.yml format used by this project.
    Only handles the subset we actually use: top-level keys, lists, and scalar values.
    Does NOT handle nested dicts with indented keys, multi-line strings, etc.
    """
    lines = content.splitlines()
    result = {}
    stack = [result]
    path: list[str] = []

    for raw_line in lines:
        line = raw_line.rstrip()
        if not line or line.startswith("#"):
            continue

        indent = len(raw_line) - len(raw_line.lstrip())
        depth = indent // 2
        while len(path) > depth:
            path.pop()
            stack.pop()

        if ": " in line:
            key, _, val = line.partition(": ")
            key = key.strip()
            val = val.strip().strip("'\"")

            if depth == 0:
                node = result
            else:
                node = stack[-1]

            if isinstance(node, list):
                node.append({})
                stack.append(node[-1])
                path.append(key)
            elif isinstance(node, dict):
                node[key] = val if val else {}
                if val == "" or val.startswith("["):
                    # empty value or list marker — treat as new dict to be filled
                    stack.append(node[key])
                    path.append(key)
                else:
                    pass  # scalar value, done
        elif line.startswith("- "):
            item = line[2:].strip()
            parent = stack[-1]
            if isinstance(parent, dict):
                parent.setdefault("items", []).append(item)
            else:
                parent.append(item)
        else:
            # plain key: value
            key, _, val = line.partition(":")
            key = key.strip()
            val = (val.strip() or "").strip("'\"")
            if depth == 0:
                stack[-1][key] = val
            else:
                stack[-1][key] = val if val else {}

    return result


def extract_yaml_tasks(index_data: dict) -> list[dict]:
    """
    Extract active task summaries from the parsed _index.yml.
    Returns list of dicts with: task_id, title, yaml_path, capability, difficulty, is_active.
    """
    tasks = index_data.get("tasks", [])
    if isinstance(tasks, list) and len(tasks) > 0:
        if isinstance(tasks[0], str):
            # Simple list format: just task_ids
            return [
                {
                    "task_id": t,
                    "title": t.replace("-", " ").replace("_", " ").title(),
                    "yaml_path": f"{t.split('-')[0]}/{t}.yml",
                    "capability": t.split("-")[0],
                    "difficulty": "medium",
                    "is_active": True,
                }
                for t in tasks
            ]
        elif isinstance(tasks[0], dict):
            return [
                {
                    "task_id": t.get("task_id", ""),
                    "title": t.get("title", ""),
                    "yaml_path": t.get("yaml_path", ""),
                    "capability": t.get("capability", ""),
                    "difficulty": t.get("difficulty", "medium"),
                    "is_active": t.get("is_active", True),
                }
                for t in tasks
                if t.get("is_active", True) is not False
            ]
    return []


def load_task_description(yaml_path: Path) -> str:
    """Load a YAML task file and extract the user-prompt excerpt for description."""
    if not yaml_path.exists():
        return ""

    try:
        import re

        content = yaml_path.read_text(encoding="utf-8")
        # Extract the user: field (simple regex, not a full YAML parser)
        m = re.search(r"^\s*user:\s*['\"]?(.+?)['\"]?\s*$", content, re.MULTILINE)
        if m:
            text = m.group(1).strip()
            return text[:200] + ("…" if len(text) > 200 else "")
    except Exception:
        pass
    return ""


def sync_yaml_tasks() -> int:
    if not INDEX_YAML.exists():
        print(f"❌ Index file not found: {INDEX_YAML}")
        return 1

    content = INDEX_YAML.read_text(encoding="utf-8")
    index_data = parse_simple_yaml(content)
    task_summaries = extract_yaml_tasks(index_data)

    print(f"📋 Found {len(task_summaries)} active YAML tasks in _index.yml")

    if not DB_PATH.exists():
        print(f"❌ Database not found: {DB_PATH}")
        return 1

    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()

    # Ensure capability column exists (migration)
    try:
        cursor.execute("ALTER TABLE tasks ADD COLUMN capability TEXT DEFAULT NULL")
        print("✅ Migrated: added capability column")
    except sqlite3.OperationalError as e:
        if "duplicate column name" not in str(e):
            raise

    upserted = 0
    skipped = 0

    for task in task_summaries:
        task_id = task["task_id"]
        yaml_path = ARENA_ROOT / "data" / "benchmark" / "tasks" / task["yaml_path"]
        description = load_task_description(yaml_path)
        if not description:
            description = f"[{task['capability']}] {task['title']}"

        scoring_criteria = json.dumps({"overall": 100})

        try:
            cursor.execute(
                """
                INSERT OR REPLACE INTO tasks
                  (id, name, category, difficulty, description, scoring_criteria, capability)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    task_id,
                    task["title"],
                    task["capability"],  # category = capability
                    task["difficulty"],
                    description,
                    scoring_criteria,
                    task["capability"],
                ),
            )
            upserted += 1
            print(f"  ✅ {task_id} — {task['title']}")
        except Exception as e:
            print(f"  ❌ {task_id}: {e}")
            skipped += 1

    conn.commit()

    cursor.execute("SELECT COUNT(*) FROM tasks")
    total = cursor.fetchone()[0]

    conn.close()

    print(f"\n✅ Sync complete: {upserted} upserted, {skipped} skipped")
    print(f"📊 Total tasks in DB: {total}")
    return 0


if __name__ == "__main__":
    sys.exit(sync_yaml_tasks())
