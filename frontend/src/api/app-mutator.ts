import apiClient from "@http/client";
import type { AxiosRequestConfig, AxiosResponse } from "axios";

export const appInstance = <T>(config: AxiosRequestConfig): Promise<T> => {
  return apiClient(config).then(({ data }) => data);
};

export type ErrorType<Error> = AxiosResponse<Error>;
export type BodyType<BodyData> = BodyData;
