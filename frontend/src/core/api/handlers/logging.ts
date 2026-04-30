import { log } from "@pack/logger";

export function logRequest(request: unknown): void {
  log.info("[API Request]", request as any);
}

export function logRequestError(error: unknown): void {
  log.error("[API Request Error]", error as any);
}

export function logResponse(response: unknown): void {
  log.info("[API Response]", response as any);
}

export function logResponseError(error: unknown): void {
  log.error("[API Response Error]", error as any);
}
