import { Env } from "../types";
import { getJob, getReportByJobId } from "../db";

function json(data: unknown, status = 200): Response {
  return new Response(JSON.stringify(data), {
    status,
    headers: { "Content-Type": "application/json" },
  });
}

const EMPTY_PROVENANCE = { c2pa_present: false, c2pa_valid: null, notes: [] };
const EMPTY_METADATA = {
  has_exif: false,
  camera_make_model: null,
  software_tag: null,
  width: 0,
  height: 0,
  format: "",
};

export async function handleGetReport(
  jobId: string,
  env: Env,
): Promise<Response> {
  const job = await getJob(env, jobId);
  if (!job) {
    return json({ error: "Report not found or expired." }, 404);
  }

  // Check expiry
  if (new Date(job.expires_at) < new Date()) {
    return json({ error: "Report not found or expired." }, 404);
  }

  // If still processing or pending, return status-only response
  if (job.status === "pending" || job.status === "processing") {
    return json({
      job_id: job.id,
      status: job.status,
      ai_likelihood: null,
      confidence: null,
      verdict_text: null,
      evidence: [],
      provenance: EMPTY_PROVENANCE,
      metadata: EMPTY_METADATA,
      limitations: [],
      expires_at: job.expires_at,
    });
  }

  // If failed, return error info
  if (job.status === "failed") {
    return json({
      job_id: job.id,
      status: "failed",
      ai_likelihood: null,
      confidence: null,
      verdict_text: null,
      evidence: [],
      provenance: EMPTY_PROVENANCE,
      metadata: EMPTY_METADATA,
      limitations: [],
      expires_at: job.expires_at,
      error: job.error_message || "Analysis failed.",
    });
  }

  // Status is "done" — fetch the report
  const report = await getReportByJobId(env, jobId);
  if (!report) {
    return json({ error: "Report data missing." }, 500);
  }

  return json({
    job_id: job.id,
    status: "done",
    ai_likelihood: report.ai_likelihood,
    confidence: report.confidence,
    verdict_text: report.verdict_text,
    evidence: JSON.parse(report.evidence_json),
    provenance: JSON.parse(report.provenance_json),
    metadata: JSON.parse(report.metadata_json),
    limitations: JSON.parse(report.limitations_json),
    expires_at: job.expires_at,
  });
}
