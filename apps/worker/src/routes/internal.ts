import { Env } from "../types";
import { getJob, updateJobStatus, createReport } from "../db";
import { deleteObject } from "../r2";

function json(data: unknown, status = 200): Response {
  return new Response(JSON.stringify(data), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

interface InternalReportBody {
  job_id: string;
  status: "done" | "failed";
  error?: string;
  ai_likelihood?: number | null;
  confidence?: string | null;
  verdict_text?: string | null;
  evidence?: string[];
  provenance?: {
    c2pa_present: boolean;
    c2pa_valid: boolean | null;
    notes: string[];
  };
  metadata?: {
    has_exif: boolean;
    camera_make_model: string | null;
    software_tag: string | null;
    width: number;
    height: number;
    format: string;
  };
  limitations?: string[];
}

export async function handleInternalReport(
  request: Request,
  env: Env,
): Promise<Response> {
  // Authenticate via shared secret
  const authHeader = request.headers.get("Authorization") || "";
  const token = authHeader.replace("Bearer ", "");
  if (!token || token !== env.INFERENCE_SHARED_SECRET) {
    return json({ error: "Unauthorized" }, 401);
  }

  const body = await request.json<InternalReportBody>();

  if (!body.job_id) {
    return json({ error: "Missing job_id." }, 400);
  }

  const job = await getJob(env, body.job_id);
  if (!job) {
    return json({ error: "Job not found." }, 404);
  }

  if (body.status === "failed") {
    await updateJobStatus(env, body.job_id, "failed", body.error || "Analysis failed");
    // Clean up the original image
    await deleteObject(env, job.object_key);
    return json({ ok: true });
  }

  // Write report to D1
  await createReport(env, {
    job_id: body.job_id,
    ai_likelihood: body.ai_likelihood ?? null,
    confidence: (body.confidence as "high" | "medium" | "low") ?? null,
    verdict_text: body.verdict_text ?? null,
    evidence_json: JSON.stringify(body.evidence ?? []),
    metadata_json: JSON.stringify(body.metadata ?? {}),
    provenance_json: JSON.stringify(body.provenance ?? {}),
    limitations_json: JSON.stringify(body.limitations ?? []),
  });

  // Update job status to done
  await updateJobStatus(env, body.job_id, "done");

  // Delete original image from R2
  await deleteObject(env, job.object_key);

  return json({ ok: true });
}
