import { AxiosInstance, InternalAxiosRequestConfig } from "axios";

export function setupVersioningInterceptor(apiClient: AxiosInstance): number {
  return apiClient.interceptors.request.use(
    (config: InternalAxiosRequestConfig) => {
      if (config.url?.startsWith("/_allauth/")) {
        return config;
      }

      if (config.url?.startsWith("/api/")) {
        const versionPattern = /^\/api\/v\d+\//;
        if (!versionPattern.test(config.url)) {
          return Promise.reject(
            new Error(`API version missing in URL: ${config.url}`),
          );
        }
      }
      return config;
    },
  );
}
