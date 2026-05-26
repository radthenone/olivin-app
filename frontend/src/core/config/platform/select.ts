import { Platform } from "react-native";

type PlatformValues<T> = {
  web?: T;
  native?: T;
  android?: T;
  ios?: T;
  default?: T;
};

export function selectPlatform<T>(values: PlatformValues<T>): T | undefined {
  const result = Platform.select({
    web: values.web,
    android: values.android ?? values.native,
    ios: values.ios ?? values.native,
    native: values.native,
    default: values.default,
  });

  return result ?? values.default;
}
