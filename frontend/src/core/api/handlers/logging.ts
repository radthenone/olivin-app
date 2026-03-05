import { log } from "@pack/logger";
import {
  InternalAxiosRequestConfig as Request,
  AxiosResponse as Response,
} from "axios";

function logRequest(request: Request): void {
  log.info("[API Request] Requesting URL", {
    method: request.method,
    url: request.url,
    headers: request.headers,
    data: request.data,
    params: request.params,
    baseURL: request.baseURL,
    timeout: request.timeout,
    withCredentials: request.withCredentials,
    responseType: request.responseType,
    responseEncoding: request.responseEncoding,
    maxContentLength: request.maxContentLength,
    maxBodyLength: request.maxBodyLength,
    validateStatus: request.validateStatus,
  });
}

function logRequestError(error: any): void {
  log.error("[API Request Error]", error);
}

function logResponse(response: Response): void {
  log.info("[API Response] Response received", {
    status: response.status,
    data: response.data,
    headers: response.headers,
    config: response.config,
  });
}

function logResponseError(error: any): void {
  log.error("[API Response Error]", {
    message: error.message,
    url: error.config?.url,
    baseURL: error.config?.baseURL,
    status: error.response?.status,
    data: error.response?.data,
  });
}

export { logRequest, logRequestError, logResponse, logResponseError };
