import { Env } from "./types";
import { updateJobStatus } from "./db";
import { getObject } from "./r2";

interface QueueMessage {
  job_id: string;
  object_key: string;
}

export async function handleQueue(
  batch: MessageBatch,
  env: Env,
): Promise<void> {
  for (const message of batch.messages) {
    const msg = message.body as QueueMessage;
    try {
      // Generate a temporary URL for the inference service to download the image.
      // Since we can't create pre-signed R2 URLs from Workers, we'll pass the
      // image bytes directly via a POST to the inference service.
      // Alternative: the inference service calls back to a Worker endpoint to get the image.
      // For simplicity in MVP, we fetch from R2 and forward to inference.

      const obj = await getObject(env, msg.object_key);
      if (!obj) {
        await updateJobStatus(env, msg.job_id, "failed", "Image not found in storage");
        message.ack();
        continue;
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
          job_id: msg.job_id,
          object_key: msg.object_key,
          image_url: `data:application/octet-stream;base64,${arrayBufferToBase64(imageBytes)}`,
          callback_url: callbackUrl,
        }),
      });

      if (!response.ok) {
        const errText = await response.text();
        console.error(`Inference service error for job ${msg.job_id}: ${errText}`);
        message.retry();
        continue;
      }

      message.ack();
    } catch (err) {
      console.error(`Queue processing error for job ${msg.job_id}:`, err);
      message.retry();
    }
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
