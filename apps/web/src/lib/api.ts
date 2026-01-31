import type { Report } from "@verifai/shared/src/types";

const BASE = "/api";

export interface UploadTokenResult {
  job_id: string;
  upload_url: string;
  expires_in: number;
}

export interface FinalizeResult {
  job_id: string;
  status: string;
  cached?: boolean;
}

export async function requestUploadToken(
  contentType: string,
  fileSize: number,
): Promise<UploadTokenResult> {
  const res = await fetch(`${BASE}/upload/token`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ content_type: contentType, file_size: fileSize }),
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error((body as { error?: string }).error || `Request failed: ${res.status}`);
  }
  return res.json();
}

export async function uploadFile(
  uploadUrl: string,
  file: File,
): Promise<void> {
  const res = await fetch(uploadUrl, {
    method: "PUT",
    headers: { "Content-Type": file.type },
    body: file,
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error((body as { error?: string }).error || `Upload failed: ${res.status}`);
  }
}

export async function finalizeUpload(jobId: string): Promise<FinalizeResult> {
  const res = await fetch(`${BASE}/upload/finalize`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ job_id: jobId }),
  });
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error((body as { error?: string }).error || `Finalize failed: ${res.status}`);
  }
  return res.json();
}

export async function getReport(jobId: string): Promise<Report> {
  const res = await fetch(`${BASE}/report/${jobId}`);
  if (!res.ok) {
    const body = await res.json().catch(() => ({}));
    throw new Error((body as { error?: string }).error || `Get report failed: ${res.status}`);
  }
  return res.json();
}
