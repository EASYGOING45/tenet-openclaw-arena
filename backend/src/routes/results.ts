import { Hono } from "hono";
import { db } from "../db/index.js";

const app = new Hono();

app.get("/", (c) => {
  const runId = c.req.query("run_id");
  const modelId = c.req.query("model_id");
  const taskId = c.req.query("task_id");
  const limit = Math.min(parseInt(c.req.query("limit") || "50"), 200);

  let sql = "SELECT * FROM runs WHERE 1=1";
  const params: any[] = [];

  if (runId) {
    sql += " AND run_id = ?";
    params.push(runId);
  }
  if (modelId) {
    sql += " AND model_id = ?";
    params.push(modelId);
  }
  if (taskId) {
    sql += " AND task_id = ?";
    params.push(taskId);
  }

  sql += ` ORDER BY created_at DESC LIMIT ?`;
  params.push(limit);

  const results = db.prepare(sql).all(...params);
  return c.json({ results });
});

app.get("/:runId", (c) => {
  const runId = c.req.param("runId");
  const results = db.prepare("SELECT * FROM runs WHERE run_id = ?").all(runId);
  return c.json({ results });
});

export default app;
