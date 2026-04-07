import { Hono } from "hono";
import { db } from "../db/index.js";

const app = new Hono();

app.get("/", (c) => {
  const runGroup = c.req.query("run_group");
  const agentId = c.req.query("agent_id");
  const taskId = c.req.query("task_id");
  const limit = Math.min(parseInt(c.req.query("limit") || "50"), 200);

  let sql = "SELECT * FROM runs WHERE 1=1";
  const params: any[] = [];

  if (runGroup) {
    sql += " AND run_group = ?";
    params.push(runGroup);
  }
  if (agentId) {
    sql += " AND agent_id = ?";
    params.push(agentId);
  }
  if (taskId) {
    sql += " AND task_id = ?";
    params.push(taskId);
  }

  sql += " ORDER BY created_at DESC LIMIT ?";
  params.push(limit);

  const rows = db.prepare(sql).all(...params) as any[];
  const results = rows.map((r) => ({
    ...r,
    events: JSON.parse(r.events || "[]"),
  }));
  return c.json({ results });
});

app.get("/:runId/:agentId/:taskId", (c) => {
  const { runId, agentId, taskId } = c.req.param();
  const row = db.prepare(
    "SELECT * FROM runs WHERE run_id = ? AND agent_id = ? AND task_id = ?"
  ).get(runId, agentId, taskId) as any;
  if (!row) return c.json({ error: "Result not found" }, 404);
  return c.json({
    result: {
      ...row,
      events: JSON.parse(row.events || "[]"),
    },
  });
});

export default app;
