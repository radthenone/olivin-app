import { Theme } from "@react-navigation/native";
import { Platform, useColorScheme } from "react-native";

/**
 * Kolory bazowe dla aplikacji Native (Android/iOS)
 */
export interface AppColors {
  primary: string;
  secondary: string;
  background: string;
  card: string;
  text: string;
  border: string;
  notification: string;
  error: string;
  success: string;
  warning: string;
  info: string;
  surface: string;
  onSurface: string;
}

/**
 * Rozszerzony motyw aplikacji Native
 */
export interface AppTheme extends Theme {
  colors: Theme["colors"] & AppColors;
  spacing: {
    xs: number;
    sm: number;
    md: number;
    lg: number;
    xl: number;
    xxl: number;
  };
  borderRadius: {
    sm: number;
    md: number;
    lg: number;
    xl: number;
    full: number;
  };
  typography: {
    fontSize: {
      xs: number;
      sm: number;
      md: number;
      lg: number;
      xl: number;
      xxl: number;
      xxxl: number;
    };
    fontWeight: {
      normal: string;
      medium: string;
      semibold: string;
      bold: string;
    };
  };
  shadows: {
    sm: object;
    md: object;
    lg: object;
  };
}

/**
 * Motyw jasny dla platformy Android (Material Design)
 */
const androidLightTheme: AppTheme = {
  dark: false,
  colors: {
    primary: "#6200EE",
    secondary: "#03DAC6",
    background: "#FFFFFF",
    card: "#F5F5F5",
    text: "#212121",
    border: "#E0E0E0",
    notification: "#B00020",
    error: "#B00020",
    success: "#4CAF50",
    warning: "#FF9800",
    info: "#2196F3",
    surface: "#FFFFFF",
    onSurface: "#212121",
  },
  spacing: {
    xs: 4,
    sm: 8,
    md: 16,
    lg: 24,
    xl: 32,
    xxl: 48,
  },
  borderRadius: {
    sm: 4,
    md: 8,
    lg: 12,
    xl: 16,
    full: 9999,
  },
  typography: {
    fontSize: {
      xs: 12,
      sm: 14,
      md: 16,
      lg: 18,
      xl: 20,
      xxl: 24,
      xxxl: 32,
    },
    fontWeight: {
      normal: "400",
      medium: "500",
      semibold: "600",
      bold: "700",
    },
  },
  shadows: {
    sm: {
      elevation: 2,
    },
    md: {
      elevation: 4,
    },
    lg: {
      elevation: 8,
    },
  },
  fonts: {
    regular: {
      fontFamily: "System",
      fontWeight: "400" as const,
    },
    medium: {
      fontFamily: "System",
      fontWeight: "500" as const,
    },
    bold: {
      fontFamily: "System",
      fontWeight: "700" as const,
    },
    heavy: {
      fontFamily: "System",
      fontWeight: "900" as const,
    },
  },
};

/**
 * Motyw ciemny dla platformy Android (Material Design Dark)
 */
const androidDarkTheme: AppTheme = {
  dark: true,
  colors: {
    primary: "#BB86FC",
    secondary: "#03DAC6",
    background: "#121212",
    card: "#1E1E1E",
    text: "#FFFFFF",
    border: "#333333",
    notification: "#CF6679",
    error: "#CF6679",
    success: "#4CAF50",
    warning: "#FF9800",
    info: "#2196F3",
    surface: "#1E1E1E",
    onSurface: "#FFFFFF",
  },
  spacing: {
    xs: 4,
    sm: 8,
    md: 16,
    lg: 24,
    xl: 32,
    xxl: 48,
  },
  borderRadius: {
    sm: 4,
    md: 8,
    lg: 12,
    xl: 16,
    full: 9999,
  },
  typography: {
    fontSize: {
      xs: 12,
      sm: 14,
      md: 16,
      lg: 18,
      xl: 20,
      xxl: 24,
      xxxl: 32,
    },
    fontWeight: {
      normal: "400",
      medium: "500",
      semibold: "600",
      bold: "700",
    },
  },
  shadows: {
    sm: {
      elevation: 2,
    },
    md: {
      elevation: 4,
    },
    lg: {
      elevation: 8,
    },
  },
  fonts: {
    regular: {
      fontFamily: "System",
      fontWeight: "400" as const,
    },
    medium: {
      fontFamily: "System",
      fontWeight: "500" as const,
    },
    bold: {
      fontFamily: "System",
      fontWeight: "700" as const,
    },
    heavy: {
      fontFamily: "System",
      fontWeight: "900" as const,
    },
  },
};

/**
 * Motyw jasny dla platformy iOS
 */
const iosLightTheme: AppTheme = {
  dark: false,
  colors: {
    primary: "#007AFF",
    secondary: "#5856D6",
    background: "#F2F2F7",
    card: "#FFFFFF",
    text: "#000000",
    border: "#C6C6C8",
    notification: "#FF3B30",
    error: "#FF3B30",
    success: "#34C759",
    warning: "#FF9500",
    info: "#007AFF",
    surface: "#FFFFFF",
    onSurface: "#000000",
  },
  spacing: {
    xs: 4,
    sm: 8,
    md: 16,
    lg: 24,
    xl: 32,
    xxl: 48,
  },
  borderRadius: {
    sm: 4,
    md: 8,
    lg: 12,
    xl: 16,
    full: 9999,
  },
  typography: {
    fontSize: {
      xs: 12,
      sm: 14,
      md: 16,
      lg: 18,
      xl: 20,
      xxl: 24,
      xxxl: 32,
    },
    fontWeight: {
      normal: "400",
      medium: "500",
      semibold: "600",
      bold: "700",
    },
  },
  shadows: {
    sm: {
      shadowColor: "#000",
      shadowOffset: { width: 0, height: 1 },
      shadowOpacity: 0.1,
      shadowRadius: 2,
    },
    md: {
      shadowColor: "#000",
      shadowOffset: { width: 0, height: 2 },
      shadowOpacity: 0.15,
      shadowRadius: 4,
    },
    lg: {
      shadowColor: "#000",
      shadowOffset: { width: 0, height: 4 },
      shadowOpacity: 0.2,
      shadowRadius: 8,
    },
  },
  fonts: {
    regular: {
      fontFamily: "System",
      fontWeight: "400" as const,
    },
    medium: {
      fontFamily: "System",
      fontWeight: "500" as const,
    },
    bold: {
      fontFamily: "System",
      fontWeight: "700" as const,
    },
    heavy: {
      fontFamily: "System",
      fontWeight: "900" as const,
    },
  },
};

/**
 * Motyw ciemny dla platformy iOS
 */
const iosDarkTheme: AppTheme = {
  dark: true,
  colors: {
    primary: "#0A84FF",
    secondary: "#5E5CE6",
    background: "#000000",
    card: "#1C1C1E",
    text: "#FFFFFF",
    border: "#38383A",
    notification: "#FF453A",
    error: "#FF453A",
    success: "#30D158",
    warning: "#FF9F0A",
    info: "#0A84FF",
    surface: "#1C1C1E",
    onSurface: "#FFFFFF",
  },
  spacing: {
    xs: 4,
    sm: 8,
    md: 16,
    lg: 24,
    xl: 32,
    xxl: 48,
  },
  borderRadius: {
    sm: 4,
    md: 8,
    lg: 12,
    xl: 16,
    full: 9999,
  },
  typography: {
    fontSize: {
      xs: 12,
      sm: 14,
      md: 16,
      lg: 18,
      xl: 20,
      xxl: 24,
      xxxl: 32,
    },
    fontWeight: {
      normal: "400",
      medium: "500",
      semibold: "600",
      bold: "700",
    },
  },
  shadows: {
    sm: {
      shadowColor: "#000",
      shadowOffset: { width: 0, height: 1 },
      shadowOpacity: 0.3,
      shadowRadius: 2,
    },
    md: {
      shadowColor: "#000",
      shadowOffset: { width: 0, height: 2 },
      shadowOpacity: 0.4,
      shadowRadius: 4,
    },
    lg: {
      shadowColor: "#000",
      shadowOffset: { width: 0, height: 4 },
      shadowOpacity: 0.5,
      shadowRadius: 8,
    },
  },
  fonts: {
    regular: {
      fontFamily: "System",
      fontWeight: "400" as const,
    },
    medium: {
      fontFamily: "System",
      fontWeight: "500" as const,
    },
    bold: {
      fontFamily: "System",
      fontWeight: "700" as const,
    },
    heavy: {
      fontFamily: "System",
      fontWeight: "900" as const,
    },
  },
};

/**
 * Pobiera motyw Native na podstawie platformy i trybu (light/dark)
 */
export const getNativeTheme = (isDark: boolean): AppTheme => {
  if (Platform.OS === "ios") {
    return isDark ? iosDarkTheme : iosLightTheme;
  }
  // Android (domyślnie)
  return isDark ? androidDarkTheme : androidLightTheme;
};

/**
 * Hook do pobierania motywu dla platformy Native (Android/iOS)
 * Zgodnie z dokumentacją Expo: https://docs.expo.dev/develop/user-interface/color-themes
 */
export const useTheme = (): AppTheme => {
  const colorScheme = useColorScheme();
  // useColorScheme może zwracać "light", "dark" lub null
  // Domyślnie używamy trybu jasnego, jeśli colorScheme jest null
  const isDark = colorScheme === "dark";
  return getNativeTheme(isDark);
};
