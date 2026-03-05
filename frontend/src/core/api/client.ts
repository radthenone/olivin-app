import { CONFIG } from "@core/env";
import axios, { AxiosInstance } from "axios";
import { interceptorManager } from "@http/InterceptorManager";

const apiClient: AxiosInstance = axios.create({
  baseURL: CONFIG.BASE_URL,
  timeout: CONFIG.TIMEOUT,
  headers: {
    "Content-Type": "application/json",
    "x-api-version": CONFIG.VERSION,
  },
});

interceptorManager.setupAll(apiClient);

export default apiClient;
