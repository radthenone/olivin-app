import type { HttpRequestConfig } from "./types";

export function buildRequestBody(
  config: HttpRequestConfig,
): BodyInit | null | undefined {
  if (config.body !== undefined) {
    return config.body;
  }

  if (config.data === undefined) {
    return undefined;
  }

  if (
    typeof config.data === "string" ||
    config.data instanceof FormData ||
    config.data instanceof URLSearchParams ||
    config.data instanceof Blob ||
    config.data instanceof ArrayBuffer
  ) {
    return config.data as BodyInit;
  }

  return JSON.stringify(config.data);
}
