const { loadEnv } = require("./load-env");

loadEnv();

const getAppVersion = () => {
  return process.env.EXPO_PUBLIC_VERSION || "v1";
};

export default {
  expo: {
    name: process.env.EXPO_PUBLIC_BACKEND_URL || "frontend",
    slug: "frontend",
    version: getAppVersion(),
    orientation: "portrait",
    icon: "./assets/images/icon.png",
    scheme: "frontend",
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
      edgeToEdgeEnabled: true,
      predictiveBackGestureEnabled: false,
      package: "com.olivin.frontend",
    },
    web: {
      output: "static",
      favicon: "./assets/images/favicon.png",
      bundler: "metro",
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
      webUrl: process.env.EXPO_PUBLIC_BACKEND_URL || "127.0.0.1:8020",
      androidUrl: process.env.EXPO_PUBLIC_EMULATOR_URL || "10.0.2.2:8020",
      sessionTokenKey:
        process.env.EXPO_SESSION_TOKEN_KEY || "auth.sessionToken",
    },
  },
};
