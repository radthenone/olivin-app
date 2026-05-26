export type HttpMethod =
  | "GET"
  | "POST"
  | "PUT"
  | "PATCH"
  | "DELETE"
  | "HEAD"
  | "OPTIONS";

export type Primitive = string | number | boolean | null | undefined;

export type QueryParams = Record<
  string,
  Primitive | Primitive[] | Record<string, Primitive>
>;

export type HttpRequestConfig = {
  url: string;
  method?: HttpMethod;
  params?: QueryParams;
  data?: unknown;
  body?: BodyInit | null;
  headers?: HeadersInit;
  signal?: AbortSignal;
  timeoutMs?: number;
  acceptStatuses?: number[] | "all";
  throwOnError?: boolean;
};

export type HttpRequest = {
  url: string;
  method: HttpMethod;
  headers: Headers;
  body?: BodyInit | null;
  signal?: AbortSignal;
  config: HttpRequestConfig;
};

export type HttpResponse<TData = unknown> = {
  data: TData;
  status: number;
  headers: Headers;
};

export type TimeoutController = {
  signal: AbortSignal;
  cleanup: () => void;
};
