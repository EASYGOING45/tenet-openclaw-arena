import Database from "better-sqlite3";
import { CREATE_TABLES_SQL } from "./schema.js";
import { seedYamlTasks } from "./seed_yaml_tasks.js";
import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const DB_PATH = path.join(__dirname, "..", "..", "arena.db");

// CLI args
export const REINIT_TASKS_FLAG = process.argv.includes("--reinit-tasks");
export const FULL_REINIT_FLAG = process.argv.includes("--full-reinit");

const db = new Database(DB_PATH);
db.pragma("journal_mode = WAL");

// Migration: add capability column to tasks if missing (existing DBs)
try {
  db.exec("ALTER TABLE tasks ADD COLUMN capability TEXT DEFAULT NULL");
  console.log("✅ Migrated: added capability column to tasks table");
} catch (err: any) {
  if (err.message?.includes("duplicate column name")) {
    // Already migrated, fine
  } else {
    // Table might not exist yet, let CREATE_TABLES_SQL handle it
  }
}

// Create tables
db.exec(CREATE_TABLES_SQL);

// Seed models
const insertModel = db.prepare(`
  INSERT OR REPLACE INTO models (id, name, provider, license_type, input_price, output_price, context_length, is_codex_harness)
  VALUES (?, ?, ?, ?, ?, ?, ?, ?)
`);

const models = [
  ["minimax-m2.7", "MiniMax-M2.7", "MiniMax", "Proprietary", 0.30, 1.20, 204800, 0],
  ["kimi-k2p5", "Kimi-K2.5", "Moonshot", "Modified MIT", 0.60, 3.00, 262144, 0],
  ["gpt-5.4", "GPT-5.4", "OpenAI", "Proprietary", 5.00, 25.00, 1000000, 0],
];

for (const m of models) {
  insertModel.run(...m);
}

// Seed tasks (legacy 6 tasks — capability is NULL for these)
const insertTask = db.prepare(`
  INSERT OR REPLACE INTO tasks (id, name, category, difficulty, description, scoring_criteria, capability)
  VALUES (?, ?, ?, ?, ?, ?, ?)
`);

const tasks = [
  [
    "coding-loop",
    "Loop Coding",
    "Coding",
    "hard",
    "用 loop 替代 lodash 包，实现以下函数：map、filter、reduce 等数组方法。",
    JSON.stringify({ style: 20, correctness: 80 }),
    null, // legacy tasks have no capability/dimension
  ],
  [
    "readme-audit",
    "README Audit",
    "Tool Use",
    "medium",
    "审查并改进 README 文档的完整性、可读性和准确性。",
    JSON.stringify({ clarity: 30, completeness: 40, accuracy: 30 }),
    null,
  ],
  [
    "context-summary",
    "Context Summary",
    "Reasoning",
    "medium",
    "根据提供的长文本提取关键信息并生成简洁摘要。",
    JSON.stringify({ relevance: 40, conciseness: 30, accuracy: 30 }),
    null,
  ],
  [
    "json-extract",
    "JSON Extract",
    "Coding",
    "easy",
    "从复杂 JSON 结构中提取指定字段并返回结构化结果。",
    JSON.stringify({ correctness: 70, edge_cases: 20, style: 10 }),
    null,
  ],
  [
    "file-search",
    "File Search",
    "Tool Use",
    "medium",
    "在指定目录树中搜索匹配条件的文件并返回路径列表。",
    JSON.stringify({ accuracy: 50, efficiency: 30, completeness: 20 }),
    null,
  ],
  [
    "multi-step-reasoning",
    "Multi-Step Reasoning",
    "Reasoning",
    "hard",
    "解决需要多步推理的复杂逻辑问题，每步需要正确的子结论支撑。",
    JSON.stringify({ reasoning: 50, correctness: 40, clarity: 10 }),
    null,
  ],
];

for (const t of tasks) {
  insertTask.run(...t);
}

// Optionally seed YAML tasks on top (Phase 2 task corpus)
if (REINIT_TASKS_FLAG) {
  console.log("\n🔄 --reinit-tasks flag detected — seeding YAML Phase 2 tasks…");
  seedYamlTasks();
}

// --full-reinit: nuke everything and reseed
if (FULL_REINIT_FLAG) {
  console.log("\n🔄 --full-reinit flag detected — dropping and recreating all tables…");
  db.exec([
    "DROP TABLE IF EXISTS runs",
    "DROP TABLE IF EXISTS tasks",
    "DROP TABLE IF EXISTS models",
  ].join(";"));
  db.exec(CREATE_TABLES_SQL);
  // Re-insert models
  for (const m of models) { insertModel.run(...m); }
  // Re-insert legacy tasks
  for (const t of tasks) { insertTask.run(...t); }
  // Seed YAML tasks
  seedYamlTasks();
  console.log("✅ Full reinit complete");
}

// Seed runs (2 groups of runs)
const insertRun = db.prepare(`
  INSERT OR REPLACE INTO runs (run_id, model_id, task_id, score, failure_label, transcript, latency_ms, created_at)
  VALUES (?, ?, ?, ?, ?, ?, ?, ?)
`);

const runGroups = [
  {
    run_id: "run_2026-04-07",
    created_at: "2026-04-07T09:00:00+08:00",
    data: [
      ["minimax-m2.7", "coding-loop", 85.5, "PASS", "Transformed lodash methods to native loops...", 2340],
      ["minimax-m2.7", "readme-audit", 72.0, "PASS", "Reviewed and improved README sections...", 1800],
      ["minimax-m2.7", "context-summary", 78.5, "PASS", "Extracted key points and summarized...", 1200],
      ["minimax-m2.7", "json-extract", 92.0, "PASS", "Successfully extracted nested fields...", 800],
      ["minimax-m2.7", "file-search", 88.0, "PASS", "Found all matching files recursively...", 950],
      ["minimax-m2.7", "multi-step-reasoning", 80.0, "PASS", "Solved with step-by-step reasoning...", 3100],
      ["kimi-k2p5", "coding-loop", 88.0, "PASS", "Elegant loop implementations...", 2100],
      ["kimi-k2p5", "readme-audit", 75.5, "PASS", "Thorough README improvements...", 1950],
      ["kimi-k2p5", "context-summary", 82.0, "PASS", "Clear and accurate summary...", 1100],
      ["kimi-k2p5", "json-extract", 95.0, "PASS", "Perfect field extraction...", 750],
      ["kimi-k2p5", "file-search", 85.5, "PASS", "Comprehensive file search...", 880],
      ["kimi-k2p5", "multi-step-reasoning", 83.5, "PASS", "Excellent multi-step logic...", 2900],
      ["gpt-5.4", "coding-loop", 91.0, "PASS", "Optimal native loop solutions...", 2500],
      ["gpt-5.4", "readme-audit", 88.5, "PASS", "Exceptional README enhancement...", 2200],
      ["gpt-5.4", "context-summary", 90.0, "PASS", "Superb summarization quality...", 1400],
      ["gpt-5.4", "json-extract", 97.5, "PASS", "Flawless JSON extraction...", 900],
      ["gpt-5.4", "file-search", 93.0, "PASS", "Fast and complete search...", 1000],
      ["gpt-5.4", "multi-step-reasoning", 89.0, "PASS", "Masterful reasoning chain...", 3400],
    ],
  },
  {
    run_id: "run_2026-04-06",
    created_at: "2026-04-06T10:00:00+08:00",
    data: [
      ["minimax-m2.7", "coding-loop", 82.0, "PASS", "Loop implementation v1...", 2400],
      ["minimax-m2.7", "readme-audit", 70.5, "PASS", "README review...", 1700],
      ["minimax-m2.7", "context-summary", 76.0, "FAIL", "Missing some key points...", 1150],
      ["minimax-m2.7", "json-extract", 90.0, "PASS", "Good extraction...", 820],
      ["minimax-m2.7", "file-search", 86.5, "PASS", "Search completed...", 920],
      ["minimax-m2.7", "multi-step-reasoning", 77.5, "PASS", "Reasoned correctly...", 3000],
      ["kimi-k2p5", "coding-loop", 86.5, "PASS", "Clean loops...", 2200],
      ["kimi-k2p5", "readme-audit", 73.0, "PASS", "Reviewed...", 1850],
      ["kimi-k2p5", "context-summary", 80.0, "PASS", "Good summary...", 1050],
      ["kimi-k2p5", "json-extract", 93.5, "PASS", "Accurate extraction...", 780],
      ["kimi-k2p5", "file-search", 84.0, "PASS", "Search done...", 860],
      ["kimi-k2p5", "multi-step-reasoning", 81.0, "PASS", "Solid reasoning...", 2800],
      ["gpt-5.4", "coding-loop", 89.5, "PASS", "Excellent loops...", 2550],
      ["gpt-5.4", "readme-audit", 86.0, "PASS", "Great review...", 2100],
      ["gpt-5.4", "context-summary", 88.5, "PASS", "Quality summary...", 1350],
      ["gpt-5.4", "json-extract", 96.0, "PASS", "Clean extraction...", 880],
      ["gpt-5.4", "file-search", 91.5, "PASS", "Fast search...", 980],
      ["gpt-5.4", "multi-step-reasoning", 87.0, "PASS", "Strong reasoning...", 3300],
    ],
  },
];

for (const group of runGroups) {
  for (const [model_id, task_id, score, failure_label, transcript, latency_ms] of group.data) {
    insertRun.run(
      group.run_id,
      model_id,
      task_id,
      score,
      failure_label,
      transcript,
      latency_ms,
      group.created_at
    );
  }
}

console.log("✅ Database initialized with seed data:");
const modelCount = (db.prepare("SELECT COUNT(*) as c FROM models").get() as {c:number}).c;
const taskCount = (db.prepare("SELECT COUNT(*) as c FROM tasks").get() as {c:number}).c;
const runCount = (db.prepare("SELECT COUNT(*) as c FROM runs").get() as {c:number}).c;
console.log(`   - Models: ${modelCount}`);
console.log(`   - Tasks: ${taskCount}`);
console.log(`   - Runs: ${runCount}`);

db.close();
