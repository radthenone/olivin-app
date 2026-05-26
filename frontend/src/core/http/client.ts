import { allauthClient } from "@core/config/platform";
import { getDurationMs, logError, logRequest, logResponse } from "./logging";
import { createRequest } from "./request";
import { getResponseBody } from "./response";
import { createTimeoutController } from "./timeout";
import type { HttpRequestConfig, HttpResponse } from "./types";
import { ApiError } from "./errors";

function isAcceptedStatus(config: HttpRequestConfig, status: number): boolean {
  if (config.acceptStatuses === "all") {
    return true;
  }

  return config.acceptStatuses?.includes(status) ?? false;
}

export class HttpClient {
  async request<TData = unknown>(
    config: HttpRequestConfig,
  ): Promise<HttpResponse<TData>> {
    const request = await createRequest(config);

    const timeoutController = createTimeoutController(config.timeoutMs);

    const startTime = performance.now();

    logRequest(config, request.method, request.url, request.headers);

    try {
      const response = await fetch(request.url, {
        method: request.method,
        headers: request.headers,
        body: request.body,
        signal: request.signal ?? timeoutController?.signal,
        credentials: allauthClient === "browser" ? "include" : "same-origin",
      });

      const responseData = await getResponseBody<TData>(response);

      const durationMs = getDurationMs(startTime);

      if (!response.ok && !isAcceptedStatus(config, response.status)) {
        const apiError = new ApiError(
          {
            status: response.status,
            data: responseData,
            headers: response.headers,
            config,
          },
          `Request failed with status ${response.status}`,
        );

        logError(request.url, request.method, durationMs, apiError);

        throw apiError;
      }

      logResponse(request.url, response.status, durationMs, responseData);

      return {
        data: responseData,
        status: response.status,
        headers: response.headers,
      };
    } catch (error: unknown) {
      const durationMs = getDurationMs(startTime);

      logError(request.url, request.method, durationMs, error);

      if (error instanceof ApiError) {
        throw error;
      }

      throw new ApiError(
        {
          status: 0,
          data: undefined,
          headers: new Headers(),
          config,
        },
        error instanceof Error ? error.message : "Network request failed",
      );
    } finally {
      timeoutController?.cleanup();
    }
  }
}

export const httpClient = new HttpClient();

export function httpRequest<TData = unknown>(
  config: HttpRequestConfig,
): Promise<HttpResponse<TData>> {
  return httpClient.request(config);
}
