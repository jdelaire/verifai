import { Env } from "./types";
import { deleteObject } from "./r2";

export async function handleScheduled(env: Env): Promise<void> {
  // Clean up R2 objects for expired jobs before deleting from D1
  const expiredJobs = await env.DB.prepare(
    `SELECT id, object_key FROM jobs WHERE expires_at < datetime('now')`,
  ).all<{ id: string; object_key: string | null }>();

  for (const job of expiredJobs.results) {
    if (job.object_key) {
      try {
        await deleteObject(env, job.object_key);
      } catch (err) {
        console.error(`Cron: failed to delete R2 object ${job.object_key} for job ${job.id}:`, err);
      }
    }
  }

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
