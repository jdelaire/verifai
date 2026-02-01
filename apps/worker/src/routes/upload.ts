import { Env } from "../types";
import { createJob, getJob, updateJobStatus, updateJobHash, findJobByHash } from "../db";
import { putObject, headObject, getObject, deleteObject } from "../r2";
import { checkRateLimit } from "../middleware/rateLimit";
import { dispatchAnalysis } from "../inference";

const ACCEPTED_TYPES = new Set([
  "image/jpeg",
  "image/png",
  "image/webp",
  "image/tiff",
]);
const MAX_FILE_SIZE = 5 * 1024 * 1024; // 5 MB

function json(data: unknown, status = 200): Response {
  return new Response(JSON.stringify(data), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

/**
 * POST /api/upload/token
 * Validates the request, creates a job, and returns the job_id.
 * The client then uploads via PUT /api/upload/:jobId.
 */
export async function handleToken(
  request: Request,
  env: Env,
): Promise<Response> {
  // Rate limit check
  const limited = await checkRateLimit(request, env);
  if (limited) return limited;

  const body = await request.json<{ content_type?: string; file_size?: number }>();
  const contentType = body.content_type;
  const fileSize = body.file_size;

  if (!contentType || !ACCEPTED_TYPES.has(contentType)) {
    return json(
      { error: `Invalid content type. Accepted: ${[...ACCEPTED_TYPES].join(", ")}` },
      400,
    );
  }
  if (typeof fileSize !== "number" || fileSize <= 0 || fileSize > MAX_FILE_SIZE) {
    return json(
      { error: `File size must be between 1 byte and ${MAX_FILE_SIZE} bytes (5 MB).` },
      400,
    );
  }

  const jobId = crypto.randomUUID();
  const objectKey = `uploads/${jobId}`;
  const ip = request.headers.get("CF-Connecting-IP") || request.headers.get("x-forwarded-for") || null;

  await createJob(env, jobId, objectKey, ip);

  return json({
    job_id: jobId,
    upload_url: `/api/upload/${jobId}`,
    expires_in: 300,
  });
}

/**
 * PUT /api/upload/:jobId
 * Client uploads the raw image body here. Worker proxies it to R2.
 */
export async function handleUpload(
  request: Request,
  env: Env,
  jobId: string,
): Promise<Response> {
  const job = await getJob(env, jobId);
  if (!job || job.status !== "pending") {
    return json({ error: "Invalid or expired upload token." }, 404);
  }

  const contentType = request.headers.get("content-type") || "application/octet-stream";
  if (!ACCEPTED_TYPES.has(contentType)) {
    return json({ error: "Invalid content type." }, 400);
  }

  const contentLength = parseInt(request.headers.get("content-length") || "0", 10);
  if (contentLength > MAX_FILE_SIZE) {
    return json({ error: "File too large." }, 413);
  }

  if (!request.body) {
    return json({ error: "Empty body." }, 400);
  }

  await putObject(env, job.object_key, request.body, contentType);

  return json({ ok: true });
}

/**
 * POST /api/upload/finalize
 * Validates the upload exists, computes hash, checks for cache hit,
 * and enqueues the analysis job.
 */
export async function handleFinalize(
  request: Request,
  env: Env,
  ctx: ExecutionContext,
): Promise<Response> {
  const body = await request.json<{ job_id?: string }>();
  const jobId = body.job_id;

  if (!jobId) {
    return json({ error: "Missing job_id." }, 400);
  }

  const job = await getJob(env, jobId);
  if (!job || job.status !== "pending") {
    return json({ error: "Job not found or not in pending state." }, 404);
  }

  // Verify object exists in R2
  const head = await headObject(env, job.object_key);
  if (!head) {
    return json({ error: "Upload not found. Please upload the file first." }, 400);
  }

  // Compute file hash for deduplication
  const obj = await getObject(env, job.object_key);
  if (!obj) {
    return json({ error: "Upload not found." }, 400);
  }
  const arrayBuffer = await obj.arrayBuffer();
  const hashBuffer = await crypto.subtle.digest("SHA-256", arrayBuffer);
  const hashArray = Array.from(new Uint8Array(hashBuffer));
  const fileHash = hashArray.map((b) => b.toString(16).padStart(2, "0")).join("");

  await updateJobHash(env, jobId, fileHash);

  // Check for cache hit
  const existing = await findJobByHash(env, fileHash);
  if (existing && existing.id !== jobId) {
    // Cache hit — delete the duplicate upload and return existing job
    await deleteObject(env, job.object_key);
    await updateJobStatus(env, jobId, "done");
    return json({
      job_id: existing.id,
      status: "done",
      cached: true,
    });
  }

  // Dispatch analysis in the background
  await updateJobStatus(env, jobId, "processing");
  ctx.waitUntil(dispatchAnalysis(env, jobId, job.object_key));

  return json({
    job_id: jobId,
    status: "processing",
  });
}
