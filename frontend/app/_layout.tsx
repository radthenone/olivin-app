import { ThemeProvider } from "@react-navigation/native";
import { Stack } from "expo-router";
import { StatusBar } from "expo-status-bar";
import "react-native-reanimated";
import { useTheme } from "../config/theme";

export const unstable_settings = {
  anchor: "(tabs)",
};

export default function RootLayout() {
  const theme = useTheme();

  return (
    <ThemeProvider value={theme}>
      <Stack>
        <Stack.Screen name="(tabs)" options={{ headerShown: false }} />
        <Stack.Screen name="(auth)" options={{ headerShown: false }} />
        <Stack.Screen
          name="health"
          options={{
            title: "Health Status",
            headerShown: true,
          }}
        />
        <Stack.Screen
          name="logs"
          options={{
            title: "Application Logs",
            headerShown: true,
          }}
        />
      </Stack>
      <StatusBar style={theme.dark ? "light" : "dark"} />
    </ThemeProvider>
  );
}
