/**
 * seed_yaml_tasks.ts
 *
 * Reads all YAML tasks from data/benchmark/tasks/ and upserts them into the SQLite tasks table.
 * Runs standalone: npx tsx src/db/seed_yaml_tasks.ts
 *
 * Task schema (tasks table):
 *   id           TEXT PRIMARY KEY  — e.g. "skill-dispatch-001"
 *   name         TEXT NOT NULL     — task title
 *   category     TEXT NOT NULL     — maps to "capability" (dimension id)
 *   difficulty   TEXT NOT NULL     — easy | medium | hard
 *   description  TEXT NOT NULL     — short user-prompt excerpt
 *   scoring_criteria TEXT NOT NULL — JSON of {dimension: weight}
 *   capability   TEXT DEFAULT NULL — same as category (convenience alias)
 */

import Database from "better-sqlite3";
import { parse as parseYaml } from "yaml";
import path from "path";
import fs from "fs";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const DB_PATH = path.join(__dirname, "..", "..", "arena.db");
const PROJECT_ROOT = path.join(__dirname, "..", "..", "..");

interface YamlTaskSummary {
  task_id: string;
  title: string;
  yaml_path: string;
  capability: string;
  difficulty: string;
  is_active: boolean;
}

interface IndexYaml {
  tasks: YamlTaskSummary[];
}

function loadIndexYaml(indexPath: string): YamlTaskSummary[] {
  const content = fs.readFileSync(indexPath, "utf-8");
  const data = parseYaml(content) as IndexYaml;
  return (data.tasks || []).filter((t) => t.is_active !== false);
}

function loadYamlTaskFile(taskPath: string): Record<string, unknown> | null {
  if (!fs.existsSync(taskPath)) {
    return null;
  }
  try {
    const content = fs.readFileSync(taskPath, "utf-8");
    return parseYaml(content) as Record<string, unknown>;
  } catch {
    return null;
  }
}

function extractDescription(taskData: Record<string, unknown>): string {
  const prompt = taskData["prompt"] as Record<string, unknown> | undefined;
  const user = prompt?.["user"] as string | undefined;
  if (typeof user === "string" && user.length > 0) {
    // Truncate to 200 chars for the description field
    return user.length > 200 ? user.slice(0, 200) + "…" : user;
  }
  const title = taskData["title"] as string | undefined;
  return typeof title === "string" ? title : "No description available";
}

function extractScoringCriteria(
  taskData: Record<string, unknown>
): Record<string, number> {
  const evaluation = taskData["evaluation"] as
    | Record<string, unknown>
    | undefined;
  if (!evaluation) return { overall: 100 };

  const scoring = evaluation["scoring"] as
    | Record<string, unknown>
    | undefined;
  if (!scoring) return { overall: 100 };

  const rules = scoring["rules"] as Array<Record<string, unknown>> | undefined;
  if (!rules || !Array.isArray(rules)) return { overall: 100 };

  // Build a criteria map from rules that have conditions
  const criteria: Record<string, number> = {};
  for (const rule of rules) {
    const event = String(rule["event"] ?? "");
    const note = String(rule["note"] ?? event);
    const score = Number(rule["score"] ?? 0);
    if (event && note) {
      criteria[note] = Math.abs(score); // use absolute as weight hint
    }
  }

  return Object.keys(criteria).length > 0 ? criteria : { overall: 100 };
}

export function seedYamlTasks(): void {
  const db = new Database(DB_PATH);
  db.pragma("journal_mode = WAL");

  const indexPath = path.join(
    PROJECT_ROOT,
    "data",
    "benchmark",
    "tasks",
    "_index.yml"
  );

  if (!fs.existsSync(indexPath)) {
    throw new Error(`Index file not found: ${indexPath}`);
  }

  const summaries = loadIndexYaml(indexPath);
  console.log(`📋 Found ${summaries.length} active YAML tasks in _index.yml`);

  const insertOrUpdate = db.prepare(`
    INSERT OR REPLACE INTO tasks (id, name, category, difficulty, description, scoring_criteria, capability)
    VALUES (?, ?, ?, ?, ?, ?, ?)
  `);

  const tasksDir = path.join(PROJECT_ROOT, "data", "benchmark", "tasks");
  let upserted = 0;
  let skipped = 0;

  for (const summary of summaries) {
    const yamlPath = path.join(tasksDir, summary.yaml_path);
    const taskData = loadYamlTaskFile(yamlPath);

    const description = taskData
      ? extractDescription(taskData)
      : `[${summary.capability}] ${summary.title}`;

    const scoring_criteria = taskData
      ? extractScoringCriteria(taskData)
      : { overall: 100 };

    try {
      insertOrUpdate.run(
        summary.task_id,
        summary.title,
        summary.capability, // category = capability/dimension
        summary.difficulty,
        description,
        JSON.stringify(scoring_criteria),
        summary.capability // capability column = same as category
      );
      upserted++;
      console.log(`  ✅ ${summary.task_id} — ${summary.title}`);
    } catch (err) {
      console.error(`  ❌ Failed to upsert ${summary.task_id}:`, err);
      skipped++;
    }
  }

  // Report final count
  const { count } = db
    .prepare("SELECT COUNT(*) as count FROM tasks")
    .get() as { count: number };
  console.log(
    `\n✅ Seed complete: ${upserted} upserted, ${skipped} skipped`
  );
  console.log(`📊 Total tasks in DB: ${count}`);

  db.close();
}

// Allow both standalone execution and module import
const isMain = import.meta.url === `file://${process.argv[1]?.replace(/\\/g, "/")}`;
if (isMain) {
  seedYamlTasks();
}
