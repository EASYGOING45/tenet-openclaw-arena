import { Hono } from "hono";
import { db } from "../db/index.js";

const app = new Hono();

app.get("/", (c) => {
  const rows = db.prepare("SELECT * FROM tasks").all() as any[];
  const tasks = rows.map((r) => {
    let scoring_criteria = null;
    try {
      scoring_criteria = r.scoring_criteria && r.scoring_criteria !== "undefined"
        ? JSON.parse(r.scoring_criteria)
        : null;
    } catch {
      scoring_criteria = null;
    }
    return {
      id: r.id,
      name: r.name,
      category: r.category,   // = capability/dimension for YAML tasks
      difficulty: r.difficulty,
      description: r.description,
      scoring_criteria,
      capability: r.capability ?? r.category, // fallback to category
    };
  });
  return c.json({ tasks });
});

export default app;
