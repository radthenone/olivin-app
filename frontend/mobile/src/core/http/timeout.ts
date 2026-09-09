import { ENV } from "@core/config/env";
import type { TimeoutController } from "./types";

export function createTimeoutController(
  timeoutMs?: number,
): TimeoutController | null {
  const effectiveTimeoutMs = timeoutMs ?? ENV.HTTP_TIMEOUT;

  if (!effectiveTimeoutMs || effectiveTimeoutMs <= 0) {
    return null;
  }

  const controller = new AbortController();

  const timeoutId = setTimeout(() => {
    controller.abort(new Error("Request timeout"));
  }, effectiveTimeoutMs);

  return {
    signal: controller.signal,
    cleanup: () => clearTimeout(timeoutId),
  };
}
