import { ENV } from "@core/config/env";
import { log } from "@core/logger";
import type { HttpMethod, HttpRequestConfig } from "./types";
import { ApiError } from "./errors";

const REDACTED_HEADERS = new Set([
  "authorization",
  "cookie",
  "set-cookie",
  "x-session-token",
  "x-csrftoken",
]);

const MAX_LOG_CHARS = 4000;
const MAX_STRING_CHARS = 500;
const MAX_ARRAY_ITEMS = 20;
const MAX_OBJECT_KEYS = 30;
const MAX_DEPTH = 6;

function sanitizeHeaders(headers: Headers): Record<string, string> {
  const result: Record<string, string> = {};

  headers.forEach((value, key) => {
    result[key] = REDACTED_HEADERS.has(key.toLowerCase())
      ? "[REDACTED]"
      : value;
  });

  return result;
}

function truncateText(value: string, maxLength = MAX_STRING_CHARS): string {
  return value.length > maxLength
    ? `${value.slice(0, maxLength)}...[truncated:${value.length}]`
    : value;
}

function compactArrayForLog(
  value: unknown[],
  depth: number,
): unknown[] | object {
  if (value.length <= MAX_ARRAY_ITEMS) {
    return value.map((item) => compactForLog(item, depth + 1));
  }

  return {
    __type: "array",
    length: value.length,
    items: value
      .slice(0, MAX_ARRAY_ITEMS)
      .map((item) => compactForLog(item, depth + 1)),
    truncated: value.length - MAX_ARRAY_ITEMS,
  };
}

function compactObjectForLog(
  value: Record<string, unknown>,
  depth: number,
): Record<string, unknown> {
  const entries = Object.entries(value);
  const visibleEntries = entries.slice(0, MAX_OBJECT_KEYS);

  return visibleEntries.reduce<Record<string, unknown>>(
    (result, [key, item]) => {
      result[key] = compactForLog(item, depth + 1);
      return result;
    },
    {
      ...(entries.length > MAX_OBJECT_KEYS
        ? { __truncatedKeys: entries.length - MAX_OBJECT_KEYS }
        : {}),
    },
  );
}

function compactForLog(value: unknown, depth = 0): unknown {
  if (value === undefined || value === null) {
    return value;
  }

  if (typeof value === "string") {
    return truncateText(value);
  }

  if (typeof value === "number" || typeof value === "boolean") {
    return value;
  }

  if (typeof value === "bigint") {
    return value.toString();
  }

  if (typeof value === "function" || typeof value === "symbol") {
    return `[${typeof value}]`;
  }

  if (depth >= MAX_DEPTH) {
    return "[MaxDepth]";
  }

  if (Array.isArray(value)) {
    return compactArrayForLog(value, depth);
  }

  if (value instanceof Date) {
    return value.toISOString();
  }

  try {
    return compactObjectForLog(value as Record<string, unknown>, depth);
  } catch {
    return "[UNSERIALIZABLE]";
  }
}

function serializeForLog(value: unknown): string {
  try {
    const serialized = JSON.stringify(compactForLog(value), null, 2);

    return serialized.length > MAX_LOG_CHARS
      ? `${serialized.slice(0, MAX_LOG_CHARS)}\n...[truncated:${serialized.length}]`
      : serialized;
  } catch {
    return "[UNSERIALIZABLE]";
  }
}

export function getDurationMs(startTime: number): number {
  return Math.round(performance.now() - startTime);
}

export function logRequest(
  config: HttpRequestConfig,
  method: HttpMethod,
  url: string,
  headers: Headers,
): void {
  if (!ENV.IS_DEV) {
    return;
  }

  log.info(
    "[HTTP Request]",
    serializeForLog({
      method,
      url,
      params: config.params,
      headers: sanitizeHeaders(headers),
      data: compactForLog(config.data),
    }),
  );
}

export function logResponse(
  url: string,
  status: number,
  durationMs: number,
  data: unknown,
): void {
  if (!ENV.IS_DEV) {
    return;
  }

  log.info(
    "[HTTP Response]",
    serializeForLog({
      url,
      status,
      durationMs,
      data: compactForLog(data),
    }),
  );
}

export function logError(
  url: string,
  method: HttpMethod,
  durationMs: number,
  error: unknown,
): void {
  if (!ENV.IS_DEV) {
    return;
  }

  if (error instanceof ApiError) {
    log.error(
      "[HTTP Error]",
      serializeForLog({
        method,
        url,
        durationMs,
        status: error.response.status,
        data: compactForLog(error.response.data),
      }),
    );

    return;
  }

  log.warn(
    "[HTTP Transport Error]",
    serializeForLog({
      method,
      url,
      durationMs,
      message: error instanceof Error ? error.message : "Unknown error",
    }),
  );
}
