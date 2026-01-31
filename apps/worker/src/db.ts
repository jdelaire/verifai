import { Env } from "./types";

export interface JobRow {
  id: string;
  created_at: string;
  status: "pending" | "processing" | "done" | "failed";
  object_key: string;
  file_hash: string | null;
  error_message: string | null;
  expires_at: string;
  ip_address: string | null;
}

export interface ReportRow {
  job_id: string;
  created_at: string;
  ai_likelihood: number | null;
  confidence: "high" | "medium" | "low" | null;
  verdict_text: string | null;
  evidence_json: string;
  metadata_json: string;
  provenance_json: string;
  limitations_json: string;
}

export async function createJob(
  env: Env,
  id: string,
  objectKey: string,
  ipAddress: string | null,
): Promise<JobRow> {
  const ttlHours = parseInt(env.REPORT_TTL_HOURS || "24", 10);
  const now = new Date();
  const expiresAt = new Date(now.getTime() + ttlHours * 60 * 60 * 1000).toISOString();

  await env.DB.prepare(
    `INSERT INTO jobs (id, object_key, ip_address, expires_at) VALUES (?, ?, ?, ?)`,
  )
    .bind(id, objectKey, ipAddress, expiresAt)
    .run();

  return {
    id,
    created_at: now.toISOString(),
    status: "pending",
    object_key: objectKey,
    file_hash: null,
    error_message: null,
    expires_at: expiresAt,
    ip_address: ipAddress,
  };
}

export async function getJob(env: Env, jobId: string): Promise<JobRow | null> {
  const result = await env.DB.prepare(`SELECT * FROM jobs WHERE id = ?`)
    .bind(jobId)
    .first<JobRow>();
  return result ?? null;
}

export async function updateJobStatus(
  env: Env,
  jobId: string,
  status: JobRow["status"],
  errorMessage?: string,
): Promise<void> {
  if (errorMessage !== undefined) {
    await env.DB.prepare(
      `UPDATE jobs SET status = ?, error_message = ? WHERE id = ?`,
    )
      .bind(status, errorMessage, jobId)
      .run();
  } else {
    await env.DB.prepare(`UPDATE jobs SET status = ? WHERE id = ?`)
      .bind(status, jobId)
      .run();
  }
}

export async function updateJobHash(
  env: Env,
  jobId: string,
  fileHash: string,
): Promise<void> {
  await env.DB.prepare(`UPDATE jobs SET file_hash = ? WHERE id = ?`)
    .bind(fileHash, jobId)
    .run();
}

export async function findJobByHash(
  env: Env,
  fileHash: string,
): Promise<JobRow | null> {
  const result = await env.DB.prepare(
    `SELECT * FROM jobs WHERE file_hash = ? AND status = 'done' AND expires_at > datetime('now') ORDER BY created_at DESC LIMIT 1`,
  )
    .bind(fileHash)
    .first<JobRow>();
  return result ?? null;
}

export async function createReport(
  env: Env,
  report: Omit<ReportRow, "created_at">,
): Promise<void> {
  await env.DB.prepare(
    `INSERT INTO reports (job_id, ai_likelihood, confidence, verdict_text, evidence_json, metadata_json, provenance_json, limitations_json) VALUES (?, ?, ?, ?, ?, ?, ?, ?)`,
  )
    .bind(
      report.job_id,
      report.ai_likelihood,
      report.confidence,
      report.verdict_text,
      report.evidence_json,
      report.metadata_json,
      report.provenance_json,
      report.limitations_json,
    )
    .run();
}

export async function getReportByJobId(
  env: Env,
  jobId: string,
): Promise<ReportRow | null> {
  const result = await env.DB.prepare(
    `SELECT * FROM reports WHERE job_id = ?`,
  )
    .bind(jobId)
    .first<ReportRow>();
  return result ?? null;
}
