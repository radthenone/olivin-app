import { log } from "@pack/logger";
import { CONFIG } from "@core/env";
import { authStorage } from "@core/auth/auth.storage";
import { isNative } from "@lib";

export type ApiRequestConfig = {
  url: string;
  method?: string;
  params?: Record<string, unknown>;
  data?: unknown;
  body?: BodyInit | null;
  headers?: HeadersInit;
  signal?: AbortSignal;
  throwOnError?: boolean;
};

export type ApiErrorResponse<T = unknown> = {
  status: number;
  data: T;
  headers: Headers;
  config: ApiRequestConfig;
};

export class ApiError<T = unknown> extends Error {
  response: ApiErrorResponse<T>;
  config: ApiRequestConfig;

  constructor(message: string, response: ApiErrorResponse<T>) {
    super(message);
    this.name = "ApiError";
    this.response = response;
    this.config = response.config;
  }
}

type ApiResponseData<T = unknown> = {
  data: T;
  status: number;
  headers: Headers;
};

const UNSAFE_METHODS = new Set(["POST", "PUT", "PATCH", "DELETE"]);

let csrfInitPromise: Promise<void> | null = null;

function getCookieValue(name: string): string | null {
  if (typeof document === "undefined") return null;

  const cookies = document.cookie ? document.cookie.split(";") : [];
  for (const cookie of cookies) {
    const [rawKey, ...rest] = cookie.trim().split("=");
    if (rawKey === name) {
      return decodeURIComponent(rest.join("="));
    }
  }

  return null;
}

function buildUrl(config: ApiRequestConfig): string {
  const url = new URL(config.url, CONFIG.BASE_URL);

  Object.entries(config.params ?? {}).forEach(([key, value]) => {
    if (value === undefined || value === null) return;

    if (Array.isArray(value)) {
      value.forEach((item) => {
        if (item !== undefined && item !== null) {
          url.searchParams.append(key, String(item));
        }
      });
      return;
    }

    url.searchParams.set(key, String(value));
  });

  return url.toString();
}

async function ensureWebCsrfCookie(): Promise<void> {
  if (isNative) return;
  if (getCookieValue("csrftoken")) return;
  if (csrfInitPromise) return csrfInitPromise;

  const url = new URL("/_allauth/browser/v1/auth/session", CONFIG.BASE_URL);

  csrfInitPromise = fetch(url.toString(), {
    method: "GET",
    credentials: "include",
    headers: {
      Accept: "application/json",
      "x-api-version": CONFIG.VERSION,
    },
  })
    .then(() => undefined)
    .finally(() => {
      csrfInitPromise = null;
    });

  return csrfInitPromise;
}

async function readResponseData(response: Response): Promise<unknown> {
  if (response.status === 204) return undefined;

  const text = await response.text();
  if (!text) return undefined;

  const contentType = response.headers.get("content-type") ?? "";
  if (contentType.includes("application/json")) {
    return JSON.parse(text);
  }

  return text;
}

async function persistSessionToken(data: unknown): Promise<void> {
  if (!isNative) return;

  const token =
    (data as any)?.meta?.session_token ??
    (data as any)?.meta?.sessiontoken ??
    (data as any)?.meta?.sessionToken;

  if (typeof token === "string") {
    await authStorage.setSessionToken(token);
  }
}

async function buildHeaders(config: ApiRequestConfig): Promise<Headers> {
  const method = (config.method ?? "GET").toUpperCase();
  const headers = new Headers({
    Accept: "application/json",
    "Content-Type": "application/json",
    "x-api-version": CONFIG.VERSION,
  });

  new Headers(config.headers).forEach((value, key) => {
    headers.set(key, value);
  });

  if (!isNative && UNSAFE_METHODS.has(method)) {
    await ensureWebCsrfCookie();
    const csrfToken = getCookieValue("csrftoken");
    if (csrfToken) {
      headers.set("X-CSRFToken", csrfToken);
    }
  }

  if (isNative) {
    const sessionToken = await authStorage.getSessionToken();
    if (sessionToken) {
      headers.set("X-Session-Token", sessionToken);
    }
  }

  return headers;
}

async function executeApiRequest(
  config: ApiRequestConfig,
): Promise<ApiResponseData> {
  const method = (config.method ?? "GET").toUpperCase();
  const headers = await buildHeaders(config);
  const body =
    config.body ??
    (config.data === undefined ? undefined : JSON.stringify(config.data));
  const url = buildUrl(config);

  if (CONFIG.IS_DEV) {
    log.info("[API Request]", { method, url, params: config.params });
  }

  const response = await fetch(url, {
    method,
    headers,
    body,
    signal: config.signal,
    credentials: isNative ? "same-origin" : "include",
  });

  const data = await readResponseData(response);

  if (isNative && (response.status === 401 || response.status === 410)) {
    await authStorage.removeSessionToken();
  } else {
    await persistSessionToken(data);
  }

  const isAllauthFlowResponse =
    config.url.startsWith("/_allauth/") &&
    (response.status === 401 || response.status === 410);

  if (!response.ok && !isAllauthFlowResponse && config.throwOnError !== false) {
    const errorResponse = {
      status: response.status,
      data,
      headers: response.headers,
      config,
    };

    if (CONFIG.IS_DEV) {
      log.error("[API Response Error]", {
        status: response.status,
        url,
        data,
      });
    }

    throw new ApiError(
      `Request failed with status ${response.status}`,
      errorResponse,
    );
  }

  if (CONFIG.IS_DEV) {
    log.info("[API Response]", { status: response.status, url, data });
  }

  return {
    data,
    status: response.status,
    headers: response.headers,
  };
}

export async function apiRequest<T>(config: ApiRequestConfig): Promise<T> {
  const response = await executeApiRequest(config);
  return response.data as T;
}

export async function apiResponse<T>(config: ApiRequestConfig): Promise<T> {
  const response = await executeApiRequest(config);
  return response as T;
}

const apiClient = {
  async request<T>(config: ApiRequestConfig): Promise<{ data: T }> {
    const data = await apiRequest<T>(config);
    return { data };
  },

  async get<T>(
    url: string,
    config: Omit<ApiRequestConfig, "url" | "method"> = {},
  ): Promise<{ data: T }> {
    return this.request<T>({ ...config, url, method: "GET" });
  },

  async post<T>(
    url: string,
    data?: unknown,
    config: Omit<ApiRequestConfig, "url" | "method" | "data"> = {},
  ): Promise<{ data: T }> {
    return this.request<T>({ ...config, url, method: "POST", data });
  },

  async patch<T>(
    url: string,
    data?: unknown,
    config: Omit<ApiRequestConfig, "url" | "method" | "data"> = {},
  ): Promise<{ data: T }> {
    return this.request<T>({ ...config, url, method: "PATCH", data });
  },

  async put<T>(
    url: string,
    data?: unknown,
    config: Omit<ApiRequestConfig, "url" | "method" | "data"> = {},
  ): Promise<{ data: T }> {
    return this.request<T>({ ...config, url, method: "PUT", data });
  },

  async delete<T>(
    url: string,
    config: Omit<ApiRequestConfig, "url" | "method"> = {},
  ): Promise<{ data: T }> {
    return this.request<T>({ ...config, url, method: "DELETE" });
  },
};

export default apiClient;
