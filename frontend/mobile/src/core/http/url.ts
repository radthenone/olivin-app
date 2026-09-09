import { ENV } from "@core/config/env";
import { type HttpRequestConfig, type Primitive } from "./types";

function isPlainObject(value: unknown): value is Record<string, Primitive> {
  if (value === null || typeof value !== "object") {
    return false;
  }

  const prototype = Object.getPrototypeOf(value);

  return prototype === Object.prototype || prototype === null;
}

export function buildUrl(config: HttpRequestConfig): string {
  const url = new URL(config.url, ENV.API_BASE_URL);

  for (const [key, value] of Object.entries(config.params ?? {})) {
    if (value === undefined || value === null) {
      continue;
    }

    if (Array.isArray(value)) {
      for (const item of value) {
        if (item !== undefined && item !== null) {
          url.searchParams.append(key, String(item));
        }
      }

      continue;
    }

    if (isPlainObject(value)) {
      url.searchParams.set(key, JSON.stringify(value));
      continue;
    }

    url.searchParams.set(key, String(value));
  }

  return url.toString();
}
