import { AxiosInstance, InternalAxiosRequestConfig } from "axios";
import { CONFIG } from "src/core/env";

export function setupVersioningInterceptor(apiClient: AxiosInstance): number {
  return apiClient.interceptors.request.use(
    (config: InternalAxiosRequestConfig) => {
      if (config.url?.startsWith("/_allauth/")) {
        return config;
      }

      if (config.url?.startsWith("/api/")) {
        const versionPattern = /^\/api\/v\d+\//;
        if (versionPattern.test(config.url)) {
          return Promise.reject(
            new Error(`API version already in URL: ${config.url}`),
          );
        }
        config.url = config.url.replace("/api/", `/api/${CONFIG.VERSION}/`);
      }
      return config;
    },
  );
}
