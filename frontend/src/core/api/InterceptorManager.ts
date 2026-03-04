import { AxiosInstance } from "axios";
import { CONFIG } from "src/core/env";
import {
  setupLoggingInterceptor,
  setupVersioningInterceptor,
  setupAuthInterceptor,
} from "./interceptors";

type InterceptorIds = {
  logging?: { request: number; response: number };
  auth?: { request: number; response: number };
  versioning?: number;
};

class ApiInterceptorManager {
  private ids: InterceptorIds = {};

  setupAll(apiClient: AxiosInstance): InterceptorIds {
    if (CONFIG.IS_DEV) {
      this.ids.logging = setupLoggingInterceptor(apiClient);
    }

    this.ids.versioning = setupVersioningInterceptor(apiClient);
    this.ids.auth = setupAuthInterceptor(apiClient);

    return this.ids;
  }

  ejectAll(apiClient: AxiosInstance): void {
    Object.values(this.ids).forEach((interceptor) => {
      if (!interceptor) return;
      if (typeof interceptor === "number") {
        apiClient.interceptors.request.eject(interceptor);
      } else {
        apiClient.interceptors.request.eject(interceptor.request);
        apiClient.interceptors.response.eject(interceptor.response);
      }
    });
    this.ids = {};
  }
}

export const interceptorManager = new ApiInterceptorManager();
