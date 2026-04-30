import {
  apiResponse,
  type ApiError,
  type ApiRequestConfig,
} from "@http/client";

export const appInstance = <T>(
  url: string,
  options: RequestInit = {},
): Promise<T> => {
  const config: ApiRequestConfig = {
    url,
    method: options.method,
    headers: options.headers,
    body: options.body,
    signal: options.signal ?? undefined,
  };

  return apiResponse<T>(config);
};

export type ErrorType<Error> = ApiError<Error>;
export type BodyType<BodyData> = BodyData;
