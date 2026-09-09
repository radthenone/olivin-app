const { loadEnv } = require("./load-env");

loadEnv();

const getAppVersion = () => {
  return process.env.EXPO_PUBLIC_VERSION || "v1";
};

const facebookScheme = process.env.EXPO_PUBLIC_FACEBOOK_CLIENT_ID
  ? `fb${process.env.EXPO_PUBLIC_FACEBOOK_CLIENT_ID}`
  : undefined;

export default {
  expo: {
    name: process.env.EXPO_PUBLIC_BACKEND_URL || "frontend",
    slug: "frontend",
    version: getAppVersion(),
    orientation: "portrait",
    icon: "./assets/images/icon.png",
    scheme: [
      "frontend",
      "com.olivin.frontend",
      ...(facebookScheme ? [facebookScheme] : []),
    ],
    userInterfaceStyle: "automatic",
    newArchEnabled: true,
    updates: {
      enabled: false,
      checkAutomatically: "NEVER",
      fallbackToCacheTimeout: 0,
    },
    developer: {
      tool: "expo-cli",
    },
    ios: {
      supportsTablet: true,
      bundleIdentifier: "com.olivin.frontend",
    },
    android: {
      adaptiveIcon: {
        backgroundColor: "#E6F4FE",
        foregroundImage: "./assets/images/android-icon-foreground.png",
        backgroundImage: "./assets/images/android-icon-background.png",
        monochromeImage: "./assets/images/android-icon-monochrome.png",
      },
      edgeToEdgeEnabled: false,
      predictiveBackGestureEnabled: false,
      softwareKeyboardLayoutMode: "pan",
      package: "com.olivin.frontend",
    },
    web: {
      output: "static",
      bundler: "metro",
      favicon: "./assets/images/favicon.png",
    },
    plugins: [
      "@rnrepo/expo-config-plugin",
      "expo-router",
      [
        "expo-splash-screen",
        {
          image: "./assets/images/splash-icon.png",
          imageWidth: 200,
          resizeMode: "contain",
          backgroundColor: "#ffffff",
          dark: {
            image: "./assets/images/splash-icon.png",
            backgroundColor: "#000000",
          },
        },
      ],
    ],
    experiments: {
      typedRoutes: false,
    },
    extra: {
      isDev: process.env.EXPO_PUBLIC_NODE_ENV === "development" ? true : false,
      appVersion: getAppVersion(),
      httpTimeout: parseInt(process.env.EXPO_PUBLIC_HTTP_TIMEOUT) || 30000,
      webUrl: process.env.EXPO_PUBLIC_BACKEND_URL || "127.0.0.1:8020",
      androidUrl:
        process.env.EXPO_PUBLIC_ANDROID_URL ||
        process.env.EXPO_PUBLIC_EMULATOR_URL ||
        "10.0.2.2:8020",
      sessionTokenKey:
        process.env.EXPO_SESSION_TOKEN_KEY || "auth.sessionToken",
      googleClientId: process.env.EXPO_PUBLIC_GOOGLE_CLIENT_ID,
      googleWebClientId:
        process.env.EXPO_PUBLIC_GOOGLE_WEB_CLIENT_ID ||
        process.env.EXPO_PUBLIC_GOOGLE_CLIENT_ID,
      googleAndroidClientId:
        process.env.EXPO_PUBLIC_GOOGLE_ANDROID_CLIENT_ID ||
        process.env.EXPO_PUBLIC_GOOGLE_CLIENT_ID,
      facebookClientId: process.env.EXPO_PUBLIC_FACEBOOK_CLIENT_ID,
    },
  },
};
