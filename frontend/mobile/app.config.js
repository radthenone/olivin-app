const { loadEnv } = require("@olivin/config/load-env.js");

loadEnv();

const getAppVersion = () => {
  return process.env.EXPO_PUBLIC_VERSION || "v1";
};

const facebookScheme = process.env.EXPO_PUBLIC_FACEBOOK_CLIENT_ID
  ? `fb${process.env.EXPO_PUBLIC_FACEBOOK_CLIENT_ID}`
  : undefined;

export default {
  expo: {
    name: process.env.EXPO_PUBLIC_APP_NAME || "Olivin",
    slug: "olivin",
    version: getAppVersion(),
    orientation: "portrait",
    icon: "./assets/images/icon.png",
    // Identyfikatory pakietów (com.olivin.frontend) zostają: Google i Facebook
    // mają je zarejestrowane razem z odciskiem klucza, zmiana zerwałaby
    // logowanie społecznościowe na urządzeniach.
    scheme: [
      "olivin",
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
      "expo-router",
      // SDK 57 wymaga jawnej rejestracji tych modulow jako pluginow konfiguracji.
      "expo-font",
      "expo-image",
      "expo-secure-store",
      "expo-status-bar",
      "expo-web-browser",
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
