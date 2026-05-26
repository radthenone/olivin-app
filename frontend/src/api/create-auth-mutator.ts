import type { HttpClient } from "@core/http/client";
import type { HttpMethod, HttpRequestConfig } from "@core/http/types";
import { handleAllauthSessionLifecycle } from "@core/auth/session-lifecycle";

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
 * Tworzy mutator Orvala dla endpointów allauth.
 *
 * Dlaczego istnieje:
 * allauth ma własny lifecycle sesji, więc po odpowiedzi trzeba obsłużyć
 * meta.session_token dla klienta app.
 */
export function createAuthMutator(client: HttpClient) {
  return async function authInstance<T>(
    url: string,
    options: RequestInit = {},
  ): Promise<T> {
    const config: HttpRequestConfig = {
      url,
      method: toHttpMethod(options.method),
      headers: options.headers,
      body: options.body,
      signal: options.signal ?? undefined,
      acceptStatuses: "all",
    };

    const response = await client.request(config);
    await handleAllauthSessionLifecycle(response);

    return response as T;
  };
}
