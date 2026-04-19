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
      ...r,
      scoring_criteria,
    };
  });
  return c.json({ tasks });
});

export default app;
