//import { ThemeProvider } from "@react-navigation/native";
import "../styles/global.css";
import { Stack } from "expo-router";
import { QueryClientProvider } from "@tanstack/react-query";
import { Platform, View } from "react-native";
import { queryClient } from "@lib/queryClient";
//import { StatusBar } from "expo-status-bar";
//import { useTheme } from "../src/core/theme/theme";
import {
  SafeAreaProvider,
  initialWindowMetrics,
} from "react-native-safe-area-context";
import { platformRender } from "@lib";
import { SafeView } from "@ui";

export default function AppLayout() {
  const stack = (
    <Stack initialRouteName="index">
      <Stack.Screen
        name="index"
        options={{ title: "index", headerShown: false }}
      />
      {/* <Stack.Screen
        name="health"
        options={{ title: "Health", headerShown: false }}
      /> */}
      <Stack.Screen
        name="+not-found"
        options={{ title: "Not Found", headerShown: false }}
      />
      {/* <Stack.Screen name="(shop)" options={{ headerShown: false }} />
      <Stack.Screen name="(auth)" options={{ headerShown: false }} /> */}
    </Stack>
  );

  return (
    <QueryClientProvider client={queryClient}>
      {platformRender({
        web: <>{stack}</>,
        native: (
          <SafeAreaProvider initialMetrics={initialWindowMetrics}>
            <SafeView>{stack}</SafeView>
          </SafeAreaProvider>
        ),
      })}
    </QueryClientProvider>
  );
}
