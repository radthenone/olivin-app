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
    async (res) => {
      if (isNative) {
        const sessionToken = res.data?.meta?.sessionToken;
        if (sessionToken) {
          await SecureStore.setItemAsync("sessionToken", sessionToken);
        }
      }
      return res;
    },
    async (error) => {
      const status = error.response?.status;

      if (isNative) {
        // 401 - brak autoryzacji
        if (status === 401) {
          await SecureStore.deleteItemAsync("sessionToken");
          // TODO: navigate to login
        }

        // ✅ 410 Gone - sesja wygasła, wyczyść token
        if (status === 410) {
          await SecureStore.deleteItemAsync("sessionToken");
          // TODO: navigate to login, show "session expired" message
        }
      }

      return Promise.reject(error);
    },
  );

  return { request, response };
}
