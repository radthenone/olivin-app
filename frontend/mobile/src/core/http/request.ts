import { buildHeaders } from "./headers";
import type { HttpMethod, HttpRequest, HttpRequestConfig } from "./types";
import { buildUrl } from "./url";
import { buildRequestBody } from "./body";

function normalizeMethod(method?: string): HttpMethod {
  return (method?.toUpperCase() ?? "GET") as HttpMethod;
}

export async function createRequest(
  config: HttpRequestConfig,
): Promise<HttpRequest> {
  const method = normalizeMethod(config.method);

  const headers = await buildHeaders(config);

  return {
    url: buildUrl(config),
    method,
    headers,
    body: buildRequestBody(config),
    signal: config.signal,
    config,
  };
}
