import type { HttpClient } from "@core/http/client";
import type { HttpMethod, HttpRequestConfig } from "@core/http/types";

const HTTP_METHODS = new Set<HttpMethod>([
  "GET",
  "POST",
  "PUT",
  "PATCH",
  "DELETE",
  "HEAD",
  "OPTIONS",
]);

function toHttpMethod(method?: string): HttpMethod | undefined {
  if (!method) return undefined;
  const normalized = method.toUpperCase() as HttpMethod;
  return HTTP_METHODS.has(normalized) ? normalized : undefined;
}

/**
 * Tworzy mutator Orvala dla endpointów aplikacyjnych.
 *
 * Dlaczego istnieje:
 * endpointy app używają tego samego transportu HTTP,
 * ale nie mają allauth session lifecycle.
 */
export function createAppMutator(client: HttpClient) {
  return async function appInstance<T>(
    url: string,
    options: RequestInit = {},
  ): Promise<T> {
    const config: HttpRequestConfig = {
      url,
      method: toHttpMethod(options.method),
      headers: options.headers,
      body: options.body,
      signal: options.signal ?? undefined,
    };

    return client.request(config) as Promise<T>;
  };
}
