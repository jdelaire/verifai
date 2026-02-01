/**
 * Cloudflare Worker environment bindings for the VerifAI worker.
 *
 * Each field maps to a binding declared in wrangler.toml or set as a secret.
 */
export interface Env {
  /** Cloudflare D1 database for jobs, reports, and rate-limit tracking. */
  DB: D1Database;

  /** Cloudflare R2 bucket for uploaded image / document storage. */
  BUCKET: R2Bucket;

  /** Base URL of the external inference micro-service. */
  INFERENCE_SERVICE_URL: string;

  /** Base URL of this Worker, used for inference callback. */
  WORKER_URL: string;

  /** Shared HMAC secret used to authenticate calls to / from the inference service. */
  INFERENCE_SHARED_SECRET: string;

  /** How many hours a report should remain accessible before automatic cleanup. */
  REPORT_TTL_HOURS: string;
}
