import { Hono } from "hono";
import { db } from "../db/index.js";

const app = new Hono();

app.get("/", (c) => {
  const rows = db.prepare("SELECT * FROM models").all() as any[];
  const models = rows.map((r) => ({
    ...r,
    is_codex_harness: r.is_codex_harness === 1,
  }));
  return c.json({ models });
});

export default app;
