import { Env } from "./types";

export async function putObject(
  env: Env,
  key: string,
  body: ReadableStream | ArrayBuffer,
  contentType: string,
): Promise<void> {
  await env.BUCKET.put(key, body, {
    httpMetadata: { contentType },
  });
}

export async function getObject(
  env: Env,
  key: string,
): Promise<R2ObjectBody | null> {
  return await env.BUCKET.get(key);
}

export async function headObject(
  env: Env,
  key: string,
): Promise<R2Object | null> {
  return await env.BUCKET.head(key);
}

export async function deleteObject(env: Env, key: string): Promise<void> {
  await env.BUCKET.delete(key);
}
