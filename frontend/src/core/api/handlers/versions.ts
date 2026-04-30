import { log } from "@pack/logger";
import type { ApiRequestConfig } from "@http/client";

export async function checkUrl(request: ApiRequestConfig): Promise<void> {
  if (!request.url) {
    log.error("[API Request Error] No URL provided");
    throw new Error("No URL provided");
  }
}
