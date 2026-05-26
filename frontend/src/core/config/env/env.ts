import { ExtraSchema } from "./env.zod";
import Constants from "expo-constants";
import { isAndroid } from "@core/config/platform";
import { flattenError } from "zod";

const normalizeUrl = (value: string) =>
  /^https?:\/\//.test(value) ? value : `http://${value}`;

const alignWebLoopbackHost = (url: string) => {
  if (typeof window === "undefined") return url;

  const currentHostname = window.location.hostname;
  if (!["localhost", "127.0.0.1"].includes(currentHostname)) return url;

  try {
    const parsed = new URL(url);
    if (!["localhost", "127.0.0.1"].includes(parsed.hostname)) return url;

    parsed.hostname = currentHostname;
    return parsed.toString().replace(/\/$/, "");
  } catch {
    return url;
  }
};

const buildEnv = () => {
  const parsed = ExtraSchema.safeParse(Constants.expoConfig?.extra ?? {});

  if (!parsed.success) {
    if (__DEV__) {
      console.error("Invalid Expo extra config", flattenError(parsed.error));
    }
    throw new Error("Invalid Expo extra config");
  }

  const extra = parsed.data;
  const webUrl = alignWebLoopbackHost(normalizeUrl(extra.webUrl));
  const androidUrl = normalizeUrl(extra.androidUrl ?? extra.webUrl);

  return {
    API_BASE_URL: isAndroid ? androidUrl : webUrl,
    IS_DEV: extra.isDev,
    APP_VERSION: extra.appVersion,
    HTTP_TIMEOUT: extra.httpTimeout,
    SESSION_TOKEN_KEY: extra.sessionTokenKey,
    GOOGLE_CLIENT_ID: extra.googleClientId ?? "",
    GOOGLE_WEB_CLIENT_ID: extra.googleWebClientId ?? extra.googleClientId ?? "",
    GOOGLE_ANDROID_CLIENT_ID:
      extra.googleAndroidClientId ?? extra.googleClientId ?? "",
    FACEBOOK_CLIENT_ID: extra.facebookClientId ?? "",
  } as const;
};

export const ENV = buildEnv();
