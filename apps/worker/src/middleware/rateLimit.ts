import { Env } from "../types";

const DAILY_LIMIT = 50;
const BURST_SECONDS = 10;

function json(data: unknown, status = 200, headers: Record<string, string> = {}): Response {
  return new Response(JSON.stringify(data), {
    status,
    headers: { "Content-Type": "application/json", ...headers },
  });
}

export async function checkRateLimit(
  request: Request,
  env: Env,
): Promise<Response | null> {
  const ip =
    request.headers.get("CF-Connecting-IP") ||
    request.headers.get("x-forwarded-for") ||
    "unknown";

  const now = new Date();
  const windowDate = now.toISOString().slice(0, 10); // YYYY-MM-DD (UTC)

  const row = await env.DB.prepare(
    `SELECT request_count, last_request_at FROM rate_limits WHERE ip_address = ? AND window_date = ?`,
  )
    .bind(ip, windowDate)
    .first<{ request_count: number; last_request_at: string }>();

  if (row) {
    // Check daily limit
    if (row.request_count >= DAILY_LIMIT) {
      const midnight = new Date(windowDate + "T00:00:00Z");
      midnight.setUTCDate(midnight.getUTCDate() + 1);
      const retryAfter = Math.ceil((midnight.getTime() - now.getTime()) / 1000);
      return json(
        { error: "Rate limit exceeded. Try again later." },
        429,
        {
          "Retry-After": String(retryAfter),
          "X-RateLimit-Limit": String(DAILY_LIMIT),
          "X-RateLimit-Remaining": "0",
          "X-RateLimit-Reset": String(Math.floor(midnight.getTime() / 1000)),
        },
      );
    }

    // Check burst limit
    const lastRequest = new Date(row.last_request_at);
    const elapsed = (now.getTime() - lastRequest.getTime()) / 1000;
    if (elapsed < BURST_SECONDS) {
      const retryAfter = Math.ceil(BURST_SECONDS - elapsed);
      return json(
        { error: "Too many requests. Please wait before trying again." },
        429,
        {
          "Retry-After": String(retryAfter),
          "X-RateLimit-Limit": String(DAILY_LIMIT),
          "X-RateLimit-Remaining": String(DAILY_LIMIT - row.request_count),
          "X-RateLimit-Reset": String(Math.floor(now.getTime() / 1000) + retryAfter),
        },
      );
    }

    // Increment
    await env.DB.prepare(
      `UPDATE rate_limits SET request_count = request_count + 1, last_request_at = ? WHERE ip_address = ? AND window_date = ?`,
    )
      .bind(now.toISOString(), ip, windowDate)
      .run();
  } else {
    // First request today
    await env.DB.prepare(
      `INSERT INTO rate_limits (ip_address, window_date, request_count, last_request_at) VALUES (?, ?, 1, ?)`,
    )
      .bind(ip, windowDate, now.toISOString())
      .run();
  }

  // Not rate-limited
  return null;
}
