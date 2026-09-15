import "../styles/global.css";
import { StatusBar } from "expo-status-bar";
import { Stack } from "expo-router";
import { Platform } from "react-native";
import { QueryClientProvider } from "@tanstack/react-query";
import {
  SafeAreaProvider,
  initialWindowMetrics,
} from "react-native-safe-area-context";
import { queryClient } from "@core/query/query-client";
import { AuthProvider, useAuthContext } from "@core/auth/auth.provider";
import { SafeView } from "@ui/layout/SafeView";
import { configureMobileApi } from "@core/api/transport";

// Transport musi być podłączony, zanim którykolwiek ekran wykona żądanie —
// stąd wywołanie w module, a nie w efekcie komponentu.
configureMobileApi();

/**
 * Główny layout aplikacji.
 *
 * Dlaczego istnieje:
 * tu spinamy globalne providery oraz ochronę route groups w Expo Router.
 */
export default function RootLayout() {
  return (
    <SafeAreaProvider initialMetrics={initialWindowMetrics}>
      {/* SDK 57 usunął backgroundColor z paska stanu — na Androidzie 16+ tło
          paska wynika z edge-to-edge, nie z propa. */}
      <StatusBar style="dark" />
      <QueryClientProvider client={queryClient}>
        <AuthProvider>
          <RootNavigator />
        </AuthProvider>
      </QueryClientProvider>
    </SafeAreaProvider>
  );
}

function RootNavigator() {
  const auth = useAuthContext();

  if (auth.isChecking) {
    return null;
  }

  const canAccessAuthRoutes =
    auth.isUnauthenticated ||
    auth.isMfaRequired ||
    auth.isEmailVerificationRequired;

  const stack = (
    <Stack
      screenOptions={{
        headerShown: false,
        contentStyle: { backgroundColor: "#ffffff" },
      }}
    >
      <Stack.Screen name="index" />
      <Stack.Screen name="authredirect" />
      <Stack.Screen name="oauthredirect" />
      <Stack.Screen name="authorize" />

      <Stack.Protected guard={auth.isAuthenticated}>
        <Stack.Screen name="(app)" />
      </Stack.Protected>

      <Stack.Protected guard={canAccessAuthRoutes}>
        <Stack.Screen name="(auth)" />
      </Stack.Protected>
    </Stack>
  );

  if (Platform.OS === "web") {
    return stack;
  }

  return (
    <SafeView className="bg-white" style={{ backgroundColor: "#ffffff" }}>
      {stack}
    </SafeView>
  );
}
