import apiClient from "@api/client";
import type { AxiosRequestConfig, AxiosResponse } from "axios";

export const authInstance = <T>(config: AxiosRequestConfig): Promise<T> => {
  return apiClient(config).then(({ data }) => data);
};

export type ErrorType<Error> = AxiosResponse<Error>;
export type BodyType<BodyData> = BodyData;
