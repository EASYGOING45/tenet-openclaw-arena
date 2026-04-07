import { Hono } from "hono";
import { db } from "../db/index.js";
import type { LeaderboardEntry } from "../types.js";

const app = new Hono();

app.get("/", (c) => {
  const runGroup = c.req.query("run_group");
  const capability = c.req.query("capability");

  // Base WHERE clause
  let whereClause = "WHERE 1=1";
  const params: any[] = [];
  if (runGroup) {
    whereClause += " AND r.run_group = ?";
    params.push(runGroup);
  }

  // Get all agents
  const agents = db.prepare(
    "SELECT * FROM agents WHERE is_active = 1"
  ).all() as any[];
  const agentMap: Record<string, any> = {};
  for (const a of agents) agentMap[a.agent_id] = a;

  // Average score per agent
  let avgSql = `
    SELECT r.agent_id, AVG(r.score) as score
    FROM runs r
    ${whereClause}
    GROUP BY r.agent_id
  `;
  if (capability) {
    avgSql = `
      SELECT r.agent_id, AVG(r.score) as score
      FROM runs r
      JOIN tasks t ON r.task_id = t.task_id
      ${whereClause} AND t.capability = ?
      GROUP BY r.agent_id
    `;
    params.push(capability);
  }

  const avgScores = db.prepare(avgSql).all(...params) as any[];
  const scores = avgScores.map((s) => s.score as number);
  scores.sort((a, b) => b - a);
  const median = scores.length % 2 === 0
    ? (scores[scores.length / 2 - 1] + scores[scores.length / 2]) / 2
    : scores[Math.floor(scores.length / 2)];

  // PASS count per agent
  let passSql = `
    SELECT agent_id, COUNT(*) as vote_count
    FROM runs
    WHERE verdict = 'PASS'
    ${runGroup ? " AND run_group = ?" : ""}
    GROUP BY agent_id
  `;
  const passParams = runGroup ? [runGroup] : [];
  const passCounts = db.prepare(passSql).all(...passParams) as any[];
  const passMap: Record<string, number> = {};
  for (const p of passCounts) passMap[p.agent_id] = p.vote_count;

  // Task-level scores per agent
  let taskSql = `
    SELECT r.agent_id, r.task_id, t.title, t.capability, AVG(r.score) as score, MAX(r.verdict) as verdict
    FROM runs r
    JOIN tasks t ON r.task_id = t.task_id
    ${whereClause}
    GROUP BY r.agent_id, r.task_id
  `;
  if (capability) {
    taskSql = `
      SELECT r.agent_id, r.task_id, t.title, t.capability, AVG(r.score) as score, MAX(r.verdict) as verdict
      FROM runs r
      JOIN tasks t ON r.task_id = t.task_id
      ${whereClause} AND t.capability = ?
      GROUP BY r.agent_id, r.task_id
    `;
  }

  const taskDetails = db.prepare(taskSql).all(...params) as any[];
  const taskMap: Record<string, any[]> = {};
  for (const t of taskDetails) {
    if (!taskMap[t.agent_id]) taskMap[t.agent_id] = [];
    taskMap[t.agent_id].push({
      task_id: t.task_id,
      title: t.title,
      capability: t.capability,
      score: Math.round(t.score * 100) / 100,
      verdict: t.verdict,
    });
  }

  const leaderboard: LeaderboardEntry[] = avgScores
    .sort((a, b) => (b.score as number) - (a.score as number))
    .map((row, idx) => {
      const rank = idx + 1;
      const score = row.score as number;
      let above = 0, below = 0;
      for (const s of scores) {
        if (s > score) above++;
        if (s < score) below++;
      }

      const agent = agentMap[row.agent_id];
      return {
        rank,
        agent_id: row.agent_id,
        model_id: agent?.model_id ?? row.agent_id,
        model_name: agent?.model_name ?? row.agent_id,
        provider: agent?.provider ?? "unknown",
        license_type: agent?.license_type ?? "unknown",
        score: Math.round(score * 100) / 100,
        vote_count: passMap[row.agent_id] || 0,
        rank_spread: `+${above}/-${below}`,
        input_price: agent?.input_price ?? null,
        output_price: agent?.output_price ?? null,
        context_length: agent?.context_length ?? null,
        tasks: (taskMap[row.agent_id] || []).map((t) => ({
          task_id: t.task_id,
          title: t.title,
          capability: t.capability,
          score: t.score,
          verdict: t.verdict,
        })),
      };
    });

  return c.json({ leaderboard });
});

export default app;
