import { Hono } from "hono";
import { db } from "../db/index.js";

const app = new Hono();

app.get("/", (c) => {
  const rows = db.prepare("SELECT * FROM agents WHERE is_active = 1").all() as any[];
  return c.json({
    agents: rows.map((r) => ({
      ...r,
      is_active: r.is_active === 1,
    })),
  });
});

export default app;
