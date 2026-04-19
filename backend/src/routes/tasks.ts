import { Hono } from "hono";
import { db } from "../db/index.js";

const app = new Hono();

app.get("/", (c) => {
  const rows = db.prepare("SELECT * FROM tasks").all() as any[];
  const tasks = rows.map((r) => ({
    ...r,
    scoring_criteria: JSON.parse(r.scoring_criteria),
  }));
  return c.json({ tasks });
});

export default app;
