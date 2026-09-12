import type { HttpRequestConfig } from "./types";

export type ApiErrorResponse<T = unknown> = {
  status: number;
  data: T;
  headers: Headers;
  config: HttpRequestConfig;
};

export class ApiError<T = unknown> extends Error {
  response: ApiErrorResponse<T>;

  constructor(response: ApiErrorResponse<T>, message?: string) {
    super(message ?? `Request failed with status ${response.status}`);

    this.name = "ApiError";
    this.response = response;
  }

  isNetworkError(): boolean {
    return this.response.status === 0;
  }

  isClientError(): boolean {
    return this.response.status >= 400 && this.response.status < 500;
  }

  isServerError(): boolean {
    return this.response.status >= 500 && this.response.status < 600;
  }
}
