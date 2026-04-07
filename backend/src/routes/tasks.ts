import { Hono } from "hono";
import { db } from "../db/index.js";

const app = new Hono();

app.get("/", (c) => {
  const rows = db.prepare("SELECT * FROM tasks WHERE is_active = 1").all() as any[];
  const tasks = rows.map((r) => ({
    ...r,
    tags: JSON.parse(r.tags || "[]"),
    scoring_rules: JSON.parse(r.scoring_rules || "[]"),
  }));
  return c.json({ tasks });
});

app.get("/:taskId", (c) => {
  const taskId = c.req.param("taskId");
  const row = db.prepare("SELECT * FROM tasks WHERE task_id = ?").get(taskId) as any;
  if (!row) return c.json({ error: "Task not found" }, 404);
  return c.json({
    task: {
      ...row,
      tags: JSON.parse(row.tags || "[]"),
      scoring_rules: JSON.parse(row.scoring_rules || "[]"),
    },
  });
});

export default app;
