import { Env } from "./types";
import { updateJobStatus } from "./db";
import { getObject } from "./r2";

/**
 * Dispatch an analysis job directly to the inference service.
 * Called via ctx.waitUntil() so it runs in the background after
 * the finalize response has been sent to the client.
 */
export async function dispatchAnalysis(
  env: Env,
  jobId: string,
  objectKey: string,
): Promise<void> {
  try {
    const obj = await getObject(env, objectKey);
    if (!obj) {
      await updateJobStatus(env, jobId, "failed", "Image not found in storage");
      return;
    }

    const imageBytes = await obj.arrayBuffer();

    const workerBaseUrl = env.WORKER_URL || "http://localhost:8787";
    const callbackUrl = `${workerBaseUrl}/api/internal/report`;
    const inferenceUrl = `${env.INFERENCE_SERVICE_URL || "http://localhost:8001"}/analyze`;

    const response = await fetch(inferenceUrl, {
      method: "POST",
      headers: {
        "Content-Type": "application/json",
        Authorization: `Bearer ${env.INFERENCE_SHARED_SECRET}`,
      },
      body: JSON.stringify({
        job_id: jobId,
        object_key: objectKey,
        image_url: `data:application/octet-stream;base64,${arrayBufferToBase64(imageBytes)}`,
        callback_url: callbackUrl,
      }),
    });

    if (!response.ok) {
      const errText = await response.text();
      console.error(`Inference service error for job ${jobId}: ${errText}`);
      await updateJobStatus(env, jobId, "failed", `Inference error: ${response.status}`);
    }
  } catch (err) {
    console.error(`Failed to dispatch analysis for job ${jobId}:`, err);
    await updateJobStatus(env, jobId, "failed", "Failed to reach inference service");
  }
}

function arrayBufferToBase64(buffer: ArrayBuffer): string {
  const bytes = new Uint8Array(buffer);
  let binary = "";
  for (let i = 0; i < bytes.byteLength; i++) {
    binary += String.fromCharCode(bytes[i]);
  }
  return btoa(binary);
}
