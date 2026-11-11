import { mock } from "bun:test";
import * as ReactNativeWeb from "react-native-web";

mock.module("react-native", () => ({
  ...ReactNativeWeb,
  Platform: {
    OS: "android",
    select: (obj: Record<string, unknown>) => obj.android ?? obj.default,
  },
  TurboModuleRegistry: {
    get: () => null,
    getEnforcing: () => null,
  },
}));

mock.module("expo-secure-store", () => ({
  getItemAsync: async () => null,
  setItemAsync: async () => {},
  deleteItemAsync: async () => {},
}));

mock.module("expo-constants", () => ({
  default: {
    expoConfig: {
      extra: {
        webUrl: "http://localhost:8020",
        androidUrl: "http://10.0.2.2:8020",
        isDev: true,
        appVersion: "v1",
      },
    },
  },
}));
