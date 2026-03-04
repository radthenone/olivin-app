import { AxiosInstance } from "axios";
import {
  checkUrl,
  logRequest,
  logResponse,
  logResponseError,
  logRequestError,
} from "@core/api/handlers";

export function setupLoggingInterceptor(apiClient: AxiosInstance) {
  const requestId = apiClient.interceptors.request.use(
    async (config) => {
      await checkUrl(config);
      logRequest(config);
      return config;
    },
    (error) => {
      logRequestError(error);
      return Promise.reject(error);
    },
  );

  const responseId = apiClient.interceptors.response.use(
    (response) => {
      logResponse(response);
      return response;
    },
    (error) => {
      logResponseError(error);
      return Promise.reject(error);
    },
  );

  return { request: requestId, response: responseId };
}
