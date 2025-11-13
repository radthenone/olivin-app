import { Theme } from "@react-navigation/native";
import { useColorScheme } from "react-native";

/**
 * Kolory bazowe dla aplikacji Web
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
 * Rozszerzony motyw aplikacji Web
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
 * Motyw jasny dla platformy Web
 */
export const webLightTheme: AppTheme = {
  dark: false,
  colors: {
    primary: "#007AFF",
    secondary: "#5856D6",
    background: "#FFFFFF",
    card: "#F2F2F7",
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
      boxShadow: "0 1px 2px rgba(0, 0, 0, 0.05)",
    },
    md: {
      boxShadow: "0 4px 6px rgba(0, 0, 0, 0.1)",
    },
    lg: {
      boxShadow: "0 10px 15px rgba(0, 0, 0, 0.1)",
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
 * Motyw ciemny dla platformy Web
 */
export const webDarkTheme: AppTheme = {
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
      boxShadow: "0 1px 2px rgba(0, 0, 0, 0.3)",
    },
    md: {
      boxShadow: "0 4px 6px rgba(0, 0, 0, 0.3)",
    },
    lg: {
      boxShadow: "0 10px 15px rgba(0, 0, 0, 0.3)",
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
 * Pobiera motyw Web na podstawie trybu (light/dark)
 */
export const getWebTheme = (isDark: boolean): AppTheme => {
  return isDark ? webDarkTheme : webLightTheme;
};

/**
 * Hook do pobierania motywu dla platformy Web
 * Zgodnie z dokumentacją Expo: https://docs.expo.dev/develop/user-interface/color-themes
 */
export const useTheme = (): AppTheme => {
  const colorScheme = useColorScheme();
  // useColorScheme może zwracać "light", "dark" lub null
  // Domyślnie używamy trybu jasnego, jeśli colorScheme jest null
  const isDark = colorScheme === "dark";
  return getWebTheme(isDark);
};
