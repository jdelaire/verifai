export interface Provenance {
  c2pa_present: boolean;
  c2pa_valid: boolean | null;
  notes: string[];
}

export interface ImageMetadata {
  has_exif: boolean;
  camera_make_model: string | null;
  software_tag: string | null;
  width: number;
  height: number;
  format: string;
}

export type JobStatus = "pending" | "processing" | "done" | "failed";
export type ConfidenceTier = "high" | "medium" | "low";

export interface Report {
  job_id: string;
  status: JobStatus;
  ai_likelihood: number | null;
  confidence: ConfidenceTier | null;
  verdict_text: string | null;
  evidence: string[];
  provenance: Provenance;
  metadata: ImageMetadata;
  limitations: string[];
  expires_at: string;
}

export interface UploadTokenRequest {
  content_type: string;
  file_size: number;
}

export interface UploadTokenResponse {
  job_id: string;
  upload_url: string;
  expires_in: number;
}

export interface FinalizeRequest {
  job_id: string;
}

export interface FinalizeResponse {
  job_id: string;
  status: JobStatus;
  cached?: boolean;
}

export const ACCEPTED_CONTENT_TYPES = [
  "image/jpeg",
  "image/png",
  "image/webp",
  "image/tiff",
] as const;

export const MAX_FILE_SIZE = 5 * 1024 * 1024; // 5 MB
export const MAX_IMAGE_DIMENSION = 4096;
