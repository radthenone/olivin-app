import { log } from "@pack/logger";
import { InternalAxiosRequestConfig } from "axios";

export async function checkUrl(
  request: InternalAxiosRequestConfig,
): Promise<void> {
  const apiPattern = /^\/api\//;
  const versionPattern = /^\/v\d+\//;

  if (!request.url) {
    log.error("[API Request Error] No URL provided");
    throw new Error("No URL provided");
  }

  // 1. check /api/ pattern
  if (!apiPattern.test(request.url)) {
    log.error("[API Request Error] URL must start with /api/", {
      url: request.url,
    });
    throw new Error("URL must start with /api/");
  }

  // 2. without /api/ check /v1/ pattern
  if (!versionPattern.test(request.url.slice(4))) {
    log.error("[API Request Error] URL must include version (e.g., /api/v1/)", {
      url: request.url,
    });
    throw new Error("URL must include version (e.g., /api/v1/)");
  }
}
