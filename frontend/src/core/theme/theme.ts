import { useColorScheme } from "react-native";

// React Native automatycznie wybierze odpowiedni plik:
// - theme.web.ts dla web
// - theme.native.ts dla android/ios
import { getWebTheme, AppTheme as WebAppTheme } from "./theme.web";
import { getNativeTheme, AppTheme as NativeAppTheme } from "./theme.native";

// Eksportujemy wspólny typ
export type AppTheme = WebAppTheme | NativeAppTheme;

/**
 * Pobiera odpowiedni motyw dla aktualnej platformy
 * Automatycznie wybiera theme.web.ts lub theme.native.ts
 */
export const getTheme = (isDark: boolean): AppTheme => {
  if (typeof window !== "undefined") {
    return getWebTheme(isDark);
  }
  return getNativeTheme(isDark);
};

/**
 * Hook do pobierania motywu dla aktualnej platformy
 * Zgodnie z dokumentacją Expo: https://docs.expo.dev/develop/user-interface/color-themes
 */
export const useTheme = (): AppTheme => {
  const colorScheme = useColorScheme();
  // useColorScheme może zwracać "light", "dark" lub null
  // Domyślnie używamy trybu jasnego, jeśli colorScheme jest null
  const isDark = colorScheme === "dark";
  return getTheme(isDark);
};
