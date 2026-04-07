import Database from "better-sqlite3";
import { CREATE_TABLES_SQL } from "./schema.js";
import path from "path";
import { fileURLToPath } from "url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const DB_PATH = path.join(__dirname, "..", "..", "arena.db");

const db = new Database(DB_PATH);
db.pragma("journal_mode = WAL");
db.exec(CREATE_TABLES_SQL);

console.log("✅ Database schema initialized");
const nAgents = (db.prepare("SELECT COUNT(*) as c FROM agents").get() as any).c;
const nTasks = (db.prepare("SELECT COUNT(*) as c FROM tasks").get() as any).c;
const nRuns = (db.prepare("SELECT COUNT(*) as c FROM runs").get() as any).c;
console.log(`   agents: ${nAgents}`);
console.log(`   tasks:  ${nTasks}`);
console.log(`   runs:   ${nRuns}`);

db.close();
