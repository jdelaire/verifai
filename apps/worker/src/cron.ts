import { Env } from "./types";

export async function handleScheduled(env: Env): Promise<void> {
  // Delete expired reports (must happen before jobs due to FK)
  await env.DB.prepare(
    `DELETE FROM reports WHERE job_id IN (SELECT id FROM jobs WHERE expires_at < datetime('now'))`,
  ).run();

  // Delete expired jobs
  const result = await env.DB.prepare(
    `DELETE FROM jobs WHERE expires_at < datetime('now')`,
  ).run();

  console.log(`Cron: cleaned up expired jobs. Rows affected: ${result.meta.changes}`);

  // Clean up old rate limit entries (older than 7 days)
  await env.DB.prepare(
    `DELETE FROM rate_limits WHERE window_date < date('now', '-7 days')`,
  ).run();
}
