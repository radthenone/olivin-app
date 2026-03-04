// src/core/api/interceptors/auth.ts
import * as SecureStore from "expo-secure-store";
import { AxiosInstance, InternalAxiosRequestConfig } from "axios";
import { isNative } from "@lib";

export function setupAuthInterceptor(apiClient: AxiosInstance): {
  request: number;
  response: number;
} {
  const request = apiClient.interceptors.request.use(
    async (config: InternalAxiosRequestConfig) => {
      config.withCredentials = true;

      if (isNative) {
        const sessionToken = await SecureStore.getItemAsync("sessionToken");
        if (sessionToken) {
          config.headers["X-Session-Token"] = sessionToken;
        }
      }

      return config;
    },
  );

  const response = apiClient.interceptors.response.use(
    (res) => res,
    async (error) => {
      if (error.response?.status === 401) {
        if (isNative) {
          await SecureStore.deleteItemAsync("sessionToken");
        }
        // TODO: navigate to login
      }
      return Promise.reject(error);
    },
  );

  return { request, response };
}
