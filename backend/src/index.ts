import { Hono } from "hono";
import { serve } from "@hono/node-server";
import modelsRoute from "./routes/models.js";
import tasksRoute from "./routes/tasks.js";
import resultsRoute from "./routes/results.js";
import leaderboardRoute from "./routes/leaderboard.js";

const app = new Hono();

app.route("/api/models", modelsRoute);
app.route("/api/tasks", tasksRoute);
app.route("/api/results", resultsRoute);
app.route("/api/leaderboard", leaderboardRoute);

app.get("/health", (c) => c.json({ status: "ok" }));

console.log("🚀 Starting server on http://0.0.0.0:3000");
serve({ fetch: app.fetch, port: 3000 });
