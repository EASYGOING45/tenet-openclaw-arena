import { Hono } from "hono";
import { db } from "../db/index.js";
import type { LeaderboardEntry } from "../types.js";

const app = new Hono();

app.get("/", (c) => {
  // Get average score per model across all runs and tasks
  const avgScores = db
    .prepare(
      `
    SELECT
      r.model_id,
      m.name as model_name,
      m.provider,
      m.license_type,
      m.input_price,
      m.output_price,
      m.context_length,
      AVG(r.score) as score
    FROM runs r
    JOIN models m ON r.model_id = m.id
    GROUP BY r.model_id
    ORDER BY score DESC
  `
    )
    .all() as any[];

  // Get vote_count (number of PASS results per model)
  const voteCounts = db
    .prepare(
      `
    SELECT model_id, COUNT(*) as vote_count
    FROM runs
    WHERE failure_label = 'PASS'
    GROUP BY model_id
  `
    )
    .all() as any[];
  const voteCountMap: Record<string, number> = {};
  for (const v of voteCounts) voteCountMap[v.model_id] = v.vote_count;

  // Get rank_spread: "+X/-Y" = number of runs above/below median
  const scores = avgScores.map((s) => s.score);
  const median = scores.length % 2 === 0
    ? (scores[scores.length / 2 - 1] + scores[scores.length / 2]) / 2
    : scores[Math.floor(scores.length / 2)];

  // Get task-level details per model
  const taskDetails = db
    .prepare(
      `
    SELECT model_id, task_id, AVG(score) as score, MAX(failure_label) as failure_label
    FROM runs
    GROUP BY model_id, task_id
  `
    )
    .all() as any[];
  const taskMap: Record<string, any[]> = {};
  for (const t of taskDetails) {
    if (!taskMap[t.model_id]) taskMap[t.model_id] = [];
    taskMap[t.model_id].push({ task_id: t.task_id, score: t.score, failure_label: t.failure_label });
  }

  const leaderboard: LeaderboardEntry[] = avgScores.map((row, idx) => {
    const rank = idx + 1;
    const score = row.score as number;
    let above = 0;
    let below = 0;
    for (const s of scores) {
      if (s > score) above++;
      if (s < score) below++;
    }
    const spread = `+${above}/-${below}`;

    return {
      rank,
      model_id: row.model_id,
      model_name: row.model_name,
      provider: row.provider,
      license_type: row.license_type,
      score: Math.round(score * 100) / 100,
      vote_count: voteCountMap[row.model_id] || 0,
      rank_spread: spread,
      input_price: row.input_price,
      output_price: row.output_price,
      context_length: row.context_length,
      tasks: (taskMap[row.model_id] || []).map((t) => ({
        task_id: t.task_id,
        score: Math.round(t.score * 100) / 100,
        failure_label: t.failure_label,
      })),
    };
  });

  return c.json({ leaderboard });
});

export default app;
