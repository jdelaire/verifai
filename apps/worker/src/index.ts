import { Env } from "./types";
import { handleToken, handleUpload, handleFinalize } from "./routes/upload";
import { handleGetReport } from "./routes/report";
import { handleInternalReport } from "./routes/internal";
import { handleQueue } from "./queue";
import { handleScheduled } from "./cron";

// ---------------------------------------------------------------------------
// CORS helpers
// ---------------------------------------------------------------------------

const CORS_HEADERS: Record<string, string> = {
  "Access-Control-Allow-Origin": "*",
  "Access-Control-Allow-Methods": "GET, POST, PUT, DELETE, OPTIONS",
  "Access-Control-Allow-Headers": "Content-Type, Authorization",
};

function withCors(response: Response): Response {
  const headers = new Headers(response.headers);
  for (const [key, value] of Object.entries(CORS_HEADERS)) {
    headers.set(key, value);
  }
  return new Response(response.body, {
    status: response.status,
    statusText: response.statusText,
    headers,
  });
}

function handleOptions(): Response {
  return new Response(null, { status: 204, headers: CORS_HEADERS });
}

// ---------------------------------------------------------------------------
// Simple pathname + method router
// ---------------------------------------------------------------------------

async function handleRequest(request: Request, env: Env): Promise<Response> {
  const url = new URL(request.url);
  const { pathname } = url;
  const method = request.method.toUpperCase();

  // Preflight
  if (method === "OPTIONS") {
    return handleOptions();
  }

  // POST /api/upload/token
  if (method === "POST" && pathname === "/api/upload/token") {
    return withCors(await handleToken(request, env));
  }

  // PUT /api/upload/:jobId (direct upload proxy to R2)
  if (method === "PUT" && pathname.startsWith("/api/upload/")) {
    const jobId = pathname.replace("/api/upload/", "");
    if (jobId && jobId !== "token" && jobId !== "finalize") {
      return withCors(await handleUpload(request, env, jobId));
    }
  }

  // POST /api/upload/finalize
  if (method === "POST" && pathname === "/api/upload/finalize") {
    return withCors(await handleFinalize(request, env));
  }

  // GET /api/report/:jobId
  if (method === "GET" && pathname.startsWith("/api/report/")) {
    const jobId = pathname.replace("/api/report/", "");
    if (!jobId) {
      return withCors(
        new Response(JSON.stringify({ error: "Missing jobId" }), {
          status: 400,
          headers: { "Content-Type": "application/json" },
        }),
      );
    }
    return withCors(await handleGetReport(jobId, env));
  }

  // POST /api/internal/report
  if (method === "POST" && pathname === "/api/internal/report") {
    return withCors(await handleInternalReport(request, env));
  }

  // 404 – no matching route
  return withCors(
    new Response(JSON.stringify({ error: "Not found" }), {
      status: 404,
      headers: { "Content-Type": "application/json" },
    }),
  );
}

// ---------------------------------------------------------------------------
// Worker exports
// ---------------------------------------------------------------------------

export default {
  /**
   * HTTP fetch handler – the primary request entry-point for the worker.
   */
  async fetch(request: Request, env: Env, _ctx: ExecutionContext): Promise<Response> {
    try {
      return await handleRequest(request, env);
    } catch (err) {
      console.error("Unhandled error in fetch handler:", err);
      return withCors(
        new Response(JSON.stringify({ error: "Internal server error" }), {
          status: 500,
          headers: { "Content-Type": "application/json" },
        }),
      );
    }
  },

  /**
   * Queue consumer handler – processes messages from the ANALYSIS_QUEUE.
   */
  async queue(batch: MessageBatch, env: Env): Promise<void> {
    await handleQueue(batch, env);
  },

  /**
   * Cron / scheduled handler – runs on the schedule defined in wrangler.toml.
   */
  async scheduled(controller: ScheduledController, env: Env, ctx: ExecutionContext): Promise<void> {
    ctx.waitUntil(handleScheduled(env));
  },
} satisfies ExportedHandler<Env>;
