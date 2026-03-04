import { Platform } from "react-native";
import { log } from "@pack/logger";
import Constants from "expo-constants";

const normalizeUrl = (url: string): string => {
  if (/^https?:\/\//.test(url)) {
    return url;
  }
  return `http://${url}`;
};

export const getApiBaseUrl = (): string => {
  let baseURL: string | undefined;

  if (Platform.OS === "web") {
    baseURL = Constants.expoConfig?.extra?.webUrl;
  } else if (Platform.OS === "android") {
    baseURL = Constants.expoConfig?.extra?.androidUrl;
  }
  if (!baseURL) {
    log.error("No API URL found");
    return "";
  }

  return normalizeUrl(baseURL);
};

export const getApiDev = (): boolean => {
  if (Constants.expoConfig?.extra?.isDev === true) {
    return true;
  }
  return false;
};

export const BASE_URL = getApiBaseUrl();

export const VERSION = Constants.expoConfig?.extra?.appVersion;

export const TIMEOUT = 10000;

const CLIENT = Platform.OS === "web" ? "browser" : "app";

export const CONFIG = {
  BASE_URL,
  VERSION,
  TIMEOUT,
  IS_DEV: getApiDev(),
  CLIENT,
} as const;
