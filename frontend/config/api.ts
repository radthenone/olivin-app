import { Platform } from "react-native";

/**
 * Konfiguracja API z automatycznym wyborem URL w zależności od platformy.
 *
 * Używa zmiennej środowiskowej EXPO_PUBLIC_API_BASE_URL lub domyślnych wartości:
 * - Web: localhost:8020
 * - Android Emulator: 10.0.2.2:8020 (10.0.2.2 to specjalny adres emulatora wskazujący na localhost hosta)
 * - iOS Simulator: localhost:8020
 *
 * Jeśli zmienna środowiskowa zawiera localhost i platforma to Android,
 * automatycznie zamienia localhost na 10.0.2.2
 */
const getBaseURL = (): string => {
  // Sprawdź czy jest ustawiona zmienna środowiskowa
  const envUrl = process.env.EXPO_PUBLIC_API_BASE_URL;

  if (envUrl) {
    // Dla Androida, jeśli URL zawiera localhost, zamień na 10.0.2.2
    if (Platform.OS === "android" && envUrl.includes("localhost")) {
      const androidUrl = envUrl.replace("localhost", "10.0.2.2");
      console.log(`[API Config] Android: converted ${envUrl} to ${androidUrl}`);
      return androidUrl;
    }
    console.log(`[API Config] Using environment variable: ${envUrl}`);
    return envUrl;
  }

  // Domyślne wartości w zależności od platformy
  let baseURL: string;

  if (Platform.OS === "web") {
    baseURL = "http://localhost:8020";
  } else if (Platform.OS === "android") {
    // Android emulator używa 10.0.2.2 zamiast localhost
    // To specjalny adres, który wskazuje na localhost maszyny hosta
    baseURL = "http://10.0.2.2:8020";
  } else {
    // iOS Simulator i inne platformy
    baseURL = "http://localhost:8020";
  }

  console.log(`[API Config] Platform: ${Platform.OS}, Base URL: ${baseURL}`);
  return baseURL;
};

export const API_CONFIG = {
  BASE_URL: getBaseURL(),

  ENDPOINTS: {
    AUTH: "/api/auth/",
    PRODUCTS: "/api/products/",
    ORDERS: "/api/orders/",
    CART: "/api/cart/",
    HEALTH: "/health/",
    LOGS: "/logs/",
  },
};

export default API_CONFIG;
